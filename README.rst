Wat?
====

datadings is a collection of tools to prepare public datasets
for machine learning, based on simple principles.

    Datasets are collections of individual data samples.
    A sample is a dictionary with descriptive keys.

E.g., for supervised training each sample is a tuple
``{'image': imagedata, 'label': label)``.
More values (meta-data) may be added though.

messagepack is used as an efficient binary serialization format
for most included datasets.
Its specification allows us to simply write data sample
to a flat file and read them sequentially afterwards.
It is schema-less, so we don't need to worry about extensions
if a new dataset does not fit our previous definitions.

For random access, an index of positions is added.

See http://msgpack.org/ for more information.





Sample Types, Keys, and Their Meanings
--------------------------------------

This section gives an overview of available types of data samples
and the respective keys they contain.

**WIP**





Command Line Tools
------------------

* *datadings-write*
  creates new dataset files
* *datadings_merge*
  merges two or more dataset files
* *datadings-shuffle*
  shuffles an existing dataset file
* *datadings-show*
  displays the contents of a dataset file; **requires OpenCV**
* *datadings-bench*
  runs a benchmark to see how many samples/s can be read
  from a given dataset file





Usage
-----

Each dataset defines modules to read and write in the
``datadings.sets`` package.
Let's consider the *MIT1003* dataset as an example.

``MIT1003_write`` is an executable that creates dataset files.
It can be called directly or through *datadings-write*.

The `MIT1003` module imports ``datadings.reader.MsgpackReader``
as ``MIT1003Reader``.

Reading all samples sequentially,
using the ``Reader`` as a context manager::

    with MIT1003Reader('MIT1003.msgpack') as reader:
        for sample in reader:
            [do dataset things]

This standard iterator returns dictionaries.
Use the ``rawiter()`` method to get samples as messagepack encoded
bytes instead.

Reading specific samples::

    reader.seek_key('i14020903.jpeg')
    print(reader.next()['key'])
    reader.seek_index(100)
    print(reader.next()['key'])

Reading samples as raw bytes::

    raw = reader.rawnext()
    for raw in reader.rawiter():
        print(type(raw), len(raw))

Number of samples::

    print(len(reader))





Adding new Datasets
-------------------

To add a dataset called *FOO*,
add a new ``FOO_write`` module to the `datadings.sets` package.
Optionally, a ``FOO`` module can define custom sample classes and a
``FOOReader``.
A custom sample type should be called ``FOOData`` and must be a
subclass of dict.

For msgpack-based datasets ``MsgpackReader`` usually provides
all required functionality out of the box.
If a custom ``FOOReader`` is necessary it must be a subclass of
``datadings.reader.Reader``.
