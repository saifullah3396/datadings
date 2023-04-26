from collections import Counter

from datadings.reader import MsgpackReader
from datadings.reader.augment import Repeater

from .dataset import KEYS
from .dataset import MSGPACK_PATH
from .common import missing_keys
from .common import return_after_iter
from .common import seek_index
from .common import seek_key
from .common import find_index
from .common import find_key
from .common import iter_start
from .common import iter_stop
from .common import iter_range


def make_reader(times=5):
    return Repeater(MsgpackReader(MSGPACK_PATH), times)


def test_missing_keys():
    missing_keys(make_reader())


def test_return_after_iter():
    return_after_iter(make_reader())


def test_seek_index():
    r = make_reader()
    seek_index(r, length=len(r) // r.times)


def test_seek_key():
    seek_key(make_reader())


def test_find_index():
    r = make_reader()
    find_index(r, length=len(r) // r.times)


def test_find_key():
    find_key(make_reader())


def test_iter_start():
    iter_start(make_reader())


def test_iter_stop():
    iter_stop(make_reader())


def test_iter_range():
    iter_range(make_reader())


def test_iter_repeat():
    # check that each key is repeated <times> times
    times = 5
    keys = set(KEYS)
    with make_reader(times=times) as r:
        count = Counter(sample['key'] for sample in r)
    assert all(c == times for c in count.values())
    assert not keys - set(count)


def test_iter_repeat_range():
    # start iterating in the middle of the reader and
    # stop such that each key is repeated <times - 1> times
    keys = set(KEYS)
    times = 5
    with make_reader(times=times) as r:
        n = len(r) // times
        i = n // 2
        count = Counter(sample['key'] for sample in r.iter(start=i, stop=-(n-i)))
    assert all(c == times - 1 for c in count.values())
    assert not keys - set(count)
