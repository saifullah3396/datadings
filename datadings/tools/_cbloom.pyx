# Cython imports
from libc.stdint cimport *
from libc.string cimport memset
from cpython.mem cimport PyMem_Malloc
from cpython.mem cimport PyMem_Free
from cpython.bytes cimport PyBytes_FromStringAndSize
from cpython cimport Py_buffer, PyObject_CopyData

# Python imports
from hashlib import blake2s

import cython


cdef extern from "_bswap.h":
    uint64_t ntoh64(const uint64_t)


cdef class BloomFilterBase:
    cdef uint64_t num_bytes
    cdef uint64_t num_bits
    cdef int num_hashes
    cdef uint8_t* data

    def __init__(self, num_bits, num_hashes, num_bytes, data):
        self.num_bits = num_bits
        self.num_hashes = num_hashes
        self.num_bytes = num_bytes
        self.data = <uint8_t*> PyMem_Malloc(self.num_bytes)
        if not self.data:
            raise MemoryError()
        if data is None:
            memset(self.data, 0, self.num_bytes)
        else:
            PyObject_CopyData(self, data)

    def __dealloc__(self):
        PyMem_Free(self.data)

    def __getbuffer__(self, Py_buffer *buffer, int flags):
        buffer.buf = self.data
        buffer.internal = NULL
        buffer.itemsize = 1
        buffer.len = self.num_bytes
        buffer.obj = self
        buffer.ndim = 1
        buffer.readonly = 0
        buffer.shape = NULL
        buffer.strides = NULL
        buffer.suboffsets = NULL

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.nonecheck(False)
    @cython.cdivision(True)
    def __iadd__(self, key):
        f = self.data
        cdef uint64_t b = self.num_bits
        cdef uint64_t B = self.num_bytes
        hashes = blake2s(key.encode('utf-8'), digest_size=16).digest()
        cdef const uint8_t[:] hashp = hashes
        cdef const uint64_t* hashp2 = <uint64_t*> &hashp[0]
        cdef uint64_t h1 = ntoh64(hashp2[0])
        cdef uint64_t h2 = ntoh64(hashp2[1])
        cdef uint64_t index, x
        cdef uint8_t y
        cdef int k
        for k in range(self.num_hashes):
            index = (h1 + k * h2) % b
            x = index >> 3
            if x >= B:
                raise IndexError('index out of range')
            y = 1 << (index & 0b111)
            f[x] |= y
        return self

    @cython.boundscheck(False)
    @cython.wraparound(False)
    @cython.nonecheck(False)
    @cython.cdivision(True)
    def __contains__(self, key):
        f = self.data
        cdef uint64_t b = self.num_bits
        cdef uint64_t B = self.num_bytes
        hashes = blake2s(key.encode('utf-8'), digest_size=16).digest()
        cdef const uint8_t[:] hashp = hashes
        cdef const uint64_t* hashp2 = <uint64_t*> &hashp[0]
        cdef uint64_t h1 = ntoh64(hashp2[0])
        cdef uint64_t h2 = ntoh64(hashp2[1])
        cdef uint64_t index, x
        cdef uint8_t y
        cdef uint64_t k
        for k in range(self.num_hashes):
            index = (h1 + k * h2) % b
            x = index >> 3
            if x >= B:
                raise IndexError('index out of range')
            y = 1 << (index & 0b111)
            if f[x] & y <= 0:
                return False
        return True
