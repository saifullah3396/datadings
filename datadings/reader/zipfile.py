from __future__ import print_function, division, unicode_literals

import os
import os.path as pt
import itertools as it
import zipfile

from .reader import pack
from .listreader import ListReader
from .directory import match
from .directory import check_included
from .directory import yield_file
from .directory import get_labels
from .directory import convert_ImageClassificationData


def glob_pattern(infos, pattern):
    parts = pattern.split(os.sep)
    label_index = None
    try:
        label_index = parts.index('{LABEL}')
        pattern = pattern.replace('{LABEL}', '*', 1)
    except ValueError:
        pass
    for i in infos:
        if i.is_dir():
            continue
        if match(i.filename, pattern):
            if label_index is not None:
                label = i.filename.split(os.sep)[label_index]
            else:
                label = None
            yield i.filename, label


def yield_zipfile(zipfile, patterns, separator):
    infos = None
    gens = []
    for pattern in patterns:
        if pt.isfile(pattern):
            # pattern is csv-like (path, label) file
            gens.append(yield_file(pattern, separator))
        else:
            if infos is None:
                infos = zipfile.infolist()
            # pattern is glob-pattern
            gens.append(glob_pattern(infos, pattern))
    return it.chain(*gens)


class ZipFileReader(ListReader):
    def __init__(
            self,
            path,
            patterns=('{LABEL}/**',),
            separator='\t',
            convertfun=convert_ImageClassificationData,
            include=(),
            exclude=(),
    ):
        self._zipfile = zipfile.ZipFile(path)
        self._convertfun = convertfun
        samples = list(yield_zipfile(self._zipfile, patterns, separator))
        samples = [{'key': s, 'label': l} for s, l in samples
                   if check_included(s, include, exclude)]
        labels = sorted(get_labels(samples))
        self.labels = {l: i for i, l in enumerate(labels)}
        ListReader.__init__(self, samples)

    def __next__(self):
        try:
            s = dict(self._samples[self._i])
            self._i += 1
            s['data'] = self._zipfile.read(s['key'])
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
