# x-cmds:file[unlisted,update]

"""
Shared helper utilities for commands.
"""

from functools import lru_cache
from _shared.consts import HASH_NAME_PATTERN, HEX_SEGMENT_PATTERN, SEP_SPLITTER_PATTERN, UUID_PATTERN


@lru_cache(maxsize=4096)
def is_likely_hash_name(name: str) -> bool:
    """Determine whether a file or directory name represents an auto-generated hash or identifier.\n
    ----------------------------------------------------------------------------------------------------
    *   `name` – File or directory base name to inspect."""

    if name.strip("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_~@. \t{}+/=") or len(name) < 2:
        return False
    elif bool(HASH_NAME_PATTERN.match(name)):
        return True

    # Cheap hex-segment check first; UUID regex (more expensive) only as fallback:
    stem = name.rsplit(".", 1)[0] if "." in name else name
    for segment in SEP_SPLITTER_PATTERN.split(stem):
        if len(segment) >= 8 and HEX_SEGMENT_PATTERN.match(segment):
            return True

    return bool(UUID_PATTERN.search(name))
