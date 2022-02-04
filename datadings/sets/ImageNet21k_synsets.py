import json
from collections import OrderedDict

from .tools import open_comp


NUM_VALID_SYNSETS = 10450
VAL_SAMPLES_PER_SYNSET = 50


def __load_synsets():
    with open_comp('ImageNet21k_synsets.json.xz', 'rt', encoding='utf-8') as f:
        return json.load(f, object_pairs_hook=OrderedDict)


meta = __load_synsets()

SYNSET_WORDS = meta['class_description']
SYNSET_LIST = list(SYNSET_WORDS)
SYNSET_TREE_LIST = meta['class_tree_list']
SYNSETS = {syn: i for i, syn in enumerate(SYNSET_WORDS)}

NUM_TRAIN_SAMPLES = meta['train']
NUM_VAL_SAMPLES = meta['val']

assert NUM_VALID_SYNSETS == len(SYNSET_LIST)
assert NUM_VAL_SAMPLES == len(SYNSET_LIST) * VAL_SAMPLES_PER_SYNSET

del meta
