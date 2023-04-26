from datadings.reader import MsgpackReader
from datadings.reader.augment import QuasiShuffler

from .dataset import MSGPACK_PATH
from .common import missing_keys
from .common import correct_length
from .common import no_repetitions


def test_missing_keys():
    missing_keys(QuasiShuffler(MsgpackReader(MSGPACK_PATH)))


def test_length():
    correct_length(QuasiShuffler(MsgpackReader(MSGPACK_PATH)))


def test_length_empty():
    r = QuasiShuffler(MsgpackReader(MSGPACK_PATH))
    for i in range(0, len(r), 809):
        correct_length(r, start=i, stop=i)


def test_length_start():
    r = QuasiShuffler(MsgpackReader(MSGPACK_PATH))
    for i in range(0, len(r) // 2, 809):
        correct_length(r, start=i)


def test_length_stop():
    r = QuasiShuffler(MsgpackReader(MSGPACK_PATH))
    for i in range(len(r) // 2 + 1, len(r), 809):
        correct_length(r, stop=i)


def test_length_stop_negative():
    r = QuasiShuffler(MsgpackReader(MSGPACK_PATH))
    for i in range(0, len(r) // 2, 809):
        correct_length(r, stop=-i)


def test_length_start_stop():
    r = QuasiShuffler(MsgpackReader(MSGPACK_PATH))
    for i in range(0, len(r) // 2, 809):
        correct_length(r, start=i, stop=-i)


def test_no_repetitions():
    no_repetitions(QuasiShuffler(MsgpackReader(MSGPACK_PATH)))
