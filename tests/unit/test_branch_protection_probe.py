"""Prova temporária de bloqueio da principal; removida após a verificação."""

import pytest


def test_branch_protection_probe():
    pytest.fail("Falha intencional para verificar a proteção da principal.")
