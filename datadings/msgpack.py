"""
Compatibility functions that wrap msgpack to seamlessly support
both version 1.0.0 and earlier versions.
Encoding is always UTF-8 and bin type is enabled and
``strict_map_key=False``.

All helpers are setup to use ``msgpack_numpy`` for transparent
packing and unpacking of numpy arrays enabled by default.
"""

from functools import partial as __partial

import msgpack as __msgpack
from msgpack_numpy import encode as __encode
from msgpack_numpy import decode as __decode


# check if msgpack version 1.0.0 or newer is installed
__IS_100 = False
try:
    __IS_100 = __msgpack.version >= (1, 0, 0)
except AttributeError:
    pass


# msgpack version 1.0.0
if __IS_100:
    pack_kwargs = dict(
        default=__encode
    )
    unpack_kwargs = dict(
        strict_map_key=False,
        object_hook=__decode
    )
# legacy msgpack
else:
    pack_kwargs = dict(
        use_bin_type=True,
        encoding='utf-8',
        default=__encode
    )
    unpack_kwargs = dict(
        encoding='utf-8',
        object_hook=__decode
    )


make_packer = __partial(__msgpack.Packer, **pack_kwargs)
"""
Create a packer with default arguments.
"""


make_unpacker = __partial(__msgpack.Unpacker, **unpack_kwargs)
"""
Create a unpacker with default arguments.
"""


pack = __partial(__msgpack.pack, **pack_kwargs)
"""
Pack object to stream.
"""


packb = __partial(__msgpack.packb, **pack_kwargs)
"""
Pack object to bytes.
"""


unpack = __partial(__msgpack.unpack, **unpack_kwargs)
"""
Unpack object from stream.
"""


unpackb = __partial(__msgpack.unpackb, **unpack_kwargs)
"""
Unpack object from bytes.
"""
