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

* ``MIT1003.msgpack`` contains sample data
* ``MIT1003.msgpack.index`` contains index for random access
* ``MIT1003.msgpack.md5`` contains MD5 hashes of both files

Reading all samples sequentially,
using a ``MsgpackReader`` as a context manager::

    from datadings.reader import MsgpackReader
    with MsgpackReader('MIT1003.msgpack') as reader:
        for sample in reader:
            # do dataset things!

This standard iterator returns dictionaries.
Use the ``rawiter()`` method to get samples as messagepack encoded
bytes instead.

Reading specific samples::

    reader.seek_key('i14020903.jpeg')
    print(reader.next()['key'])
    reader.seek_index(100)
    print(reader.next()['key'])

Reading samples as raw msgpacked bytes::

    raw = reader.rawnext()
    for raw in reader.rawiter():
        print(type(raw), len(raw))

Number of samples::

    print(len(reader))

You can also change the order and selection of iterated samples
with :py:mod:`Augments <datadings.reader.augment>`.
For example, to randomize the order of samples, wrap the reader
in a :py:class:`Shuffler <datadings.reader.augment.Shuffler>`::

    with Shuffler(MsgpackReader('MIT1003.msgpack')) as reader:
        for sample in reader:
            # do dataset things, but in random order!

A common use case is to iterate over the whole dataset multiple times.
This can be done with the
:py:class:`Cycler <datadings.reader.augment.Cycler>`::

    with Cycler(MsgpackReader('MIT1003.msgpack')) as reader:
        for sample in reader:
            # do dataset things, but FOREVER!
