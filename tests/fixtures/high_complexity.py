"""Fixture containing a function with high cyclomatic complexity (>10)."""


def complex_decision_engine(score: int, mode: str, is_admin: bool) -> str:
    """Function with cyclomatic complexity exceeding the threshold of 10."""
    if score > 95:
        if is_admin:
            status = "A++"
        else:
            status = "A+"
    elif score > 90:
        if is_admin:
            status = "A+"
        else:
            status = "A"
    elif score > 80:
        if mode == "strict":
            status = "B+"
        else:
            status = "B"
    elif score > 70:
        if mode == "strict":
            status = "C+"
        else:
            status = "C"
    elif score > 60:
        if mode == "strict":
            status = "D+"
        else:
            status = "D"
    elif score > 50:
        status = "E"
    else:
        status = "F"

    return status
