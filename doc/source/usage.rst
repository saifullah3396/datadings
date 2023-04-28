Usage
=====

Each dataset defines modules to read and write in the
``datadings.sets`` package.
For most datasets the reading module only contains additional
metadata like class labels and distributions.

Let's consider the *MIT1003* dataset as an example.

``MIT1003_write`` is an executable that creates dataset files.
It can be called directly ``python -m datadings.sets.MIT1003_write``
or through
:py:mod:`datadings-write <datadings.commands.write>`.
Three files will be written:

- ``MIT1003.msgpack`` contains sample data
- ``MIT1003.msgpack.index`` contains index for random access
- ``MIT1003.msgpack.md5`` contains MD5 hashes of both files

Reading all samples sequentially,
using a ``MsgpackReader`` as a context manager::

    from datadings.reader import MsgpackReader
    with MsgpackReader('MIT1003.msgpack') as reader:
        for sample in reader:
            # do dataset things!

This standard iterator returns dictionaries.
Use ``reader.iter(raw=True)`` to get samples as messagepack encoded
bytes instead.

Reading specific samples::

    i = reader.find_index('i14020903.jpeg')
    print(reader[i]['key'])
    print(reader.get(i)['key'])

Reading samples as raw bytes::

    raw = reader.get(100, raw=True)
    for raw in reader.iter(raw=True):
        print(type(raw), len(raw))

Number of samples::

    print(len(reader))

You can also change the order and selection of iterated samples
with :py:mod:`Augments <datadings.reader.augment>`.
For example, to randomize the order of samples, wrap the reader
in a :py:class:`Shuffler <datadings.reader.augment.Shuffler>`::

    from datadings.reader import Shuffler
    with Shuffler(MsgpackReader('MIT1003.msgpack')) as reader:
        for sample in reader:
            # do dataset things, but in random order!

Alternatively the
:py:class:`QuasiShuffler <datadings.reader.augment.QuasiShuffler>`
offers slightly less random, but much faster iteration.
It keeps a buffer of samples and reads random chunks instead of
single samples.
Randomness increases with bigger buffers.

A common use case is to iterate over the whole dataset multiple times.
This can be done with the
:py:class:`Cycler <datadings.reader.augment.Cycler>`::

    from datadings.reader import Cycler
    with Cycler(MsgpackReader('MIT1003.msgpack')) as reader:
        for sample in reader:
            # do dataset things, but FOREVER!
