import pytest

from radar_contratos.config import Settings
from radar_contratos.domain.documents import (
    DocumentInput,
    DocumentLimits,
    DocumentRole,
    prepare_documents,
    revision_fingerprint,
)
from radar_contratos.errors import ValidationError


def document(content=b"texto", filename="base.txt", role=DocumentRole.BASE):
    return DocumentInput(filename, content, role)


def test_normalization_preserves_original_bytes_empty_lines_and_other_whitespace():
    raw = b"\xef\xbb\xbfprimeira\r\n\r\nsegunda\rterceira\t \n"
    (result,) = prepare_documents((document(raw),), DocumentLimits())
    assert result.original_bytes == raw
    assert result.reference_text == "primeira\n\nsegunda\nterceira\t \n"
    assert result.raw_sha256 != result.reference_sha256
    assert result.normalization_version == "TEXT_REFERENCE_V1"


@pytest.mark.parametrize(
    "item",
    [
        document(b""),
        document(b" \r\n\t"),
        document(b"\xef\xbb\xbf"),
        document(b"\xff"),
        document(b"texto\x00oculto"),
        document(b"%PDF-1.7\ntexto"),
        document(filename="../base.txt"),
        document(filename="C:\\base.txt"),
        document(filename="arquivo.pdf"),
        document(filename="base.txt\n"),
        document(role="papel inventado"),
        document(content="texto"),
    ],
)
def test_invalid_document_is_rejected_without_silent_conversion(item):
    with pytest.raises(ValidationError):
        prepare_documents((item,), DocumentLimits())


def test_limits_count_raw_utf8_bytes_at_the_inclusive_boundary():
    raw = ("é" * 131_072).encode("utf-8")
    assert len(raw) == 262_144
    assert prepare_documents((document(raw),), DocumentLimits())[0].original_bytes == raw
    with pytest.raises(ValidationError, match="262144"):
        prepare_documents((document(raw + "é".encode()),), DocumentLimits())


def test_count_and_aggregate_limits_apply_to_the_complete_set():
    limits = DocumentLimits(max_document_bytes=8, max_revision_bytes=10, max_documents=2)
    assert len(prepare_documents((document(b"aaaaa"), document(b"bbbbb")), limits)) == 2
    with pytest.raises(ValidationError, match="conjunto excede"):
        prepare_documents((document(b"aaaaaa"), document(b"bbbbb")), limits)
    with pytest.raises(ValidationError, match="até 2"):
        prepare_documents((document(b"a"), document(b"b"), document(b"c")), limits)


def test_logical_identity_ignores_filename_order_bom_and_line_endings_only():
    limits = DocumentLimits()
    original = prepare_documents((document(b"A\nB"), document(b"C")), limits)
    equivalent = prepare_documents(
        (
            document(b"C", filename="outro.txt"),
            document(b"\xef\xbb\xbfA\r\nB"),
        ),
        limits,
    )
    assert revision_fingerprint(original) == revision_fingerprint(equivalent)
    for changed in (document(b"A\nB "), document(b"A\nB", role=DocumentRole.AMENDMENT)):
        revised = prepare_documents((changed, document(b"C")), limits)
        assert revision_fingerprint(original) != revision_fingerprint(revised)


def test_duplicate_members_are_rejected_even_with_different_names_and_line_endings():
    with pytest.raises(ValidationError, match="repete"):
        prepare_documents((document(b"A\nB"), document(b"A\r\nB", "outro.txt")), DocumentLimits())


@pytest.mark.parametrize("value", ["0", "-1", "dez"])
def test_invalid_environment_limits_are_actionable(monkeypatch, value):
    monkeypatch.setenv("RADAR_MAX_DOCUMENT_BYTES", value)
    with pytest.raises(ValidationError):
        Settings.from_environment()


def test_cli_reports_invalid_limits_without_a_traceback(monkeypatch, capsys):
    from radar_contratos.cli import main

    monkeypatch.setenv("RADAR_MAX_DOCUMENTS", "zero")
    monkeypatch.setattr("sys.argv", ["radar", "init-db"])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 1
    assert "limites documentais" in capsys.readouterr().err
