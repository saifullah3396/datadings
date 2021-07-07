from typing import Union
from typing import Sequence
from typing import Callable

import os
import os.path as pt
import itertools as it
import zipfile
from fnmatch import fnmatch
from pathlib import Path

from .list import ListReader
from .list import noop
from .directory import check_included
from .directory import yield_file


def glob_pattern(infos, pattern):
    parts = pattern.split('/')
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
        if fnmatch(i.filename, pattern):
            if label_index is not None:
                label = i.filename.split('/')[label_index]
            else:
                label = None
            yield i.filename[label_start:], i.filename, label, []


def yield_zipfile(zipfile_, patterns, separator):
    infos = None
    gens = []
    for pattern in patterns:
        if pt.isfile(pattern):
            # pattern is csv-like (path, label) file
            gens.append(yield_file(pattern, '', separator))
        else:
            if infos is None:
                infos = zipfile_.infolist()
            # pattern is glob-pattern
            gens.append(glob_pattern(infos, pattern))
    return it.chain(*gens)


class ZipFileReader(ListReader):
    """
    Reader that reads files from a ZIP file.

    Note:
        Functionally identical to the
        :py:class:`DirectoryReader <datadings.reader.list.DirectoryReader>`,
        expect it reads from ZIP files instead of filesystem directories.
        Please refer to its documentation for more detailed explanations.

    Parameters:
        patterns: One or more search patterns.
        labels: Optional. List of labels in desired order,
                or path to file with one label per line.
                If ``None``, get ``"label"`` keys from samples, if any,
                and sort.
        numeric_labels: If true, convert labels to numeric index to list
                        of all labels.
        initfun: Callable ``initfun(sample: dict)`` to modify samples
                 in-place during initialization.
        convertfun: Callable ``convertfun(sample: dict)`` to modify samples
                    in-place before they are returned.
        include: Set of inclusion patterns.
        exclude: Set of exclusion patterns.
        separator: Separator string for file patterns.
    """
    def __init__(
            self,
            path: Union[str, Path],
            patterns: Sequence[Union[str, Path]] = '{LABEL}/**',
            labels=None,
            numeric_labels=True,
            initfun: Callable = noop,
            convertfun: Callable = noop,
            include=(),
            exclude=(),
            separator='\t',
    ):
        self._path = str(path)
        # single patterns must be wrapped in tuple
        if isinstance(patterns, (str, Path)):
            patterns = patterns,
        self._args = (
            path,
            patterns,
            labels,
            numeric_labels,
            initfun,
            separator,
            include,
            exclude,
        )
        self._zipfile = zipfile.ZipFile(path)
        samples = yield_zipfile(self._zipfile, patterns, separator)
        samples = [
            {'key': k, 'label': l, 'path': p, '_additional_info': i}
            for k, p, l, i in samples
            if check_included(p, include, exclude)
        ]
        ListReader.__init__(
            self,
            samples,
            labels=labels,
            numeric_labels=numeric_labels,
            initfun=initfun,
            convertfun=self._load_binary,
        )
        self._cust_convertfun = convertfun
        self.bytes_read = 0

    def _load_binary(self, sample):
        data = self._zipfile.read(sample['path'])
        self.bytes_read += len(data)
        sample['data'] = data
        # apply custom convert function, if any
        self._cust_convertfun(sample)

    def __copy__(self):
        return ZipFileReader(*self._args)
