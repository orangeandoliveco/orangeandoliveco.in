#!/usr/bin/env python3


def slugify(text: str) -> str:
    """Convert a string to a URL-friendly slug."""
    return (
        text.lower()
        .replace(" ", "-")
        .replace("_", "-")
        .replace("'", "")
        .replace('"', "")
    )
