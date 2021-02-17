import io
import scipy.io


def loadmat(mat):
    """
    Load a Matlab "mat" file.

    Parameters:
        mat: Path, file-like object, or data.

    Returns:
        Contents of the Matlab file.
    """
    try:
        return scipy.io.loadmat(mat)
    except (ValueError, TypeError, IOError):
        buf = io.BytesIO(mat)
        # noinspection PyTypeChecker
        return scipy.io.loadmat(buf)


def iter_fields(arr, ignore=()):
    """
    Iterate over the fields of a structured numpy array
    (i.e., an array with a complex data type).
    Each iteration yields (fieldname, value).

    Parameters:
        arr: A structured array.
        ignore: Fields to ignore.

    Returns:
        Yields individual fields from the array.
    """
    for k in arr.dtype.fields.keys():
        if k in ignore:
            continue
        yield k, arr[k]
