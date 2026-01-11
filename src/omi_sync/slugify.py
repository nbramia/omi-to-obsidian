"""Stable slugify helper."""
import re
import unicodedata


def slugify(text: str, max_length: int = 50) -> str:
    """
    Convert text to URL-safe slug.

    PRD: Use a small slugify helper (stable).
    """
    if not text:
        return "untitled"

    # Normalize unicode
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    # Convert to lowercase
    text = text.lower()

    # Replace non-alphanumeric with hyphens
    text = re.sub(r"[^a-z0-9]+", "-", text)

    # Remove leading/trailing hyphens
    text = text.strip("-")

    # Collapse multiple hyphens
    text = re.sub(r"-+", "-", text)

    # Truncate
    if len(text) > max_length:
        text = text[:max_length].rstrip("-")

    return text or "untitled"
