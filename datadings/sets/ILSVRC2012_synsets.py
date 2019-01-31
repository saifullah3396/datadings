from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

import os.path as pt
import gzip
from collections import OrderedDict


__p = pt.join(pt.abspath(pt.dirname(__file__)), 'ILSVRC2012_synsets.txt.gz')
with gzip.open(__p, mode='rt', encoding='utf-8') as __f:
    SYNSET_WORDS = OrderedDict(l.strip('\n').split(' ', 1) for l in __f)
SYNSET_LIST = list(SYNSET_WORDS)
SYNSETS = {s: i for i, s in enumerate(SYNSET_WORDS)}
