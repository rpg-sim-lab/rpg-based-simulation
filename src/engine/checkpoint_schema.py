# Compliance IDs: INFRA-215
"""The schema fingerprint of a scenario checkpoint (TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION).

``save`` records, in the JSON header, ``{"<module>.<qualname>": [ordered field names]}`` for every dataclass the payload contains, taken from the pickler itself so it covers the
records actually written. ``restore`` compares it with the current classes BEFORE ``pickle.loads``: a slotted dataclass unpickles positionally, so an insert, reorder, rename or
removal would silently shift values. Only an append named in ``FIELD_RULES`` (``record`` + ``field``) is accepted; ``fill_missing_fields`` then fills it.
Not detected: enum member renames, changed field types or defaults, a field that keeps its name but changes meaning.
"""
from __future__ import annotations

import dataclasses
import importlib
import io
import json
import pickle
import struct
from typing import Any, BinaryIO, Dict, List, Optional, Tuple

from src.engine.checkpoint_fields import FIELD_RULES, FieldRule


class CheckpointSchemaError(ValueError):
    """A checkpoint is refused before unpickling. A ValueError, so the restore route answers 400; ``to_detail`` is that response's shaped detail."""
    reason = "mismatch"

    def __init__(self, message: str, classes: Optional[List[Dict[str, Any]]] = None) -> None:
        super().__init__(message)
        self.classes = list(classes or [])

    def to_detail(self) -> Dict[str, Any]:
        """The shaped 400 body of the restore route."""
        return {"error": "checkpoint_schema", "reason": self.reason, "message": str(self), "classes": self.classes}


class CheckpointHeaderError(CheckpointSchemaError):
    """The header cannot be read: too short, a length past the end of the file, bad UTF-8 or JSON, or not an object with ``tick`` and ``spec_id``."""
    reason = "header"


class CheckpointSchemaMissingError(CheckpointSchemaError):
    """No fingerprint in the header (a checkpoint from before it existed): refused, since only the payload could be judged and that needs ``pickle.loads``."""
    reason = "missing"


class CheckpointSchemaMismatchError(CheckpointSchemaError):
    """A record's saved fields are not the current fields, or are an append that no FIELD_RULES row fills."""
    reason = "mismatch"


class _SchemaPickler(pickle.Pickler):
    def __init__(self, file: BinaryIO, **kw: Any) -> None:
        super().__init__(file, **kw)
        self.schema: Dict[str, List[str]] = {}

    def reducer_override(self, obj: Any) -> Any:
        cls = type(obj)
        if dataclasses.is_dataclass(cls) and not isinstance(obj, type):
            self.schema.setdefault(class_key(cls), [f.name for f in dataclasses.fields(cls)])
        return NotImplemented


def class_key(cls: type) -> str:
    """The fingerprint key of a dataclass."""
    return f"{cls.__module__}.{cls.__qualname__}"


def dump_with_schema(state: Any) -> Tuple[bytes, Dict[str, List[str]]]:
    """The payload (byte-identical to ``pickle.dumps(state, protocol=HIGHEST_PROTOCOL)``) and the fingerprint of the dataclasses written into it."""
    buf = io.BytesIO()
    pickler = _SchemaPickler(buf, protocol=pickle.HIGHEST_PROTOCOL)
    pickler.dump(state)
    return buf.getvalue(), pickler.schema


def read_header(f: BinaryIO) -> Dict[str, Any]:
    """The checkpoint header, validated; raises CheckpointHeaderError when it cannot be read."""
    raw = f.read(4)
    if len(raw) < 4:
        raise CheckpointHeaderError("checkpoint header unreadable: the file is shorter than its 4-byte length prefix")
    (length,) = struct.unpack("<I", raw)
    body = f.read(length)
    if len(body) < length:
        raise CheckpointHeaderError(f"checkpoint header unreadable: it declares {length} bytes but the file holds {len(body)}")
    try:
        header = json.loads(body.decode("utf-8"))
    except ValueError as e:  # UnicodeDecodeError and JSONDecodeError are both ValueErrors
        raise CheckpointHeaderError(f"checkpoint header unreadable: not UTF-8 JSON ({e})") from e
    if not isinstance(header, dict) or "tick" not in header or "spec_id" not in header:
        raise CheckpointHeaderError("checkpoint header unreadable: not a JSON object with 'tick' and 'spec_id'")
    schema = header.get("schema")
    if schema is not None and not (isinstance(schema, dict) and all(isinstance(k, str) and isinstance(v, list) and all(isinstance(n, str) for n in v) for k, v in schema.items())):
        raise CheckpointHeaderError("checkpoint header unreadable: 'schema' is not a mapping of class name to field-name list")
    return header


def _resolve(key: str) -> Optional[type]:
    """The current class named ``key``. Only modules under ``src`` are imported: a header is untrusted until the check passes."""
    parts = key.split(".")
    for i in range(len(parts) - 1, 0, -1):
        module = ".".join(parts[:i])
        if module != "src" and not module.startswith("src."):
            continue
        try:
            obj: Any = importlib.import_module(module)
        except ImportError:
            continue
        for name in parts[i:]:
            obj = getattr(obj, name, None)
        return obj if isinstance(obj, type) and dataclasses.is_dataclass(obj) else None
    return None


def _change(cls: type, old: List[str], rows: List[FieldRule]) -> Optional[str]:
    """How the saved field list ``old`` differs from the current ``cls``, or None when it is accepted (equal, or an append that every row fills)."""
    now = [f.name for f in dataclasses.fields(cls)]
    if now == old:
        return None
    if now[: len(old)] == old:
        unfilled = [n for n in now[len(old):] if not any(r.record == cls.__qualname__ and r.field == n for r in rows)]
        return f"appended without a fill rule: {', '.join(unfilled)}" if unfilled else None
    if sorted(now) == sorted(old):
        return "fields reordered"
    gone = [n for n in old if n not in now]
    if not gone:
        return f"fields inserted: {', '.join(n for n in now if n not in old)}"
    return f"fields removed or renamed: {', '.join(gone)}"


def check_schema(saved: Optional[Dict[str, List[str]]], rules: Optional[List[FieldRule]] = None) -> None:
    """Refuse (typed, before any unpickle) unless every saved record is the current record or the current record with a rule-filled tail appended."""
    if saved is None:
        raise CheckpointSchemaMissingError(
            "checkpoint has no schema fingerprint in its header (written before it existed): restore refused; re-create the checkpoint with a current build"
        )
    rows = FIELD_RULES if rules is None else rules
    problems: List[Dict[str, Any]] = []
    for key, old in saved.items():
        cls = _resolve(key)
        change = "class removed or renamed" if cls is None else _change(cls, old, rows)
        if change is not None:
            current = None if cls is None else [f.name for f in dataclasses.fields(cls)]
            problems.append({"class": key, "change": change, "saved": old, "current": current})
    if problems:
        names = "; ".join(f"{p['class']} ({p['change']})" for p in problems[:5]) + (f" (+{len(problems) - 5} more)" if len(problems) > 5 else "")
        raise CheckpointSchemaMismatchError(f"checkpoint was written by a different build and is refused before unpickling: {names}. Re-create the checkpoint with a current build.", problems)
