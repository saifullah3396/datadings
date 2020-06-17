import numpy as np


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


def median_frequency_weights(counts):
    total = sum(counts)
    freq = [n/total for n in counts]
    # cannot serialize numpy scalars,
    # weights must be Python numbers!
    median_freq = float(np.median(freq))
    return [median_freq/f for f in freq]


WEIGHTS = median_frequency_weights(COUNTS)


def bitget(byteval, idx):
    return (byteval & (1 << idx)) != 0


def class_color_map(n=256):
    """
    Create class colors as per VOC devkit.

    Adapted from:
    https://gist.github.com/wllhf/a4533e0adebe57e3ed06d4b50c8419ae

    Parameters:
        n: Number of classes.

    Returns:
        Numpy array of shape (n, 3).
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


COLORS = class_color_map(256)[:21]


def index_to_color(array):
    return COLORS[array]
