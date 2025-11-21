from typing import Any, Dict


def merge_dict(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    # get only proper args
    valid_args = [arg for arg in args if isinstance(arg, dict)]

    # Merge args into one dictionary
    merged_dict = {k: v for arg in valid_args for k, v in arg.items()}

    # Add kwargs to the merged dictionary
    merged_dict.update(kwargs)

    return merged_dict
