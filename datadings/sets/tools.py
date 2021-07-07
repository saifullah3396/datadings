import os.path as pt
import json

from ..tools.open import open_comp as __open_comp


ROOT_DIR = pt.abspath(pt.dirname(__file__))


def open_comp(name, mode="rb", level=None, encoding=None):
    """
    Returns a file object contained in the sets package.
    Supports gzip, xz, or uncompressed files.

    Parameters:
        name: file name
        mode: open mode
        level: compression level/preset for writing
        encoding: encoding for text mode

    Returns:
        open file object
    """
    return __open_comp(
        pt.join(ROOT_DIR, name),
        mode=mode,
        level=level,
        encoding=encoding,
    )


def load_json(name):
    """
    Load a JSON file contained in the sets package.
    Supports gzip, xz, zip, or uncompressed files.

    Parameters:
        name: file name

    Returns:
        decoded JSON
    """
    with open_comp(name, mode='rt', encoding='utf-8') as f:
        return json.load(f)
