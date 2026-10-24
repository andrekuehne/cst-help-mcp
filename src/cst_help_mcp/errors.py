"""Errors that the CLI reports as a clear message rather than a traceback."""


class CstHelpError(Exception):
    """A problem the user can fix, reported as a one-line message."""


class ConfigError(CstHelpError):
    """The configuration is missing, malformed or names paths that don't exist."""


class BuildError(CstHelpError):
    """The build cannot produce a trustworthy Collection."""


class KnowledgeBaseError(CstHelpError):
    """The Knowledge Base is missing or doesn't hold the requested Release or Area."""


class BenchmarkError(CstHelpError):
    """The benchmark file is malformed, or a query log can't be read."""
