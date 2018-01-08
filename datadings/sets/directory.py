from __future__ import print_function, division

import os
import os.path as pt
import io
import itertools as it

import glob2
import msgpack

from ..reader import Reader


def load_binary(path):
    with io.FileIO(path, 'rb') as f:
        return f.read()


def iglob_files(pattern):
    for p in glob2.iglob(pattern):
        if pt.isfile(p):
            yield p


def find_labels_for_pattern(pattern):
    parts = pattern.split(os.sep)
    try:
        label_index = parts.index('{LABEL}')
    except ValueError:
        label_index = len(parts)
    root_dir = os.sep.join(parts[:label_index]) or '.'
    labels = sorted([f for f in os.listdir(root_dir) if pt.isdir(f)])
    return root_dir, labels


def check_included(label, include, exclude):
    return (include and label in include) \
        or (label not in exclude)


def yield_lines(infile):
    with open(infile) as f:
        for l in f:
            yield l.strip('\n')


def yield_file(infile, separator):
    with open(infile) as f:
        for line in f:
            path, label = line.strip('\n').split(separator)
            try:
                label = int(label)
            except ValueError:
                pass
            yield path, label


def glob_labels(root_dir, labels):
    for label in labels:
        for path in iglob_files(pt.join(root_dir, label, '**')):
            yield path, label


def find_files(patterns, separator):
    gens = []
    labels = set()
    for pattern in patterns:
        if pt.isfile(pattern):
            # pattern is csv-like path-label file
            gens.append(yield_file(pattern, separator))
        else:
            # pattern corresponds to a directory tree
            # with labeled subdirectories
            root_dir, new_labels = find_labels_for_pattern(pattern)
            labels.update(new_labels)
            gens.append(glob_labels(root_dir, labels))
    return labels, it.chain(*gens)


class DirectoryReader(Reader):
    def __init__(
            self,
            patterns,
            label_sorting='alphabetical',
            separator='\t',
    ):
        self._patterns = patterns
        self._sorting = label_sorting
        labels, files = find_files(patterns, separator)
        self._files = list(files)
        if pt.isfile(label_sorting):
            labels = yield_lines(label_sorting)
        elif label_sorting == 'alphabetical':
            labels = sorted(labels)
        self._labels = {label: i for i, label in enumerate(labels)}
        self.__len = None
        self._i = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def iter(self, yield_key=False):
        """
        :param yield_key: if True, yields (key, sample) pairs
        """
        if yield_key:
            while 1:
                yield self.get_key(), self.next()
        else:
            while 1:
                yield self.next()

    __iter__ = iter

    def __len__(self):
        return len(self._files)

    def __next__(self):
        path, label = self._files[self._i]
        return load_binary(path), self._labels[label]

    next = __next__

    def rawnext(self):
        """
        Return the next sample as raw bytes.
        :return:
        """
        return msgpack.packb(self.next())

    def rawiter(self, yield_key=False):
        """
        Like iter, but yields raw bytes.

        :param yield_key: if True, yields (key, sample) pairs
        """
        if yield_key:
            while 1:
                yield self.get_key(), self.rawnext()
        else:
            while 1:
                yield self.rawnext()

    def seek_index(self, index):
        """
        Seek to the given index.
        """
        self._i = index

    seek = seek_index

    seek_key = seek_index

    def get_key(self, index=None):
        """
        Get the key of a sample.
        Uses current index if none is given.
        """
        return index or self._i

    def _convert(self, item):
        """
        Implement this method to convert samples to proper
        data types before they are returned.
        """
        return item
