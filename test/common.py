import random

from .dataset import KEYS
from .dataset import make_key


def missing_keys(reader):
    """
    Check if a reader returns all expected keys
    """
    keys = set(KEYS)
    with reader:
        for sample in reader:
            keys.remove(sample["key"])
    assert not keys, keys


def return_after_iter(reader):
    """
    Readers should return to first element after iteration.
    """
    with reader:
        first = None
        for sample in reader:
            if first is None:
                first = sample
        for sample in reader:
            assert sample == first, (first, sample)
            break


def seek_index(reader):
    index = list(range(len(reader)))
    random.shuffle(index)
    with reader:
        for i in index:
            sample = reader.get(i)
            key = make_key(i)
            assert key == sample['key'], (key, sample['key'])


def seek_key(reader):
    keys = list(KEYS)
    random.shuffle(keys)
    with reader:
        for key in keys:
            sample = reader.get(reader.find_index(key))
            assert key == sample['key'], (key, sample['key'])


def find_index(reader):
    index = list(range(len(reader)))
    random.shuffle(index)
    with reader:
        for i in index:
            key = make_key(i)
            j = reader.find_index(key)
            assert i == j, (i, j)


def find_key(reader):
    keys = list(KEYS)
    random.shuffle(keys)
    with reader:
        for key in keys:
            index = reader.find_index(key)
            found = reader.get(index)['key']
            assert key == found, (key, found)


def iter_start(reader):
    keys = list(KEYS)
    start = random.randrange(len(keys))
    with reader:
        for key, sample in zip(keys[start:], reader.iter(start=start)):
            assert key == sample['key'], (key, sample['key'])


def iter_stop(reader):
    keys = list(KEYS)
    stop = random.randrange(len(keys))
    with reader:
        for key, sample in zip(keys[:stop], reader.iter(start=0, stop=stop)):
            assert key == sample['key'], (key, sample['key'])


def iter_range(reader):
    keys = list(KEYS)
    while True:
        start = random.randrange(len(keys))
        stop = random.randrange(len(keys))
        if start < stop:
            break
    with reader:
        for key, sample in zip(keys[start:stop], reader.iter(start=start, stop=stop)):
            assert key == sample['key'], (key, sample['key'])
