"""Fixture containing unclosed resource management issue."""


def read_config_unclosed(filepath: str) -> str:
    """Opens a file handle without using a 'with' context manager."""
    f = open(filepath, "r", encoding="utf-8")
    data = f.read()
    return data
