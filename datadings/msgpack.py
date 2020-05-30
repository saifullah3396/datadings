from functools import partial

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


make_packer = partial(__msgpack.Packer, **pack_kwargs)


make_unpacker = partial(__msgpack.Unpacker, **unpack_kwargs)


pack = partial(__msgpack.pack, **pack_kwargs)


packb = partial(__msgpack.packb, **pack_kwargs)


unpack = partial(__msgpack.unpack, **unpack_kwargs)


unpackb = partial(__msgpack.unpackb, **unpack_kwargs)
