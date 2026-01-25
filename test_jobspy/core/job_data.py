# -*- coding: utf-8 -*-
"""
Unified Job Data Model for JobScrapper.
Provides consistent data structure across LinkedIn and Indeed.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
import re
import pandas as pd


@dataclass
class JobData:
    """Unified job data model."""

    # Core fields
    job_id: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    description: str = ""

    # Salary fields (raw from source)
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    currency: str = "USD"
    interval: str = "yearly"  # yearly, monthly, hourly, weekly

    # Processed salary fields
    salary_range: str = ""
    estimated_annual: Optional[float] = None
    estimated_annual_usd: Optional[float] = None

    # Metadata
    posted_date: Optional[datetime] = None
    job_url: str = ""
    platform: str = ""  # "linkedin" or "indeed"

    # Extracted fields
    requirements: str = ""
    company_size: str = ""
    job_status: str = "Active"

    # AI analysis fields
    ai_analysis: Optional[Dict[str, Any]] = None
    ai_analyzed: bool = False

    # Deduplication key
    _dedup_key: str = field(default="", repr=False)

    def __post_init__(self):
        """Generate dedup key after initialization."""
        self._dedup_key = self.generate_dedup_key()

    def generate_dedup_key(self) -> str:
        """Generate unique key based on title + company + location."""
        title = str(self.title).strip().lower()
        company = str(self.company).strip().lower()
        location = str(self.location).strip().lower()

        # Normalize: remove extra spaces
        title = re.sub(r'\s+', ' ', title) if title and title != 'nan' else ""
        company = re.sub(r'\s+', ' ', company) if company and company != 'nan' else ""
        location = re.sub(r'\s+', ' ', location) if location and location != 'nan' else ""

        return f"{title}|||{company}|||{location}"

    def generate_cross_platform_key(self) -> Optional[str]:
        """Generate key for cross-platform deduplication (title + company only)."""
        title = str(self.title).strip().lower()
        company = str(self.company).strip().lower()

        title = re.sub(r'\s+', ' ', title) if title and title != 'nan' else ""
        company = re.sub(r'\s+', ' ', company) if company and company != 'nan' else ""

        if not title or not company:
            return None

        return f"{title}|||{company}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_export_dict(self) -> Dict[str, Any]:
        """Convert to export format matching expected Excel columns."""
        return {
            "Job Title": self.title,
            "Company Name": self.company,
            "Requirements": self.requirements,
            "Location": self.location,
            "Salary Range": self.salary_range,
            "Estimated Annual Salary": self.estimated_annual,
            "Estimated Annual Salary (USD)": self.estimated_annual_usd,
            "Job Description": self.description,
            "Company Size": self.company_size,
            "Posted Date": self.posted_date.strftime("%Y-%m-%d") if self.posted_date else "",
            "Job Status": self.job_status,
            "Platform": self.platform.title(),
            "Job Link": self.job_url,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobData":
        """Create JobData from a dictionary (e.g., from checkpoint)."""
        # Handle posted_date
        posted_date = data.get('posted_date')
        if posted_date and isinstance(posted_date, str):
            try:
                posted_date = datetime.fromisoformat(posted_date)
            except:
                posted_date = None

        return cls(
            job_id=data.get('job_id', ''),
            title=data.get('title', ''),
            company=data.get('company', ''),
            location=data.get('location', ''),
            description=data.get('description', ''),
            min_amount=data.get('min_amount'),
            max_amount=data.get('max_amount'),
            currency=data.get('currency', 'USD'),
            interval=data.get('interval', 'yearly'),
            salary_range=data.get('salary_range', ''),
            estimated_annual=data.get('estimated_annual'),
            estimated_annual_usd=data.get('estimated_annual_usd'),
            posted_date=posted_date,
            job_url=data.get('job_url', ''),
            platform=data.get('platform', ''),
            requirements=data.get('requirements', ''),
            company_size=data.get('company_size', ''),
            job_status=data.get('job_status', 'Active'),
            ai_analysis=data.get('ai_analysis'),
            ai_analyzed=data.get('ai_analyzed', False),
        )

    @classmethod
    def from_jobspy_dict(cls, job: Dict[str, Any], platform: str = "indeed") -> "JobData":
        """Create JobData from JobSpy raw dictionary."""
        # Parse posted date
        posted_date = None
        date_str = job.get("date_posted", "")
        if date_str and not pd.isna(date_str):
            try:
                posted_date = pd.to_datetime(date_str).to_pydatetime()
            except:
                pass

        return cls(
            job_id=str(job.get("id", "")),
            title=str(job.get("title", "")),
            company=str(job.get("company", "") if not pd.isna(job.get("company")) else ""),
            location=str(job.get("location", "")),
            description=str(job.get("description", "")),
            min_amount=job.get("min_amount") if not pd.isna(job.get("min_amount")) else None,
            max_amount=job.get("max_amount") if not pd.isna(job.get("max_amount")) else None,
            currency=str(job.get("currency", "USD")) if job.get("currency") else "USD",
            interval=str(job.get("interval", "yearly")) if job.get("interval") else "yearly",
            posted_date=posted_date,
            job_url=str(job.get("job_url", "")),
            platform=platform,
        )


class JobDataCollection:
    """Collection of JobData with deduplication support."""

    def __init__(self):
        self.jobs: List[JobData] = []
        self._seen_keys: set = set()
        self._cross_platform_keys: set = set()

    def add(self, job: JobData, deduplicate: bool = True) -> bool:
        """
        Add a job to collection.

        Args:
            job: JobData instance
            deduplicate: If True, skip duplicates based on dedup_key

        Returns:
            True if job was added, False if duplicate
        """
        if deduplicate and job._dedup_key in self._seen_keys:
            return False

        self.jobs.append(job)
        self._seen_keys.add(job._dedup_key)

        # Track cross-platform key
        xp_key = job.generate_cross_platform_key()
        if xp_key:
            self._cross_platform_keys.add(xp_key)

        return True

    def add_many(self, jobs: List[JobData], deduplicate: bool = True) -> int:
        """
        Add multiple jobs to collection.

        Returns:
            Number of jobs actually added
        """
        added = 0
        for job in jobs:
            if self.add(job, deduplicate):
                added += 1
        return added

    def is_cross_platform_duplicate(self, job: JobData) -> bool:
        """Check if job is a cross-platform duplicate."""
        xp_key = job.generate_cross_platform_key()
        return xp_key is not None and xp_key in self._cross_platform_keys

    def to_dataframe(self, export_format: bool = False) -> pd.DataFrame:
        """Convert collection to pandas DataFrame."""
        if export_format:
            records = [job.to_export_dict() for job in self.jobs]
        else:
            records = [job.to_dict() for job in self.jobs]
        return pd.DataFrame(records)

    def __len__(self) -> int:
        return len(self.jobs)

    def __iter__(self):
        return iter(self.jobs)

    def __getitem__(self, index):
        return self.jobs[index]
