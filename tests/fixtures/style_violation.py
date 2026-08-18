"""Fixture containing intentional PEP 8 formatting and style violations."""


def style_violation_function():
    # Long line exceeding standard 79 character limit (E501)
    detailed_message = "This is a deliberately long string formatted to exceed the standard PEP 8 line length limit of 79 characters."
    x=10+20    
    return detailed_message, x
