"""Traduz falhas de acesso sem colocar SQL, parâmetros ou caminhos na mensagem."""

import logging
import sqlite3

from radar_contratos.errors import RadarError, StorageBusyError, StorageUnavailableError

logger = logging.getLogger(__name__)


def read_error(error: Exception, *, operation: str, message: str) -> RadarError:
    original = getattr(error, "orig", error)
    code = getattr(original, "sqlite_errorcode", 0)
    code = (code & 0xFF) if isinstance(code, int) else 0
    logger.warning("operation=%s outcome=failed sqlite_code=%d", operation, code)
    if code in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
        return StorageBusyError(
            "O banco local está ocupado. Aguarde e atualize para tentar novamente."
        )
    return StorageUnavailableError(message)
