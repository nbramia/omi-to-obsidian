"""Frontmatter writer with stable key ordering."""
import yaml
from typing import Any, Dict


def write_frontmatter(data: Dict[str, Any]) -> str:
    """
    Write YAML frontmatter with stable key ordering.

    PRD: Use a YAML frontmatter writer that preserves stable ordering of keys.
    """
    yaml_str = yaml.dump(
        data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=True,
    )
    return f"---\n{yaml_str}---\n"
