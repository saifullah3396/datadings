from typing import Union
from typing import Sequence
from typing import Iterable
from typing import Callable
from pathlib import Path

from natsort import natsorted

from .reader import Reader
from ..msgpack import packb


def load_lines(path):
    with open(path, encoding='utf-8') as f:
        return [l.strip('\n ') for l in f]


canary = object()


def sorted_labels(samples):
    # try to get label, but with canary instead of None as default
    labels = set(s.get('label', canary) for s in samples)
    if None in labels:
        raise ValueError('Found None as label. '
                         'Labels must be given to reader to use None.')
    # remove canaries from the mine
    if canary in labels:
        labels.remove(canary)
    return natsorted(labels)


class ListReader(Reader):
    """
    Reader that holds a list of samples.
    Functions can be given to load data on the fly and/or perform further
    conversion steps.

    Two special keys ``"key"`` and ``"label"`` in samples are used:

    - ``"key"`` is a unique identifier for samples.
      Sample index is added to samples if it is missing.
    - ``"label"`` holds an optional label.
      Replaced by a numeric index to the list of labels if
      ``numeric_labels`` is true.
      The original label is retained as ``"_label"``.

    Note:
        If ``labels`` argument is not given, the list of all labels will
        be extracted from all samples.
        The list of all labels is :py:func:`natsorted <natsort.natsorted>`
        to determine numerical labels.

    Important:
        Since ``None`` is not sortable, the ``labels`` argument must be
        given to use ``None`` as a label.

    Parameters:
        samples: Sequence of samples. Must be indexable, so no
                 generators or one-time iterators.
        labels: Optional. List of labels in desired order,
                or path to file with one label per line.
                If ``None``, get ``"label"`` keys from samples, if any,
                and sort.
        numeric_labels: If true, convert labels to numeric index to list
                        of all labels.
        convertfun: Callable ``convertfun(sample: dict) -> dict``.
                    Applied to samples. Result is returned by ``next()``.
        loadfun: Callable ``loadfun(sample: dict) -> dict``.
                 Applied to samples. Result is further transformed by
                 ``convertfun``.
    """
    def __init__(
            self,
            samples: Sequence[dict],
            labels: Union[Iterable, Path] = None,
            numeric_labels=True,
            loadfun: Callable = None,
            convertfun: Callable = None,
    ):
        super().__init__()
        self._convertfun = convertfun
        self._loadfun = loadfun
        self._samples = samples
        self._index = {}
        for i, sample in enumerate(self._samples):
            key = sample.get('key', i)
            if key in self._index:
                raise ValueError('duplicate key %r' % key)
            sample['key'] = key
            self._index[key] = i
        self.labels = labels or sorted_labels(self._samples)
        try:
            self.labels = load_lines(labels)
        except TypeError:
            pass
        self._numeric_labels = numeric_labels
        if numeric_labels:
            self._label_index = {str(l): i for i, l in enumerate(self.labels)}
            self._label_index.update({l: i for i, l in enumerate(self.labels)})

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __len__(self):
        return len(self._samples)

    def find_key(self, index):
        return self._samples[index]['key']

    def find_index(self, key):
        return self._index[key]

    def get(self, index, yield_key=False, raw=False):
        sample = dict(self._samples[index])

        # load and convert sample
        if self._loadfun is not None:
            sample = self._loadfun(sample)
        if self._numeric_labels and 'label' in sample:
            sample['_label'] = sample['label']
            sample['label'] = self._label_index[sample['label']]
        if self._convertfun is not None:
            sample = self._convertfun(sample)

        # return sample
        key = sample['key']
        if raw:
            sample = packb(sample)
        if yield_key:
            return key, sample
        else:
            return sample

    def slice(self, start, stop=None, step=None, yield_key=False, raw=False):
        start, stop, step = slice(start, stop, step).indices(len(self._samples))
        for index in range(start, stop, step):
            yield self.get(index, yield_key=yield_key, raw=raw)
