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


def test_repetitions():
    no_repetitions(QuasiShuffler(MsgpackReader(MSGPACK_PATH)))
