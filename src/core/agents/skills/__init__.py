"""
Package initialization for skills.
Imports all skill modules so they automatically register with @register_skill.
"""

from src.core.agents.skills import (
    auto_analyze_skills,
    clean_skills,
    io_skills,
    ml_skills,
    stats_skills,
    transform_skills,
    visualization_skills,
)

__all__ = [
    "auto_analyze_skills",
    "clean_skills",
    "io_skills",
    "ml_skills",
    "stats_skills",
    "transform_skills",
    "visualization_skills",
]
