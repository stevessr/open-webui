from datetime import datetime
from typing import Any

KEYS_TO_EXCLUDE = ["content", "pages", "tables", "paragraphs", "sections", "figures"]


def filter_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    metadata = {key: value for key, value in metadata.items() if key not in KEYS_TO_EXCLUDE}
    return metadata


def process_metadata(
    metadata: dict[str, Any],
) -> dict[str, Any]:
    for key, value in metadata.items():
        # Remove large fields
        if key in KEYS_TO_EXCLUDE:
            del metadata[key]

        # Convert non-serializable fields to strings
        if isinstance(value, datetime) or isinstance(value, list) or isinstance(value, dict):
            metadata[key] = str(value)
    return metadata
