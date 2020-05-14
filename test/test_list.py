import os
import os.path as pt
import sys

ROOT = pt.dirname(__file__)
parent = pt.abspath(pt.join(ROOT, os.pardir))

for p in (os.pardir, parent):
    try:
        sys.path.remove(p)
    except ValueError:
        pass
print(sys.path)

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
        yield delta * x/steps + a


def test_checkAllKeys():
    count = 0
    samples = []
    map = {}
    for data in floatrange(10, 20, 0.1):
        sample = {"data": data, "key": count, "label": random.random()}
        samples.append(sample)
        map[count] = sample
        count = count +1
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
        count = count +1
    reader = ListReader(samples)
    print(reader)
    with reader:
        for test in reader:
            print (test)
        for test in reader:
            print("this should never be reached")
            assert False


def test_multipleIterations():
    count = 0
    samples = []
    for data in floatrange(10, 20, 0.1):
        sample = {"data": data, "key": count, "label": random.random()}
        samples.append(sample)
        count = count +1
    reader = ListReader(samples)
    print(reader)
    reached1 = False
    reached2= False
    with reader:
        for test in reader:
            reached1 = True
            print (test)
    reader.seek_index(0)
    with reader:
        for test in reader:
            reached2 = True
            print (test)
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
    reader.seek_key(10)
    with reader:
        for test in reader:
            map.pop(test["key"])
    assert len(map) == 10 #because the reader is ordered


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
    reader.seek_index(10)
    with reader:
        for test in reader:
            map.pop(test["key"])
    assert len(map) == 10
