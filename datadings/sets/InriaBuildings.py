from datadings.sets import convert_segementation as convert_InriaBuildings
from datadings.sets import SegmentationReader as InriaBuildingsReader

NUM_INPUT_CHANNELS = 3
CROP_SIZE = 384

CLASSES = [
    '0. Building',
    '1. Background'
]

TRAIN_MSG_FILE = 'InriaBuildings_train.msgpack'
VAL_MSG_FILE = 'InriaBuildings_val.msgpack'
TEST_MSG_FILE = 'InriaBuildings_test.msgpack'