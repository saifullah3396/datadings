from .tools import load_json
from .VOC2012 import median_frequency_weights

import numpy as np


def load_statistics(name):
    d = load_json(name)
    return d['INDEXES'], d['COUNTS']


INDEXES, COUNTS = load_statistics('ADE20k_counts.json.xz')
WEIGHTS = median_frequency_weights(COUNTS)
SCENELABELS = load_json('ADE20k_scenelabels.json.gz')


def index_to_color(array, _index_array=np.array(INDEXES, np.uint16)):
    array = np.take(_index_array, array)
    image = np.zeros(array.shape + (3,), dtype=np.uint8)
    image[..., 0] = array // 256 * 10
    image[..., 1] = array % 256
    return image
