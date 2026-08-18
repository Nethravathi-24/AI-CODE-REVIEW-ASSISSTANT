"""Fixture containing dangerous eval usage."""


def evaluate_expression(user_payload: str) -> None:
    """Executes arbitrary user string using eval."""
    eval(user_payload)
