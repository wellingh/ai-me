"""Routine bounded context — domain errors."""


class AiMeError(Exception):
    """Base exception for ai-me domain errors."""


class NothingStagedError(AiMeError):
    """Raised when there are no staged changes for commit."""


class NoChangesError(AiMeError):
    """Raised when there are no changes between base and head."""
