from collections import OrderedDict

from .tools import open_comp


def __load_synsets():
    with open_comp('ILSVRC2012_synsets.txt.xz', 'rt', encoding='utf-8') as f:
        return OrderedDict(line.strip('\n').split(' ', 1) for line in f)


SYNSET_WORDS = __load_synsets()
SYNSET_LIST = list(SYNSET_WORDS)
SYNSETS = {syn: i for i, syn in enumerate(SYNSET_WORDS)}
