"""Shape checks for the optional evidence fields (TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT)."""

import pytest

from tools import validate_frontmatter as vf

BASE = {"status": "active", "layer": "engine", "authority": "P1", "audience": "agent"}


def errors_for(**fields):
    return vf._validate_doc("docs/engine/x.md", {**BASE, **fields})


def test_a_doc_without_the_fields_is_valid():
    assert errors_for() == []


def test_well_formed_fields_are_accepted():
    assert errors_for(
        evidence_paths=["src/engine/kernel.py", "tests/engine/test_kernel.py"],
        verified_by="TCK-20261101-KERNEL-CHECK", verified_at="abcdef1", reviewed_by="#812",
    ) == []


@pytest.mark.parametrize("bad", ["/abs/path.py", "src/engine/", "src/*.py", "src/{a,b}.py", "src/../x.py", "C:/x.py", "src\\x.py", ""])
def test_malformed_evidence_paths_are_rejected(bad):
    assert any("evidence_paths" in e for e in errors_for(evidence_paths=[bad]))


def test_evidence_paths_must_be_a_list():
    assert any("must be a list" in e for e in errors_for(evidence_paths="src/a.py"))


@pytest.mark.parametrize("field", ["verified_by", "reviewed_by"])
@pytest.mark.parametrize("bad", ["812", "tck-1", "TCK-2026-X", "PR 812", "https://example.com/pull/1"])
def test_malformed_references_are_rejected(field, bad):
    assert any(field in e for e in errors_for(**{field: bad}))


@pytest.mark.parametrize("bad", ["abc", "ABCDEF1", "zzzzzzz", "a" * 41])
def test_malformed_shas_are_rejected(bad):
    assert any("verified_at" in e for e in errors_for(verified_at=bad))


def test_a_path_that_does_not_exist_is_valid():
    """No existence check: a deleted evidence file is drift, and must not make the corpus frontmatter test red."""
    assert errors_for(evidence_paths=["src/this/file/was/deleted.py"]) == []


def test_the_fields_parse_from_real_frontmatter_text():
    text = '---\nstatus: active\nlayer: engine\nauthority: P1\naudience: agent\nevidence_paths: [src/a.py, tests/b.py]\nverified_by: "#812"\nverified_at: abcdef1\n---\nbody\n'
    fm = vf.extract_frontmatter(text)
    assert fm["evidence_paths"] == ["src/a.py", "tests/b.py"] and fm["verified_by"] == "#812"
    assert vf._validate_doc("docs/engine/x.md", fm) == []
