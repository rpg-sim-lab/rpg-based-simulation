"""Writers for hand-made scenario checkpoints that carry a schema fingerprint (TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION).

``old_shape_schema`` is the schema a build WITHOUT the named trailing fields would have recorded: the current fingerprint of ``state`` minus those fields."""
import json
import struct

from src.engine.checkpoint_schema import class_key, dump_with_schema


def current_schema(state):
    return dump_with_schema(state)[1]


def old_shape_schema(state, drop):
    """``drop`` maps a class to the field names it lacked; those names are removed from that class's fingerprint."""
    schema = {k: list(v) for k, v in current_schema(state).items()}
    for cls, names in drop.items():
        schema[class_key(cls)] = [n for n in schema[class_key(cls)] if n not in names]
    return schema


def write_checkpoint(path, blob, spec_id, schema, tick=7):
    header = json.dumps({"tick": tick, "spec_id": spec_id, "rng_checkpoint": None, "schema": schema}).encode()
    path.write_bytes(struct.pack("<I", len(header)) + header + blob)
    return path
