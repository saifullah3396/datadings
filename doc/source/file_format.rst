.. _file-format:

The datadings file format
=========================

The file format datadings uses is simple.
A dataset is made up of three files:

    - ``.msgpack`` main data file
    - ``.msgpack.index`` index file
    - ``.msgpack.md5`` for integrity checks



Data file
---------

Each sample is a key-value
`map <https://github.com/msgpack/msgpack/blob/master/spec.md#map-format-family>`_
with a ``key`` that is unique
for the dataset.
In Python notation::

    {"key": <unique key>, ... }

Each sample is represented by one `msgpack <http://msgpack.org>`_
message.
The main dataset file has the extension ``.msgpack`` and contains
a sequence of these messages::

    <sample 1><sample 2><sample 3> ...

Note that no additional data is stored in this file.
The msgpack format does not require the length of the message to
be known for unpacking, so this single file is sufficient for
sequential access.



Arrays & complex numbers
^^^^^^^^^^^^^^^^^^^^^^^^

msgpack on its own does not support densely packed arrays or complex
numbers.
While it may be sufficient to use lists for heterogeneous data types
or few values, datadings uses
`msgpack-numpy <https://github.com/lebedov/msgpack-numpy>`_
to support storing arbitrary numpy arrays efficiently.
This introduces a limitation on the keys that can be present in samples.



Reserved keys
^^^^^^^^^^^^^

The following keys are reserved by datadings for internal use and thus
cannot be used in samples:

    - ``"key"``: used to uniquely identify samples in a dataset
    - ``"nd"``: used by msgpack-numpy for array decoding
    - ``"complex"``: used by msgpack-numpy for complex number decoding

Using these keys results in undefined behavior.



Index file
----------

To enable random access, an index file with the ``.msgpack.index``
extension is added.
The index is a map of key-offset pairs.
In Python notation::

    {"sample 1": 0, "sample 2": 1234, ... }

For every ``key`` in the dataset it gives the offset in bytes of
the respective sample from the beginning of the file.
Index entries are stored with offsets in ascending order.



MD5 file
--------

Finally, every dataset comes with a ``.msgpack.md5`` file with hashes
for the data and index files, so their integrity can be verified.



Limitations
===========

Since msgpack is used datadings inherits its limitations.

    - Maps and lists cannot have more than 2\ :sup:`32`\-1  entries.
    - Strings and binary data cannot be longer than 2\ :sup:`32`\-1  bytes.
    - Integers (signed or unsinged) are limited to 64 bits.
    - Floats are limited to single or double precision.

This means each dataset is limited to less than 2\ :sup:`32`\  samples
(since the index uses a map) and around 2\ :sup:`64`\  bytes total
file size (the largest possible byte offset is 2\ :sup:`64`\-1).
The same applies to each individual sample regarding the number of
keys present and its packed size.
