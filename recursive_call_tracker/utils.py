def prettify_kwargs_repr(kwargs_dict: dict) -> str:
    """Create a pretty repr of `kwargs_dict` in the form of dict(kwarg=value)."""
    return "".join(
        (
            "dict(",
            ", ".join(f"{name}={value!r}" for name, value in kwargs_dict.items()),
            ")",
        ),
    )
