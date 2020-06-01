import os.path as pt
import gzip
import json

import numpy as np

from .VOC2012 import median_frequency_weights


ROOT_DIR = pt.abspath(pt.dirname(__file__))


def _load_gzip_json(name):
    path = pt.join(ROOT_DIR, name)
    with gzip.open(path, mode='rt') as f:
        return json.load(f)


def load_statistics(name):
    d = _load_gzip_json(name)
    return d['INDEXES'], d['COUNTS']


def load_scenelabels():
    return _load_gzip_json('ADE20k_scenelabels.json.gz')


INDEXES, COUNTS = load_statistics('ADE20k_counts.json.gz')
WEIGHTS = median_frequency_weights(COUNTS)
SCENELABELS = load_scenelabels()


def index_to_color(array, _index_array=np.array(INDEXES, np.uint16)):
    array = np.take(_index_array, array)
    image = np.zeros(array.shape + (3,), dtype=np.uint8)
    image[..., 0] = array // 256 * 10
    image[..., 1] = array % 256
    return image
