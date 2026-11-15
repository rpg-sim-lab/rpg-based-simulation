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


def claim_run_dir(path: str, *, label: str) -> None:
    """Create ``path`` exclusively: the creation itself is the claim, so two processes cannot both succeed.

    ``ensure_run_dir_free`` is the early, friendly check; this is the one that decides. Raises ``RunDirectoryInUseError`` when the
    directory already exists, and deletes nothing.
    """
    try:
        os.makedirs(path)
    except FileExistsError as exc:
        raise RunDirectoryInUseError(
            f"{label} already exists at {path}; refusing to reuse or delete it. Pick another id."
        ) from exc


def append_line(path: str, line: str) -> None:
    """Append ``line`` (a newline is added when missing) to ``path`` with a single ``os.write`` on an ``O_APPEND`` fd.

    POSIX guarantees that the position of an ``O_APPEND`` write is the end of the file; it does not promise that a write of any
    length stays in one piece against other writers. On a local Linux filesystem the kernel serializes such writes, so concurrent
    processes do not split each other's lines in practice; this is NOT guaranteed on network filesystems (NFS and similar). A short
    write (disk full) is raised, not retried: a retry would no longer be one write.
    """
    data = (line if line.endswith("\n") else line + "\n").encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        written = os.write(fd, data)
    finally:
        os.close(fd)
    if written != len(data):
        raise OSError(f"short append to {path}: wrote {written} of {len(data)} bytes")
