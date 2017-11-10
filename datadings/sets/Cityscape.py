from datadings.sets import convert_depth_segementation as convert_cityscape
from datadings.sets import DepthSegmentationReader as CityscapeReader


import numpy as np


def median_frequency_weights(counts):
    total = sum(counts)
    freq = [n/total for n in counts]
    # cannot serialize numpy scalars,
    # weights must be Python numbers!
    median_freq = float(np.median(freq))
    return [median_freq/f for f in freq]


#WEIGHTS = median_frequency_weights(_COUNTS)
#SCENELABELS = load_scenelabels()

ignored_class_indices = [0, 1, 2, 3, 4, 5, 6, 9, 10, 14, 15, 16, 18,
                         29, 30, -1]
used_class_indices = [7, 8, 11, 12, 13, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27,
                      28, 31, 32, 33]
