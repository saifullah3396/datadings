from typing import Union
from typing import Sequence
from typing import Iterable
from typing import Callable

import os
import os.path as pt
import itertools as it
import glob
from fnmatch import fnmatch
from pathlib import Path

from .list import ListReader
from .list import noop


def check_included(filename, include, exclude):
    return (not include or any(fnmatch(filename, i) for i in include)) \
        and not any(fnmatch(filename, e) for e in exclude)


def yield_file(infile, prefix, separator):
    with open(infile) as f:
        for line in f:
            parts = line.strip('\n').split(separator)
            path = parts[0]
            try:
                label = parts[1]
            except IndexError:
                label = None
            additional_info = parts[2:]
            yield path.replace(prefix, ''), path, label, additional_info


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
    for p in glob.iglob(pattern, recursive=True):
        if pt.isfile(p):
            if label_index is not None:
                label = p.split(os.sep)[label_index]
            else:
                label = None
            yield p.replace(prefix, ''), p, label, []


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
    """
    Reader that loads samples from one or multiple filesystem directories.

    One or more search patterns must be given to tell the reader where to
    look for samples.
    Each search pattern can either be:

    - A glob pattern to a filesystem directory.
      Use the special ``{LABEL}`` string to define which directory
      in the path to use as a label.
    - A path to a CSV-like file (with the given ``separator`` string)
      where each line contains the path to a sample file.
      Paths can be relative and optionally prefixed with a ``root_dir``.
      A label as well as additional information can be included besides
      the path in additional columns.
      They will be stored as ``"label"`` and ``"_additional_info"``.

    Example glob pattern: ``some_dir/{LABEL}/**``

    This patterns loads a dataset with a typical directory tree structure
    where samples from each class are located in separate subdirectories.
    The name of the directory at the level of ``{LABEL}`` is used as the
    label.

    You can further narrow down which files to include with additional
    :py:func:`fnmatch.fnmatch` glob patterns.
    These are applied as follows:

    - If no inclusion patterns are given, all files are included.
    - If inclusion patterns are given, a file must match at least one.
    - A file is excluded if it matches any exclusion patterns.

    Note:
        Please refer to the
        :py:class:`ListReader <datadings.reader.list.ListReader>`
        documentation for a more detailed explanation on how labels are
        handled.

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
        root_dir: Prefix for relative paths.
    """
    def __init__(
            self,
            patterns: Sequence[Union[str, Path]],
            labels: Union[Iterable, Path] = None,
            numeric_labels=True,
            initfun: Callable = noop,
            convertfun: Callable = noop,
            include: Sequence[str] = (),
            exclude: Sequence[str] = (),
            separator='\t',
            root_dir='',
    ):
        # single patterns must be wrapped in tuple
        if isinstance(patterns, (str, Path)):
            patterns = patterns,
        samples = yield_directory(patterns, separator)
        samples = [
            {'key': k,
             'label': l,
             'path': pt.join(root_dir, p),
             '_additional_info': i}
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
        with open(sample['path'], 'rb') as f:
            data = f.read()
        self.bytes_read += len(data)
        sample['data'] = data
        # apply custom convert function, if any
        self._cust_convertfun(sample)
