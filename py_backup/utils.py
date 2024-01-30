def get_filtered_args(args: list, unwanted_args: set | None = None) -> list:
    """Short function to remove duplicate args and remove unwanted_args while
    maintaining args list order (if duplicate first position is kept).

    Args:
        args (list): Unfiltered args list
        unwanted_args (set): Set of unwanted args to remove. Defaults to None if not provided.

    Returns:
        list: deduplicated list without unwanted args with initial order intact
    """
    excl = unwanted_args if unwanted_args else set()
    filtered_args_dict = {key: None for key in args if key not in excl}
    return list(filtered_args_dict)


def sanitize_subprocess_kwargs(kwargs: dict | None) -> dict:
    """Sanitize the subprocess keyword arguments."""
    kwargs.pop("shell", None)
    return kwargs
