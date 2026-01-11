"""File writing with atomic operations."""
import tempfile
import os
from pathlib import Path


def write_file_atomic(path: Path, content: str):
    """
    Write file atomically using temp file + rename.

    PRD: For deterministic file writes: write to temp then atomic rename.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=".tmp_",
        suffix=".md",
    )

    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.replace(temp_path, path)
    except:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise
