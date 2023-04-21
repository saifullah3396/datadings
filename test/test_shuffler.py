from datadings.reader import MsgpackReader
from datadings.reader.augment import Shuffler

from .dataset import MSGPACK_PATH
from .common import missing_keys
from .common import correct_length
from .common import no_repetitions


def test_missing_keys():
    missing_keys(Shuffler(MsgpackReader(MSGPACK_PATH)))


def test_length():
    correct_length(Shuffler(MsgpackReader(MSGPACK_PATH)))


def test_repetitions():
    no_repetitions(Shuffler(MsgpackReader(MSGPACK_PATH)))
