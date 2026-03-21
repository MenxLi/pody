"""
General utility functions, 
functions in this module should not depend on any other modules in the project.
"""
import time
from collections import OrderedDict
from functools import wraps

def parse_storage_size(s: str) -> int:
    """ Parse the file size string to bytes """
    if s[-1].isdigit():
        return int(s)
    unit = s[-1].lower()
    match unit:
        case 'b': return int(float(s[:-1]))
        case 'k': return int(float(s[:-1])) * 1024
        case 'm': return int(float(s[:-1])) * 1024**2
        case 'g': return int(float(s[:-1])) * 1024**3
        case 't': return int(float(s[:-1])) * 1024**4
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

def format_time(seconds: int | float) -> str:
    """ Format the time in seconds to human-readable format """
    assert isinstance(seconds, (int, float)), "seconds should be an integer or float"
    if isinstance(seconds, float):
        seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds//60}m {seconds%60}s"
    if seconds < 86400:
        return f"{seconds//3600}h {seconds%3600//60}m {seconds%60}s"
    return f"{seconds//86400}d {seconds%86400//3600}h {seconds%3600//60}m {seconds%60}s"

def expiry_cache(seconds: float, buffer_size: int = 128):
    """ A decorator to cache the result of a function for a certain amount of time (in seconds) """
    def decorator(func):
        cache: OrderedDict[tuple, tuple] = OrderedDict()
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(kwargs.items()))
            if key in cache and time.time() - cache[key][1] < seconds:
                return cache[key][0]
            result = func(*args, **kwargs)
            if len(cache) >= buffer_size:
                cache.popitem(last=False)
            cache[key] = (result, time.time())
            return result
        return wrapper
    return decorator