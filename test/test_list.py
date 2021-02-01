import random

from datadings.reader import ListReader


def floatrange(start, stop=None, step=None):
    a = 0 if stop is None else start
    b = start if stop is None else stop
    step = step or 1
    print(a, b, step)
    delta = b - a
    steps = int(delta / step)
    for x in range(steps):
        yield delta * x / steps + a


def test_missing_keys():
    count = 0
    samples = []
    map = {}
    for data in floatrange(10, 20, 0.1):
        sample = {"data": data, "key": count, "label": random.random()}
        samples.append(sample)
        map[count] = sample
        count = count + 1
    reader = ListReader(samples)
    print(reader)
    with reader:
        for test in reader:
            map.pop(test["key"])
    assert len(map) == 0


def test_return_to_front():
    """
    Readers should return to first element after iteration.
    """
    count = 0
    samples = []
    for data in floatrange(10, 20, 0.1):
        sample = {"data": data, "key": count, "label": random.random()}
        samples.append(sample)
        count = count + 1
    reader = ListReader(samples)
    print(reader)
    with reader:
        first = None
        for sample in reader:
            if first is None:
                first = sample
        for sample in reader:
            assert sample == first, (first, sample)
            break


def test_seek_key():
    count = 0
    samples = []
    map = {}
    for data in floatrange(10, 20, 0.1):
        sample = {"data": data, "key": count, "label": random.random()}
        samples.append(sample)
        map[count] = sample
        count = count + 1
    reader = ListReader(samples)
    print(reader)
    start = reader.find_index(10)
    with reader:
        for test in reader.iter(start=start):
            map.pop(test["key"])
    assert len(map) == 10  # because the reader is ordered


def test_seek_index():
    count = 0
    samples = []
    map = {}
    for data in floatrange(10, 20, 0.1):
        sample = {"data": data, "key": count, "label": random.random()}
        samples.append(sample)
        map[count] = sample
        count = count + 1
    reader = ListReader(samples)
    print(reader)
    with reader:
        for test in reader.iter(start=10):
            map.pop(test["key"])
    assert len(map) == 10
