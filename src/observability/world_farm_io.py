"""File helpers that let several world processes share one host (world farm, step one).

Two rules, both outside the tick, neither touching simulation state:

* a run directory that already exists belongs to someone else: refuse it, never delete it (``ensure_run_dir_free``);
* a line appended to a file that more than one process writes reaches the file in ONE ``write`` on an ``O_APPEND`` descriptor, so
  two writers cannot interleave inside a line (``append_line``).
"""

from __future__ import annotations

import os


class RunDirectoryInUseError(FileExistsError):
    """A run directory already exists and is not ours to reuse or delete."""


def ensure_run_dir_free(path: str, *, label: str) -> None:
    """Raise ``RunDirectoryInUseError`` when ``path`` exists. Deletes nothing."""
    if os.path.exists(path):
        raise RunDirectoryInUseError(
            f"{label} already exists at {path}; refusing to reuse or delete it. Pick another id."
        )


def append_line(path: str, line: str) -> None:
    """Append ``line`` (a newline is added when missing) to ``path`` with a single ``os.write`` on an ``O_APPEND`` fd.

    POSIX makes one ``write`` on an ``O_APPEND`` descriptor land at the end of the file atomically with respect to other writers,
    for any length a regular file accepts, so concurrent processes never split each other's lines. A short write (disk full) is
    raised, not retried: a retry would no longer be one write.
    """
    data = (line if line.endswith("\n") else line + "\n").encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        written = os.write(fd, data)
    finally:
        os.close(fd)
    if written != len(data):
        raise OSError(f"short append to {path}: wrote {written} of {len(data)} bytes")
