import gzip
import lzma


def open_comp(path, mode="rb", level=None, encoding=None):
    """
    Returns a file object contained in the sets package.
    Supports gzip, xz, or uncompressed files.

    Parameters:
        path: file path
        mode: open mode
        level: compression level/preset for writing
        encoding: encoding for text mode

    Returns:
        open file object
    """
    path = str(path)
    if path.endswith('.gz'):
        return gzip.open(path, mode=mode, compresslevel=level, encoding=encoding)
    elif path.endswith('.xz'):
        return lzma.open(path, mode=mode, preset=level, encoding=encoding)
    else:
        return open(path, mode=mode, encoding=encoding)
