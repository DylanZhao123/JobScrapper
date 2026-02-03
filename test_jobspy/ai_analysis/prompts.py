# -*- coding: utf-8 -*-
"""
Prompt Manager for AI analysis.
Supports hot-reload of prompt templates from files.
"""

import os
import time
from typing import Dict, Optional, List
from pathlib import Path


class PromptManager:
    """Manage prompt templates with hot-reload support."""

    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize prompt manager.

        Args:
            templates_dir: Directory containing prompt template files
        """
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            # Default: prompt_templates/ in same directory as this file
            self.templates_dir = Path(__file__).parent / "prompt_templates"

        # Cache for loaded templates
        self._cache: Dict[str, Dict] = {}

    def get_template(self, name: str = "default", force_reload: bool = False) -> Optional[str]:
        """
        Get a prompt template by name.

        Args:
            name: Template name (without .txt extension)
            force_reload: If True, reload from file even if cached

        Returns:
            Template string or None if not found
        """
        # Check cache
        if not force_reload and name in self._cache:
            cached = self._cache[name]
            # Check if file was modified
            file_path = self.templates_dir / f"{name}.txt"
            if file_path.exists():
                mtime = os.path.getmtime(file_path)
                if mtime <= cached.get('mtime', 0):
                    return cached.get('content')

        # Load from file
        return self._load_template(name)

    def _load_template(self, name: str) -> Optional[str]:
        """Load template from file."""
        file_path = self.templates_dir / f"{name}.txt"

        if not file_path.exists():
            print(f"[PromptManager] Template not found: {file_path}")
            return None

        try:
            content = file_path.read_text(encoding='utf-8')
            mtime = os.path.getmtime(file_path)

            # Update cache
            self._cache[name] = {
                'content': content,
                'mtime': mtime,
            }

            return content

        except Exception as e:
            print(f"[PromptManager] Error loading template: {e}")
            return None

    def list_templates(self) -> List[str]:
        """List available template names."""
        if not self.templates_dir.exists():
            return []

        templates = []
        for file in self.templates_dir.glob("*.txt"):
            templates.append(file.stem)

        return sorted(templates)

    def reload_all(self):
        """Force reload all templates."""
        self._cache.clear()
        for name in self.list_templates():
            self._load_template(name)

    def save_template(self, name: str, content: str) -> bool:
        """
        Save a template to file.

        Args:
            name: Template name
            content: Template content

        Returns:
            True if successful
        """
        try:
            self.templates_dir.mkdir(parents=True, exist_ok=True)
            file_path = self.templates_dir / f"{name}.txt"
            file_path.write_text(content, encoding='utf-8')

            # Update cache
            self._cache[name] = {
                'content': content,
                'mtime': time.time(),
            }

            return True

        except Exception as e:
            print(f"[PromptManager] Error saving template: {e}")
            return False

    def get_default_template(self) -> str:
        """Get the default analysis template."""
        template = self.get_template("default")
        if template:
            return template

        # Return built-in default if file not found
        return self._builtin_default_template()

    def _builtin_default_template(self) -> str:
        """Built-in default template."""
        return '''Analyze this job posting and provide structured insights.

**Job Title:** {title}
**Company:** {company}
**Location:** {location}
**Salary:** {salary_range}

**Description:**
{description}

Please analyze and respond in JSON format with the following structure:
{{
    "job_category": "string - categorize the job (e.g., ML Engineer, Data Scientist, AI Researcher, etc.)",
    "seniority_level": "string - Junior/Mid/Senior/Lead/Principal/Director",
    "required_skills": ["list", "of", "key", "technical", "skills"],
    "nice_to_have_skills": ["list", "of", "optional", "skills"],
    "years_experience_required": "string - e.g., '3-5 years' or 'Not specified'",
    "education_required": "string - e.g., 'Bachelor's in CS' or 'PhD preferred'",
    "remote_policy": "string - Remote/Hybrid/On-site/Not specified",
    "key_responsibilities": ["list", "of", "main", "responsibilities"],
    "company_stage": "string - Startup/Scaleup/Enterprise/Not specified",
    "ai_ml_focus_areas": ["list", "of", "AI/ML", "domains", "mentioned"],
    "job_attractiveness_score": "number 1-10 - overall attractiveness for AI professionals",
    "analysis_notes": "string - any additional insights or red flags"
}}

Respond ONLY with valid JSON, no additional text.'''

    def create_default_template_file(self) -> bool:
        """Create the default template file if it doesn't exist."""
        default_path = self.templates_dir / "default.txt"

        if default_path.exists():
            return True

        return self.save_template("default", self._builtin_default_template())
