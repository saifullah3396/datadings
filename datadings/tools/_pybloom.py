from struct import unpack
from hashlib import blake2s


__all__ = ('BloomFilter',)


class BloomFilterBase(bytearray):
    def __init__(self, num_bits, num_hashes, num_bytes, data):
        self.num_bits = num_bits
        self.num_hashes = num_hashes
        super().__init__(num_bytes)
        if data is not None:
            if len(data) != num_bytes:
                raise ValueError('data must have same length as filter')
            self.clear()
            self.extend(data)

    def __iadd__(self, key):
        b = self.num_bits
        h1, h2 = unpack('>QQ', blake2s(key.encode('utf-8'), digest_size=16).digest())
        for k in range(self.num_hashes):
            # simulate uint64 value range:
            # logical AND with max uint64 == 2**64-1
            index = (h1 + k * h2 & 18446744073709551615) % b
            x = index >> 3
            y = 1 << (index & 7)
            self[x] |= y
        return self

    def __contains__(self, key):
        b = self.num_bits
        h1, h2 = unpack('>QQ', blake2s(key.encode('utf-8'), digest_size=16).digest())
        for k in range(self.num_hashes):
            # simulate uint64 value range:
            # logical AND with max uint64 == 2**64-1
            index = (h1 + k * h2 & 18446744073709551615) % b
            x = index >> 3
            y = 1 << (index & 7)
            if not self[x] & y:
                return False
        return True
