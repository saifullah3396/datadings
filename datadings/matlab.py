from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

import io
import scipy.io


def loadmat(mat):
    """ Load a Matlab "mat" file.

        @param mat: path, file-like object, or data
        @return: contents of the "mat" file
    """
    try:
        return scipy.io.loadmat(mat)
    except (TypeError, IOError):
        buf = io.BytesIO(mat)
        return scipy.io.loadmat(buf)


def iter_fields(arr, ignore=set()):
    """ Iterate over the fields of a structured numpy array
        (i.e., an array with a complex data type).
        Each iteration yields (fieldname, value).

        @param arr: a structured array
        @param ignore: set of fields to ignore
    """
    for k in arr.dtype.fields.keys():
        if k in ignore:
            continue
        yield k, arr[k]
