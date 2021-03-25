from datadings.reader import ListReader

from .dataset import SAMPLES
from .common import missing_keys
from .common import return_after_iter
from .common import seek_index
from .common import seek_key
from .common import find_index
from .common import find_key
from .common import iter_start
from .common import iter_stop
from .common import iter_range


def test_missing_keys():
    missing_keys(ListReader(SAMPLES))


def test_return_after_iter():
    return_after_iter(ListReader(SAMPLES))


def test_seek_key():
    seek_key(ListReader(SAMPLES))


def test_seek_index():
    seek_index(ListReader(SAMPLES))


def test_find_key():
    find_key(ListReader(SAMPLES))


def test_find_index():
    find_index(ListReader(SAMPLES))


def test_iter_start():
    iter_start(ListReader(SAMPLES))


def test_iter_stop():
    iter_stop(ListReader(SAMPLES))


def test_iter_range():
    iter_range(ListReader(SAMPLES))
