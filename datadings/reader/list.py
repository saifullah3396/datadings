from __future__ import print_function, division, unicode_literals

import os.path as pt

from .reader import Reader, pack
from ..sets import ImageClassificationData


def load_lines(path):
    with open(path) as f:
        return [l.strip('\n ') for l in f.readlines()]


def get_labels(samples):
    labels = set(s.get('label') for s in samples)
    if None in labels:
        labels.remove(None)
    return labels


def convert_ImageClassificationData(sample):
    return ImageClassificationData(
        sample['data'],
        sample['label'],
        sample['key']
    )


def noop(sample):
    return sample.get('data')


class ListReader(Reader):
    """
    A simple Reader that holds a list of samples.
    """
    def __init__(
            self,
            samples,
            labels=None,
            convertfun=convert_ImageClassificationData,
            loadfun=noop,
    ):
        """

        :param samples: list of samples
        :param labels: list of labels in correct order;
                       if None, extract labels from samples and sort;
                       if
        :param convertfun:
        :param loadfun:
        """
        self._convertfun = convertfun
        self._loadfun = loadfun
        self._samples = samples
        self._index = {s.get('key', 1): i for i, s in enumerate(samples)}
        self._keys = {i: s.get('key', i) for i, s in enumerate(samples)}
        labels = labels or sorted(get_labels(samples))
        try:
            labels = load_lines(labels)
        except (TypeError, FileNotFoundError, IOError):
            pass
        self._labels = {l: i for i, l in enumerate(labels)}
        self._i = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def iter(self, yield_key=False):
        """
        :param yield_key: if True, yields (key, sample) pairs
        """
        try:
            if yield_key:
                while 1:
                    yield self.get_key(), self.next()
            else:
                while 1:
                    yield self.next()
        except StopIteration:
            self._i = 0
            raise

    __iter__ = iter

    def __len__(self):
        return len(self._samples)

    def __next__(self):
        try:
            s = dict(self._samples[self._i])
            self._i += 1
            if self._loadfun is not None:
                s['data'] = self._loadfun(s)
            if s['label'] is None:
                s.pop('label')
            else:
                s['labelstring'] = s['label']
                s['label'] = self._labels[s['label']]
            return self._convertfun(s)
        except IndexError:
            raise StopIteration()

    next = __next__

    def rawnext(self):
        """
        Return the next sample as raw bytes.
        :return:
        """
        return pack(self.next())

    def rawiter(self, yield_key=False):
        """
        Like iter, but yields raw bytes.

        :param yield_key: if True, yields (key, sample) pairs
        """
        try:
            if yield_key:
                while 1:
                    yield self.get_key(), self.rawnext()
            else:
                while 1:
                    yield self.rawnext()
        except StopIteration:
            self._i = 0
            raise

    def seek_index(self, index):
        """
        Seek to the given index.
        """
        self._i = index

    seek = seek_index

    def seek_key(self, key):
        self._i = self._index.get(key, None) or self._i

    def get_key(self, index=None):
        """
        Get the key of a sample.
        Uses current index if none is given.
        """
        return self._keys.get(index or self._i, self._i)
