import os
import errno


def make_folder(directory: str) -> None:
    """Creates a folder in the provided location

    Parameters
    ----------
    directory : str
        Location of the directory to be created.

    Raises
    ----------
    OSError
        If the directory can not be created.
    """

    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
