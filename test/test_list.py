import os
import os.path as pt
import sys
import random

from datadings.reader import ListReader

ROOT = pt.dirname(__file__)
parent = pt.abspath(pt.join(ROOT, os.pardir))

for p in (os.pardir, parent):
    try:
        sys.path.remove(p)
    except ValueError:
        pass
print(sys.path)


def floatrange(start, stop=None, step=None):
    a = 0 if stop is None else start
    b = start if stop is None else stop
    step = step or 1
    print(a, b, step)
    delta = b - a
    steps = int(delta / step)
    for x in range(steps):
        yield delta * x / steps + a


def test_checkAllKeys():
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


def test_checkEndOfIteration():
    count = 0
    samples = []
    for data in floatrange(10, 20, 0.1):
        sample = {"data": data, "key": count, "label": random.random()}
        samples.append(sample)
        count = count + 1
    reader = ListReader(samples)
    print(reader)
    with reader:
        for test in reader:
            print(test)
        for test in reader:
            print("this should be reached")
            assert True


def test_multipleIterations():
    count = 0
    samples = []
    for data in floatrange(10, 20, 0.1):
        sample = {"data": data, "key": count, "label": random.random()}
        samples.append(sample)
        count = count + 1
    reader = ListReader(samples)
    print(reader)
    reached1 = False
    reached2 = False
    with reader:
        for test in reader:
            reached1 = True
            print(test)
        for test in reader:
            reached2 = True
            print(test)
    assert reached1 and reached2


def test_seek_keys():
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
