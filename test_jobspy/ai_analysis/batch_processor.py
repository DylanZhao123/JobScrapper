# -*- coding: utf-8 -*-
"""
Batch Processor for AI job analysis.
Supports checkpointing, progress tracking, and cost control.
"""

import os
import json
import time
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, asdict

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.job_data import JobData, JobDataCollection
from ai_analysis.gemini_client import GeminiClient
from ai_analysis.prompts import PromptManager


@dataclass
class BatchCheckpoint:
    """Checkpoint state for batch processing."""
    processed_count: int = 0
    total_count: int = 0
    last_job_id: str = ""
    processed_ids: List[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if self.processed_ids is None:
            self.processed_ids = []


class BatchProcessor:
    """
    Batch processor for AI analysis with checkpoint support.

    Features:
    - Checkpoint/resume capability
    - Progress tracking
    - Cost estimation
    - Rate limiting
    """

    def __init__(
        self,
        gemini_client: GeminiClient,
        prompt_manager: PromptManager = None,
        checkpoint_dir: Optional[str] = None,
        checkpoint_interval: int = 10,
    ):
        """
        Initialize batch processor.

        Args:
            gemini_client: Initialized GeminiClient
            prompt_manager: PromptManager instance (optional)
            checkpoint_dir: Directory for checkpoint files
            checkpoint_interval: Save checkpoint every N jobs
        """
        self.client = gemini_client
        self.prompt_manager = prompt_manager or PromptManager()
        self.checkpoint_interval = checkpoint_interval

        # Checkpoint directory
        if checkpoint_dir:
            self.checkpoint_dir = Path(checkpoint_dir)
        else:
            self.checkpoint_dir = Path(__file__).parent.parent / "output" / "checkpoints"

        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Current batch state
        self._current_batch_id: Optional[str] = None
        self._checkpoint: Optional[BatchCheckpoint] = None

    def process_collection(
        self,
        collection: JobDataCollection,
        template_name: str = "default",
        batch_id: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, JobData], None]] = None,
        resume: bool = True,
    ) -> JobDataCollection:
        """
        Process all jobs in a collection with AI analysis.

        Args:
            collection: JobDataCollection to process
            template_name: Name of prompt template to use
            batch_id: Unique identifier for this batch (for checkpointing)
            progress_callback: Optional callback(processed, total, job)
            resume: If True, resume from checkpoint if available

        Returns:
            Updated JobDataCollection with AI analysis results
        """
        # Generate batch ID if not provided
        if batch_id is None:
            batch_id = f"batch_{int(time.time())}"

        self._current_batch_id = batch_id

        # Load prompt template
        prompt = self.prompt_manager.get_template(template_name)
        if not prompt:
            print(f"[BatchProcessor] Template '{template_name}' not found, using default")
            prompt = self.prompt_manager.get_default_template()

        # Load checkpoint if resuming
        processed_ids = set()
        if resume:
            checkpoint = self._load_checkpoint(batch_id)
            if checkpoint:
                processed_ids = set(checkpoint.processed_ids)
                print(f"[BatchProcessor] Resuming from checkpoint: {checkpoint.processed_count}/{checkpoint.total_count} processed")

        total = len(collection)
        processed = len(processed_ids)

        print(f"\n{'=' * 50}")
        print(f"AI Analysis Batch Processing")
        print(f"{'=' * 50}")
        print(f"  Batch ID: {batch_id}")
        print(f"  Template: {template_name}")
        print(f"  Total jobs: {total}")
        print(f"  Already processed: {processed}")
        print(f"  Remaining: {total - processed}")
        print(f"{'=' * 50}\n")

        # Process each job
        for i, job in enumerate(collection):
            # Skip already processed
            if job.job_id in processed_ids or job._dedup_key in processed_ids:
                continue

            # Prepare job data for prompt
            job_data = {
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "salary_range": job.salary_range or "Not specified",
                "description": job.description[:4000] if job.description else "No description",
            }

            # Analyze with AI
            result = self.client.analyze(prompt, job_data)

            if result:
                job.ai_analysis = result
                job.ai_analyzed = True

            # Track progress
            processed += 1
            processed_ids.add(job.job_id or job._dedup_key)

            # Progress callback
            if progress_callback:
                progress_callback(processed, total, job)
            else:
                # Default progress output
                status = "OK" if result else "FAILED"
                print(f"[{processed}/{total}] {job.title[:40]}... [{status}]")

            # Save checkpoint
            if processed % self.checkpoint_interval == 0:
                self._save_checkpoint(batch_id, processed, total, list(processed_ids))

        # Final checkpoint
        self._save_checkpoint(batch_id, processed, total, list(processed_ids))

        # Print summary
        self._print_summary(processed, total)

        return collection

    def process_jobs(
        self,
        jobs: List[JobData],
        template_name: str = "default",
        batch_id: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
        resume: bool = True,
    ) -> List[JobData]:
        """
        Process a list of JobData objects.

        Args:
            jobs: List of JobData to process
            template_name: Prompt template name
            batch_id: Batch identifier
            progress_callback: Progress callback
            resume: Resume from checkpoint

        Returns:
            List of processed JobData with AI analysis
        """
        collection = JobDataCollection()
        for job in jobs:
            collection.add(job, deduplicate=False)

        self.process_collection(
            collection,
            template_name=template_name,
            batch_id=batch_id,
            progress_callback=progress_callback,
            resume=resume,
        )

        return list(collection)

    def _load_checkpoint(self, batch_id: str) -> Optional[BatchCheckpoint]:
        """Load checkpoint from file."""
        checkpoint_file = self.checkpoint_dir / f"{batch_id}_checkpoint.json"

        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return BatchCheckpoint(**data)
        except Exception as e:
            print(f"[BatchProcessor] Error loading checkpoint: {e}")
            return None

    def _save_checkpoint(
        self,
        batch_id: str,
        processed: int,
        total: int,
        processed_ids: List[str],
    ):
        """Save checkpoint to file."""
        checkpoint = BatchCheckpoint(
            processed_count=processed,
            total_count=total,
            last_job_id=processed_ids[-1] if processed_ids else "",
            processed_ids=processed_ids,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

        checkpoint_file = self.checkpoint_dir / f"{batch_id}_checkpoint.json"

        try:
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(checkpoint), f, indent=2)
        except Exception as e:
            print(f"[BatchProcessor] Error saving checkpoint: {e}")

    def _print_summary(self, processed: int, total: int):
        """Print processing summary."""
        stats = self.client.stats

        print(f"\n{'=' * 50}")
        print("Batch Processing Complete")
        print(f"{'=' * 50}")
        print(f"  Processed: {processed}/{total}")
        print(f"  API requests: {stats['request_count']}")
        print(f"  Input tokens: {stats['input_tokens']:,}")
        print(f"  Output tokens: {stats['output_tokens']:,}")
        print(f"  Estimated cost: ${stats['estimated_cost_usd']:.4f}")
        print(f"{'=' * 50}")

    def clear_checkpoint(self, batch_id: str) -> bool:
        """Clear checkpoint for a batch."""
        checkpoint_file = self.checkpoint_dir / f"{batch_id}_checkpoint.json"

        if checkpoint_file.exists():
            try:
                checkpoint_file.unlink()
                return True
            except Exception as e:
                print(f"[BatchProcessor] Error clearing checkpoint: {e}")
                return False

        return True

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """List all available checkpoints."""
        checkpoints = []

        for file in self.checkpoint_dir.glob("*_checkpoint.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['batch_id'] = file.stem.replace('_checkpoint', '')
                    checkpoints.append(data)
            except:
                pass

        return checkpoints
