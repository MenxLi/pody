"""
General utility functions, 
functions in this module should not depend on any other modules in the project.
"""

def parse_storage_size(s: str) -> int:
    """ Parse the file size string to bytes """
    if s[-1].isdigit():
        return int(s)
    unit = s[-1].lower()
    match unit:
        case 'b': return int(s[:-1])
        case 'k': return int(s[:-1]) * 1024
        case 'm': return int(s[:-1]) * 1024**2
        case 'g': return int(s[:-1]) * 1024**3
        case 't': return int(s[:-1]) * 1024**4
        case _: raise ValueError(f"Invalid file size string: {s}")

def format_storage_size(size: int, precision: int = 2) -> str:
    """ Format the file size to human-readable format """
    assert isinstance(size, int), "size should be an integer"
    if size < 1024:
        return f"{size}B"
    if size < 1024**2:
        return f"{size/1024:.{precision}f}K" if precision > 0 else f"{size//1024}K"
    if size < 1024**3:
        return f"{size/1024**2:.{precision}f}M" if precision > 0 else f"{size//1024**2}M"
    if size < 1024**4:
        return f"{size/1024**3:.{precision}f}G" if precision > 0 else f"{size//1024**3}G"
    return f"{size/1024**4:.{precision}f}T" if precision > 0 else f"{size//1024**4}T"