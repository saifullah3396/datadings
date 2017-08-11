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
    0.01288745142261085,
    1.3572450331268846,
    3.200060719932177,
    1.1468105887322737,
    1.7561724718844058,
    1.4620014812604847,
    0.5781454431467643,
    0.7093150407797294,
    0.40307713990642213,
    1.0105491465411824,
    1.0,
    0.80490898571365,
    0.5360472058801579,
    1.0207266982237566,
    0.9181326938005482,
    0.2011471595899994,
    1.730787820036614,
    1.2007277776344862,
    0.7089888632304979,
    0.6361653058118041,
    1.2200394128690952
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
