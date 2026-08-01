import os
import re

# Only allow QMOF-style identifiers, e.g. "qmof-8a95c27".
# Prevents path traversal via crafted qmof_id values.
QMOF_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def validate_file_extension(filename: str, allowed_extensions: list[str]) -> bool:
    """Return True if filename ends with one of allowed_extensions (case-insensitive)."""
    return any(filename.lower().endswith(ext.lower()) for ext in allowed_extensions)


def is_valid_qmof_id(qmof_id: str) -> bool:
    """
    Validate a qmof_id supplied via a URL path parameter.

    Rejects empty strings, path separators, '..', and any characters outside
    a conservative alphanumeric/dash/underscore set.
    """
    if not qmof_id:
        return False

    if ".." in qmof_id or "/" in qmof_id or "\\" in qmof_id:
        return False

    return bool(QMOF_ID_PATTERN.match(qmof_id))


def safe_join(base_dir: str, filename: str) -> str:
    """
    Join base_dir and filename, then verify the resolved path is still
    inside base_dir. Raises ValueError if the resulting path would escape
    base_dir (e.g. via '..' segments or absolute path injection).
    """
    base_dir = os.path.abspath(base_dir)
    candidate = os.path.abspath(os.path.join(base_dir, filename))

    if not (candidate == base_dir or candidate.startswith(base_dir + os.sep)):
        raise ValueError("Resolved path escapes the base directory")

    return candidate
