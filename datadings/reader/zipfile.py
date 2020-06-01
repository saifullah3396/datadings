import os
import os.path as pt
import itertools as it
import zipfile

from .list import ListReader
from .list import convert_ImageClassificationData
from .directory import match
from .directory import check_included
from .directory import yield_file


def glob_pattern(infos, pattern):
    parts = pattern.split(os.sep)
    label_index = None
    label_start = 0
    try:
        label_index = parts.index('{LABEL}')
        label_start = pattern.index('{LABEL}')
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
            yield i.filename[label_start:], i.filename, label


def yield_zipfile(zipfile, patterns, separator):
    infos = None
    gens = []
    for pattern in patterns:
        if pt.isfile(pattern):
            # pattern is csv-like (path, label) file
            gens.append(yield_file(pattern, '', separator))
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
            labels=(),
    ):
        self._args = (path, patterns, separator, convertfun,
                      include, exclude, labels)
        self._zipfile = zipfile.ZipFile(path)
        samples = list(yield_zipfile(self._zipfile, patterns, separator))
        samples = [{'key': s, 'label': l} for s, l in samples
                   if check_included(s, include, exclude)]
        ListReader.__init__(self, samples, labels, convertfun, self._load)

    def _load(self, s):
        return self._zipfile.read(s['key'])

    def __copy__(self):
        return ZipFileReader(*self._args)
