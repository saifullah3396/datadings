from math import ceil
from math import log

try:
    from ._cbloom import BloomFilterBase
except ImportError:
    from ._pybloom import BloomFilterBase

from ..msgpack import pack as pack_msgpack
from ..msgpack import unpack as unpack_msgpack


class BloomFilter(BloomFilterBase):
    def __init__(self, num_elements, false_positive_prob=None, data=None):
        if false_positive_prob is None:
            false_positive_prob = 1.0 / num_elements
        if not 0 < false_positive_prob < 1:
            raise ValueError('false_positive_prob must be in (0, 1)')

        self.false_positive_prob = false_positive_prob
        self.num_elements = num_elements

        ln2 = 0.6931471805599453
        num_bits = num_elements * log(false_positive_prob) / -0.4804530139182015
        num_bits = int(ceil(num_bits / 8) * 8)
        num_hashes = int(round(num_bits / num_elements * ln2))
        num_bytes = (num_bits >> 3) + (num_bits & 0b111 > 0)
        super().__init__(num_bits, num_hashes, num_bytes, data)

    @classmethod
    def load(cls, fp):
        spec = unpack_msgpack(fp)
        return cls(**spec)

    def dump(self, fp):
        pack_msgpack({
            'num_elements': self.num_elements,
            'false_positive_prob': self.false_positive_prob,
            'data': memoryview(self)
        }, fp)
