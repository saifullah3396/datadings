from __future__ import print_function, division, unicode_literals

import os
import os.path as pt
import itertools as it
import io

import glob2
from glob2.fnmatch import fnmatch

from datadings.reader.listreader import ListReader
from datadings.reader.reader import pack
from ..sets import ImageClassificationData


def match(f, p):
    return fnmatch(f, p, case_sensitive=False)


def check_included(filename, include, exclude):
    return (not include or any(match(filename, i) for i in include)) \
        and not any(match(filename, e) for e in exclude)


def yield_file(infile, separator):
    with open(infile) as f:
        for line in f:
            path, label = line.strip('\n').split(separator)[:2]
            try:
                label = int(label)
            except ValueError:
                pass
            yield path, label


def load_binary(path):
    with io.FileIO(path, 'rb') as f:
        return f.read()


def glob_pattern(pattern):
    parts = pattern.split(os.sep)
    label_index = None
    try:
        label_index = parts.index('{LABEL}')
        pattern = pattern.replace('{LABEL}', '*', 1)
    except ValueError:
        pass
    for p in glob2.iglob(pattern):
        if pt.isfile(p):
            if label_index is not None:
                label = p.split(os.sep)[label_index]
            else:
                label = None
            yield p, label


def yield_directory(patterns, separator):
    gens = []
    for pattern in patterns:
        if pt.isfile(pattern):
            # pattern is csv-like (path, label) file
            gens.append(yield_file(pattern, separator))
        else:
            # pattern is glob-pattern
            gens.append(glob_pattern(pattern))
    return it.chain(*gens)


def get_labels(samples):
    labels = set(s['label'] for s in samples)
    if None in labels:
        labels.remove(None)
    return labels


def convert_ImageClassificationData(sample):
    return ImageClassificationData(
        sample['data'],
        sample['label'],
        sample['key']
    )


class DirectoryReader(ListReader):
    def __init__(
            self,
            patterns,
            separator='\t',
            convertfun=convert_ImageClassificationData,
            include=(),
            exclude=(),
    ):
        self._convertfun = convertfun
        samples = list(yield_directory(patterns, separator))
        samples = [{'key': s, 'label': l} for s, l in samples
                   if check_included(s, include, exclude)]
        labels = sorted(get_labels(samples))
        self.labels = {l: i for i, l in enumerate(labels)}
        ListReader.__init__(self, samples)

    def __next__(self):
        try:
            s = dict(self._samples[self._i])
            self._i += 1
            s['data'] = load_binary(s['key'])
            if s['label'] is None:
                s.pop('label')
            else:
                s['labelstring'] = s['label']
                s['label'] = self.labels[s['label']]
            return self._convertfun(s)
        except IndexError:
            raise StopIteration()

    next = __next__

    def rawnext(self):
        return pack(self.next())
