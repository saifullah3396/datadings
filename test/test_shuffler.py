from datadings.reader import MsgpackReader
from datadings.reader.augment import Shuffler

from .dataset import MSGPACK_PATH
from .common import missing_keys
from .common import correct_length
from .common import no_repetitions


def make_reader():
    return Shuffler(MsgpackReader(MSGPACK_PATH))


def test_missing_keys():
    missing_keys(make_reader())


def test_length():
    correct_length(make_reader())


def test_length_empty():
    r = make_reader()
    for i in range(0, len(r), 809):
        correct_length(r, start=i, stop=i)


def test_length_start():
    r = make_reader()
    for i in range(0, len(r) // 2, 809):
        correct_length(r, start=i)


def test_length_stop():
    r = make_reader()
    for i in range(len(r) // 2 + 1, len(r), 809):
        correct_length(r, stop=i)


def test_length_stop_negative():
    r = make_reader()
    for i in range(0, len(r) // 2, 809):
        correct_length(r, stop=-i)


def test_length_start_stop():
    r = make_reader()
    for i in range(0, len(r) // 2, 809):
        correct_length(r, start=i, stop=-i)


def test_repetitions():
    no_repetitions(make_reader())
