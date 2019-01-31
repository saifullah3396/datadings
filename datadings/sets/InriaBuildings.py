from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import


NUM_INPUT_CHANNELS = 3
CROP_SIZE = 384

CLASSES = [
    '0. Building',
    '1. Background'
]

TRAIN_MSG_FILE = 'InriaBuildings_train.msgpack'
VAL_MSG_FILE = 'InriaBuildings_val.msgpack'
TEST_MSG_FILE = 'InriaBuildings_test.msgpack'