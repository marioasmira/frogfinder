def is_between(value, value_range) -> bool:
    """Checks if the first argument is between the 2 values of the second argument

    Parameters
    ----------
    value : int or float
        The value to be tested.
    value_range : list with two values
        The bounds to test 'value' with.

    Returns
    -------
    bool
        If 'value' is within the range in 'value_range'.
    """

    if value_range[1] < value_range[0]:
        return value >= value_range[0] or value <= value_range[1]
    return value_range[0] <= value <= value_range[1]
