from __future__ import print_function, division

import numpy as np

from datadings.sets import convert_segementation as convert_VOC2012
from datadings.sets import SegmentationReader as VOC2012Reader


CLASSES = [
    'background',
    'aeroplane',
    'bicycle',
    'bird',
    'boat',
    'bottle',
    'bus',
    'car',
    'cat',
    'chair',
    'cow',
    'diningtable',
    'dog',
    'horse',
    'motorbike',
    'person',
    'pottedplant',
    'sheep',
    'sofa',
    'train',
    'tvmonitor',
    # 'void',
]


WEIGHTS = [
    0.0145713832544,
    1.60683092026,
    3.77297836903,
    1.28170896859,
    1.88943180167,
    1.88578789944,
    0.653870695412,
    0.818682829582,
    0.423707463071,
    1.0,
    1.38825575894,
    0.846068111492,
    0.65848636728,
    1.25280997522,
    0.99046264316,
    0.238506673931,
    1.71287941377,
    1.26907871187,
    0.792056926623,
    0.718102432636,
    1.21788199137,
]


def bitget(byteval, idx):
    return (byteval & (1 << idx)) != 0


def class_color_map(n=256):
    """
    Create class colors as per VOC devkit.

    Adapted from:
    https://gist.github.com/wllhf/a4533e0adebe57e3ed06d4b50c8419ae

    :param n: number of classes
    :param norm: divide colors by this factor
    :return: numpy array of shape (n, 3)
    """
    cmap = np.zeros((n, 3), dtype=np.uint8)
    for i in range(n):
        r = g = b = 0
        c = i
        for j in range(8):
            r |= (bitget(c, 0) << 7-j)
            g |= (bitget(c, 1) << 7-j)
            b |= (bitget(c, 2) << 7-j)
            c >>= 3
        cmap[i] = np.array([r, g, b])
    return cmap


M = class_color_map(256)[:21]


def index_to_color(array):
    return M[array]
