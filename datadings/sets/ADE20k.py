from __future__ import print_function, division

import os.path as pt
import gzip
import json

import numpy as np

from datadings.sets.VOC2012 import median_frequency_weights
from datadings.sets import convert_segementation as convert_ADE20K
from datadings.sets import SegmentationReader as ADE20KReader


ROOT_DIR = pt.abspath(pt.dirname(__file__))


def load_statistics(name):
    path = pt.join(ROOT_DIR, name)
    with gzip.open(path, mode='rt') as f:
        d = json.load(f)
    return d['INDEXES'], d['COUNTS']


INDEXES, COUNTS = load_statistics('ADE20k_counts.json.gz')
WEIGHTS = median_frequency_weights(COUNTS)


def index_to_color(array, _index_array=np.array(INDEXES, np.uint16)):
    array = np.take(_index_array, array)
    image = np.zeros(array.shape + (3,), dtype=np.uint8)
    image[..., 0] = array // 256 * 10
    image[..., 1] = array % 256
    return image
