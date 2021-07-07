Creating a custom dataset
=========================

Follow this guide if the dataset you want to use is not yet part
of datadings.
If the data is publicly available, please consider
:ref:`contributing<contributing-dataset>`
it to datadings.



A basic example
---------------

Typically the process of converting individual samples into the
datadings format is divided into locating/loading/pre-processing
samples and writing them to the dataset file.
Here's a ready-to-run example that illustrates this::

    import random
    from datadings.writer import FileWriter


    def generate_samples():
        for i in range(1000):
            data = i.to_bytes(10000, 'big')
            label = random.randrange(10)
            yield {'key': str(i), 'data': data, 'label': label}


    def main():
        with FileWriter('dummy.msgpack') as writer:
            for sample in generate_samples():
                writer.write(sample)

The :py:class:`FileWriter <datadings.writer.FileWriter>` should
be used as a context manager to ensure that it is closed properly.
Its :py:meth:`write <datadings.writer.FileWriter.write>` method
accepts samples as dictionaries with a unique string ``key``.



Converting directory trees
--------------------------

Apart from the featured
:py:class:`MsgpackReader <datadings.reader.msgpack.MsgpackReader>`
datadings also provides the
:py:class:`DirectoryReader <datadings.reader.directory.DirectoryReader>`
class to read samples from directory trees.
Let's assume your dataset is currently stored in a directory tree
like this::

    yourdataset / a / a1
                    / a2
                / b / b3
                    / b4

You can now simply replace the ``generate_samples`` function above
with a
:py:class:`DirectoryReader <datadings.reader.directory.DirectoryReader>`::

    def main():
        with FileWriter('yourdataset.msgpack') as writer:
            for sample in DirectoryReader('yourdataset/{LABEL}/**'):
                writer.write(sample)

The names of the directories at the level marked by ``{LABEL}`` are
used as ``label``, the path to the file from the label onwards is
used as the ``key``, and the file contents are loaded into ``data``::

    {'key': 'a/a1', 'label': 0, 'path': 'yourdataset/a/a1',
     '_additional_info': [], '_label': 'a', 'data': b'content of a1'}
    {'key': 'a/a2', 'label': 0, 'path': 'yourdataset/a/a2',
     '_additional_info': [], '_label': 'a', 'data': b'content of a2'}
    {'key': 'b/b1', 'label': 1, 'path': 'yourdataset/b/b1',
     '_additional_info': [], '_label': 'b', 'data': b'content of b1'}
    {'key': 'b/b2', 'label': 1, 'path': 'yourdataset/b/b2',
     '_additional_info': [], '_label': 'b', 'data': b'content of b2'}

You can now make any additional changes to the samples before handing
them off to the writer.
Check the
:py:class:`reference <datadings.reader.directory.DirectoryReader>`
for more details on how you can influence its behavior.

If your dataset is not a directory tree, but stored in a ZIP file
you can use the
:py:class:`ZipFileReader <datadings.reader.zipfile.ZipFileReader>`
instead.



More complex datasets
---------------------

If your dataset consists of multiple files per sample, needs
additional metadata, or it is stored in an unusual way
(like a single large TAR file that you don't want to extract),
you will need to write additional code to provide the samples.
You can take a look at the source code of the
:py:mod:`included datasets <datadings.sets>`
like :py:mod:`MIT1003 <datadings.sets.MIT1003_write>`
for pointers.
