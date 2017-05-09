import io
import scipy.io


def loadmat(mat):
    try:
        return scipy.io.loadmat(mat)
    except IOError:
        buf = io.BytesIO(mat)
        return scipy.io.loadmat(buf)


def iter_fields(mat, ignore=set()):
    for k in mat.dtype.fields.keys():
        if k in ignore:
            continue
        yield k, mat[k]
