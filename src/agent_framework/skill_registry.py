"""
Skill Registry - Skill discovery and management

Inspired by claw-code's skill system:
- Discover skills from filesystem
- Version control
- Composition of multiple skills
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Skill:
    """
    Skill definition.

    Attributes:
        name: Skill identifier
        description: Human-readable description
        version: Semantic version
        tools: Required tools
        steps: Execution steps
        handler: Optional custom handler
        metadata: Additional metadata
    """
    name: str
    description: str
    version: str = "1.0.0"
    tools: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    handler: Callable = None
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "Skill":
        """Create skill from dictionary"""
        return cls(
            name=d.get("name", ""),
            description=d.get("description", ""),
            version=d.get("version", "1.0.0"),
            tools=d.get("tools", []),
            steps=d.get("steps", []),
            metadata=d.get("metadata", {})
        )

    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "tools": self.tools,
            "steps": self.steps,
            "metadata": self.metadata
        }


class SkillRegistry:
    """
    Skill discovery and management.

    Discovers skills from:
    - Built-in skills
    - skills/ directory
    - External skill paths
    """

    def __init__(self, skills_dir: str = None):
        self.skills_dir = Path(skills_dir or "./skills")
        self.skills: Dict[str, Skill] = {}
        self._logger = logging.getLogger(__name__)

    def discover_skills(self) -> int:
        """
        Discover skills from skills directory.

        Returns:
            Number of skills discovered
        """
        if not self.skills_dir.exists():
            self._logger.info(f"Skills directory not found: {self.skills_dir}")
            return 0

        count = 0
        for skill_path in self.skills_dir.rglob("SKILL.md"):
            try:
                skill = self._load_skill(skill_path)
                if skill:
                    self.skills[skill.name] = skill
                    count += 1
            except Exception as e:
                self._logger.warning(f"Failed to load skill from {skill_path}: {e}")

        self._logger.info(f"Discovered {count} skills")
        return count

    def _load_skill(self, skill_path: Path) -> Optional[Skill]:
        """Load skill from SKILL.md file"""
        # Try to load companion JSON if exists
        json_path = skill_path.with_name("skill.json")
        if json_path.exists():
            with open(json_path) as f:
                data = json.load(f)
                return Skill.from_dict(data)

        # Parse SKILL.md frontmatter
        with open(skill_path) as f:
            content = f.read()

        # Simple frontmatter parsing
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                body = parts[2]

                data = {}
                for line in frontmatter.strip().split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        data[key.strip()] = value.strip()

                data["description"] = body.strip().split("\n")[0] if body.strip() else ""
                return Skill.from_dict(data)

        return None

    def get(self, name: str) -> Optional[Skill]:
        """Get skill by name"""
        return self.skills.get(name)

    def list_skills(self) -> List[Skill]:
        """List all skills"""
        return list(self.skills.values())

    def register(self, skill: Skill) -> None:
        """Register a skill"""
        self.skills[skill.name] = skill
        self._logger.debug(f"Registered skill: {skill.name}")

    def unregister(self, name: str) -> bool:
        """Unregister a skill"""
        if name in self.skills:
            del self.skills[name]
            return True
        return False
