from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

import os
import os.path as pt
import itertools as it

import glob2
from glob2.fnmatch import fnmatch

from .list import ListReader
from .list import convert_ImageClassificationData


def match(f, p):
    return fnmatch(f, p, case_sensitive=False)


def check_included(filename, include, exclude):
    return (not include or any(match(filename, i) for i in include)) \
        and not any(match(filename, e) for e in exclude)


def yield_file(infile, prefix, separator):
    with open(infile) as f:
        for line in f:
            path, label = line.strip('\n').split(separator)[:2]
            try:
                label = int(label)
            except ValueError:
                pass
            yield path.replace(prefix, ''), path, label


def load_binary(sample):
    with open(sample['path'], 'rb') as f:
        return f.read()


def glob_pattern(pattern, prefix):
    parts = pattern.split(os.sep)
    label_index = None
    try:
        label_index = parts.index('{LABEL}')
        if not prefix:
            prefix = pattern[:pattern.index('{LABEL}')]
        pattern = pattern.replace('{LABEL}', '*', 1)
    except ValueError:
        pass
    for p in glob2.iglob(pattern):
        if pt.isfile(p):
            if label_index is not None:
                label = p.split(os.sep)[label_index]
            else:
                label = None
            yield p.replace(prefix, ''), p, label


def yield_directory(patterns, separator):
    if len(patterns) > 1:
        prefix = os.path.commonprefix(patterns)
    else:
        prefix = ''
    if '{LABEL}' in prefix:
        prefix = prefix[:prefix.index('{LABEL}')]
    gens = []
    for pattern in patterns:
        if pt.isfile(pattern):
            # pattern is csv-like (path, label) file
            gens.append(yield_file(pattern, prefix, separator))
        else:
            # pattern is glob-pattern
            gens.append(glob_pattern(pattern, prefix))
    return it.chain(*gens)


class DirectoryReader(ListReader):
    def __init__(
            self,
            patterns,
            separator='\t',
            convertfun=convert_ImageClassificationData,
            include=(),
            exclude=(),
            labels=None,
    ):
        samples = list(yield_directory(patterns, separator))
        samples = [{'key': k, 'label': l, 'path': p} for k, p, l in samples
                   if check_included(p, include, exclude)]
        ListReader.__init__(self, samples, labels, convertfun, load_binary)
