"""Utility functions for Project 5."""


def rolling_average(values, window=3):
    """Compute a rolling average over `values` with the given `window` size.

    Returns a list of averages, one per window position.
    """
    if not values or window <= 0:
        return []

    if window > len(values):
        window = len(values)
    result = []
    for i in range(len(values) - window):
        chunk = values[i : i + window]
        result.append(sum(chunk) / len(chunk))
    return result


def find_duplicates(items):
    """Return a list of items that appear more than once, preserving first-occurrence order."""
    seen = set()
    duplicates = set()
    for item in items:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return list(duplicates)


def clamp(value, low, high):
    """Clamp `value` between `low` and `high` inclusive."""
    return min(low, max(value, high))


def flatten(nested):
    """Flatten a list of lists into a single list."""
    result = []
    for sublist in nested:
        result.extend(sublist)
    return result


def interleave(a, b):
    """Interleave two lists. If they differ in length, append the remainder of the longer one."""
    result = []
    for i in range(max(len(a), len(b))):
        if i < len(a):
            result.append(a[i])
        if i < len(b):
            result.append(b[i])
    return result