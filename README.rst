Wat?
====

datadings is a collection of tools to prepare public datasets
for machine learning, based on simple principles.

    Datasets are collections of individual data samples.
    A sample is a tuple.

E.g., for supervised training each sample is a tuple
``(sample, groundtruth)``.
More values (meta-data) may be added though.

messagepack is used as an efficient binary serialization format.
Its specification allows us to simply write data sample
to a flat file and read them sequentially afterwards.
It is schema-less, so we don't need to worry about extensions
if a new dataset does not fit our previous definitions.

For random access, an index of positions is added.

See http://msgpack.org/ for more information.





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

The `MIT1003` module defines the ``convert_mit1003`` function
and the ``MIT1003Reader`` class.

``convert_mit1003`` converts a sample as unpacked from the dataset
file and converts it to the type appropriate for the dataset.

A ``MIT1003Reader`` can be used to access the data.
It is iterable and has methods to seek.

Reading all samples sequentially,
using the ``Reader`` as a context manager::

    with MIT1003Reader('MIT1003.msgpack') as reader:
        for sample in reader:
            [do dataset things]


Reading specific samples::

    reader.seek_key('i14020903.jpeg')
    print(reader.next().filename)
    reader.seek_index(100)
    print(reader.next().filename)

Reading samples as raw bytes::

    raw = reader.rawnext()
    for raw in reader.rawiter():
        print(type(raw), len(raw))

Number of samples::

    print(len(reader))





Adding new Datasets
-------------------

To add a dataset called *FOO*,
you have to add two modules to the `datadings.sets` package:
``FOO`` and ``FOO_write``.

``FOO`` must define, as a minimum,
a ``convert_foo`` function and a class ``FOOReader``.
Optionally, you can define your own sample type, ``FOOData``
(usually a namedtuple).

``convert_foo`` takes an unpacked sample as loaded from file and
converts it to the appropriate type::

    def convert_foo(sample):
        return FOOData(sample)

The ``FOOReader`` must be a subclass of ``datadings.reader.Reader``.
We can reuse ``convert_foo``::

    class FOOReader(Reader):
        _convert = staticmethod(convert_foo)

