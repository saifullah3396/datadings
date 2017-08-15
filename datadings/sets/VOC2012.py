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


INDEXES = [
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
]


COUNTS = [
    1096.41576898,
    10.3095622192,
    4.12905110457,
    12.0429902908,
    8.58478973106,
    8.43477098778,
    24.74073322,
    19.9420767928,
    37.4964065785,
    16.051006968,
    11.7559521937,
    18.2245417825,
    23.5776165031,
    12.9779183112,
    15.8809800135,
    66.9628144956,
    9.05575018634,
    12.3852355498,
    20.2024935412,
    22.2167849844,
    12.6127555631,
]


WEIGHTS = [
    0.0144844505732,
    1.54041264564,
    3.84615729165,
    1.31869075952,
    1.84989737792,
    1.88279919354,
    0.641896093873,
    0.796355373538,
    0.423533385266,
    0.989407084873,
    1.35088844798,
    0.871406271993,
    0.673561723738,
    1.22369240063,
    1.0,
    0.237161178679,
    1.75369016224,
    1.28225094708,
    0.786090092348,
    0.714818999447,
    1.25912057314,
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
