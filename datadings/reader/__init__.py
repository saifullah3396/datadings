from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

from .directory import DirectoryReader
from .list import ListReader
from .msgpack import MsgpackReader
from .reader import Reader
from .zipfile import ZipFileReader
from .augment import Cycler
from .augment import Shuffler

IdentityReader = MsgpackReader
