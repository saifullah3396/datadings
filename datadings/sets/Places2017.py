from __future__ import print_function, division

import os.path as pt
import gzip
import json

import numpy as np

from .VOC2012 import median_frequency_weights
from .ADE20k import load_statistics
from .ADE20k import SCENELABELS


ROOT_DIR = pt.abspath(pt.dirname(__file__))


CLASSES = [
    'background',
    'wall', 'building', 'sky', 'floor', 'tree',
    'ceiling', 'road', 'bed ', 'windowpane', 'grass',
    'cabinet', 'sidewalk', 'person', 'earth', 'door',
    'table', 'mountain', 'plant', 'curtain', 'chair',
    'car', 'water', 'painting', 'sofa', 'shelf',
    'house', 'sea', 'mirror', 'rug', 'field',
    'armchair', 'seat', 'fence', 'desk', 'rock',
    'wardrobe', 'lamp', 'bathtub', 'railing', 'cushion',
    'base', 'box', 'column', 'signboard', 'chest of drawers',
    'counter', 'sand', 'sink', 'skyscraper', 'fireplace',
    'refrigerator', 'grandstand', 'path', 'stairs', 'runway',
    'case', 'pool table', 'pillow', 'screen door', 'stairway',
    'river', 'bridge', 'bookcase', 'blind', 'coffee table',
    'toilet', 'flower', 'book', 'hill', 'bench',
    'countertop', 'stove', 'palm', 'kitchen island', 'computer',
    'swivel chair', 'boat', 'bar', 'arcade machine', 'hovel',
    'bus', 'towel', 'light', 'truck', 'tower',
    'chandelier', 'awning', 'streetlight', 'booth', 'television',
    'airplane', 'dirt track', 'apparel', 'pole', 'land',
    'bannister', 'escalator', 'ottoman', 'bottle', 'buffet',
    'poster', 'stage', 'van', 'ship', 'fountain',
    'conveyer belt', 'canopy', 'washer', 'plaything', 'swimming pool',
    'stool', 'barrel', 'basket', 'waterfall', 'tent',
    'bag', 'minibike', 'cradle', 'oven', 'ball',
    'food', 'step', 'tank', 'trade name', 'microwave',
    'pot', 'animal', 'bicycle', 'lake', 'dishwasher',
    'screen', 'blanket', 'sculpture', 'hood', 'sconce',
    'vase', 'traffic light', 'tray', 'ashcan', 'fan',
    'pier', 'crt screen', 'plate', 'monitor', 'bulletin board',
    'shower', 'radiator', 'glass', 'clock', 'flag',
]
INDEXES, COUNTS = load_statistics('Places2017_counts.json.gz')
WEIGHTS = median_frequency_weights(COUNTS)
with gzip.open(
        pt.join(ROOT_DIR, 'Places2017_colors.json.gz'), 'rt'
) as f:
    COLORS = np.array(json.load(f), dtype=np.uint8)


def index_to_color(array):
    return COLORS[array]


class Places2017Data(dict):
    def __init__(self, image, tasks, key, classes):
        super(Places2017Data, self).__init__(
            image=image, tasks=tasks, key=key, classes=classes,
        )


class Places2017Task(dict):
    def __init__(self, label_image, class_weights):
        super(Places2017Task, self).__init__(
            label_image=label_image, class_weights=class_weights,
        )
