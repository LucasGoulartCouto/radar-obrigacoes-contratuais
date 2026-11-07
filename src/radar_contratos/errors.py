"""Erros que podem ser apresentados ao operador sem expor detalhes do banco."""


class RadarError(Exception):
    """Erro esperado na operação do Radar."""


class ValidationError(RadarError):
    """Entrada inválida para a operação."""


class StaleRecordError(RadarError):
    """O registro mudou depois de ser exibido ao operador."""


class IdempotencyConflictError(RadarError):
    """A mesma identificação de operação foi usada para conteúdos diferentes."""


class StorageBusyError(RadarError):
    """O banco não conseguiu concluir a operação no tempo permitido."""


class StorageUnavailableError(RadarError):
    """O armazenamento não pôde ser acessado; não representa resultado vazio."""


class DatabaseNotReadyError(RadarError):
    """O banco não está na versão de esquema exigida pela aplicação."""
