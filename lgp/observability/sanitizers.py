"""
Output Sanitization for Langfuse Dashboard

Truncates large outputs to prevent dashboard rendering issues while
preserving full length information in metadata.
"""

from typing import Any, Dict, Union


def sanitize_for_dashboard(
    data: Any,
    max_length: int = 2000,
    truncation_suffix: str = "... [truncated]"
) -> tuple[Any, Dict[str, Any]]:
    """
    Sanitize data for Langfuse dashboard display.

    Truncates string values >max_length while preserving metadata about
    the original length. Returns both sanitized data and metadata.

    Args:
        data: Data to sanitize (dict, str, list, or primitive)
        max_length: Maximum string length before truncation (default: 2000)
        truncation_suffix: Suffix to append to truncated strings

    Returns:
        Tuple of (sanitized_data, metadata_dict)

    Examples:
        >>> sanitize_for_dashboard("short text")
        ("short text", {})

        >>> sanitize_for_dashboard("x" * 3000)
        ("xxx... [truncated]", {"output_truncated": True, "output_full_length": 3000})
    """
    metadata = {}

    if isinstance(data, str):
        if len(data) > max_length:
            sanitized = data[:max_length] + truncation_suffix
            metadata = {
                "output_truncated": True,
                "output_full_length": len(data),
                "output_displayed_length": len(sanitized)
            }
            return sanitized, metadata
        return data, metadata

    elif isinstance(data, dict):
        sanitized_dict = {}
        for key, value in data.items():
            if isinstance(value, str) and len(value) > max_length:
                sanitized_dict[key] = value[:max_length] + truncation_suffix
                metadata[f"{key}_truncated"] = True
                metadata[f"{key}_full_length"] = len(value)
            else:
                sanitized_dict[key] = value
        return sanitized_dict, metadata

    elif isinstance(data, list):
        # Truncate individual list items
        sanitized_list = []
        for i, item in enumerate(data):
            if isinstance(item, str) and len(item) > max_length:
                sanitized_list.append(item[:max_length] + truncation_suffix)
                metadata[f"item_{i}_truncated"] = True
                metadata[f"item_{i}_full_length"] = len(item)
            else:
                sanitized_list.append(item)
        return sanitized_list, metadata

    else:
        # Primitive types (int, float, bool, None)
        return data, metadata


def sanitize_workflow_result(result: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Sanitize workflow execution result for dashboard display.

    Specially handles common LangGraph output patterns while preserving
    structure and metadata.

    Args:
        result: Workflow execution result dictionary

    Returns:
        Tuple of (sanitized_result, sanitization_metadata)
    """
    sanitized = {}
    all_metadata = {}

    for key, value in result.items():
        sanitized_value, value_metadata = sanitize_for_dashboard(value)
        sanitized[key] = sanitized_value

        # Merge metadata
        if value_metadata:
            all_metadata.update({
                f"{key}_{k}": v for k, v in value_metadata.items()
            })

    return sanitized, all_metadata
