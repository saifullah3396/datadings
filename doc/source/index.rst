datadings' documentation
========================

datadings is a collection of tools to prepare datasets for machine
learning, based on two simple principles:

    Datasets are collections of individual data samples.

    Each sample is a dictionary with descriptive keys.

For supervised training with images samples are dictionaries like this::

    {"key": unique_key, "image": imagedata, "label": label}



Mission statement
=================

Dealing with different datasets can be tedious for machine learning
practitioners.
Two datasets almost never share the same directory structure and often
custom file formats are used.
How datadings fits into the picture is best explained by
`XKCD #927 <https://xkcd.com/927/>`_:

.. image:: _static/xkcd927.png
    :alt: XKCD #927
    :width: 500
    :target: https://xkcd.com/927/

Slightly less cynically, datadings aims to make dealing with datasets
fast and easy.
datadings currently supports over 20 different datasets for image
classification, segmentation, saliency prediction, and remote sensing.
One command lets you download all necessary files and convert them to
the datadings format.
And since it's based on the excellent
`msgpack <http://msgpack.org>`_, a JSON-like format that supports
binary data,
it's space-efficient, blazingly fast, does not use schema, and has
support for over 50 programming languages and environments.
You are also not limited to any specific learning framework, only
Python if you want to use additional tools provided by datadings.



Fast, you say?
--------------

The ImageNet dataset (the ILSVRC2012 challenge dataset, to be precise)
is prominently featured in many scientific publications.
Tutorials on how to train models with it usually recommended unpacking
the large training and validation set tar files into separate folders.
There are now roughly 1.3 million tiny files you need to load per
epoch of training.
This is bad for HDDs and doubly bad if you access them over the network.
While datadings supports reading from datasets like these with the
:py:class:`DirectoryReader <datadings.reader.directory.DirectoryReader>`,
it will only read with a leisurely pace of about 500 samples/s.
Reading the whole training set takes about 40 minutes.
This is not fast enough for modern GPUs.

Once converted into the datadings format, you can easily saturate
10G ethernet reading well over 20000 samples/s using the
:py:class:`MsgpackReader <datadings.reader.msgpack.MsgpackReader>`.

It also takes several seconds to start reading from the directory tree,
whereas reading from msgpack files is almost instant.
This makes debugging a breeze.
Check out the :ref:`file format description<file-format>` description
if you want to know how this is achieved.



TL;DR
-----

First, use the :py:mod:`datadings-write <datadings.commands.write>`
command to create the dataset files.
It creates a ``dataset.msgpack`` file.
In your code, open this file with the
:py:class:`MsgpackReader <datadings.reader.msgpack.MsgpackReader>`
like any other file.
You can now iterate over it::

    from datadings.reader import MsgpackReader
    with MsgpackReader('dataset.msgpack') as reader:
        for sample in reader:
            [do dataset things]



Contents
========

.. toctree::
    :maxdepth: 2

    usage.rst
    conventions.rst
    file_format.rst
    add_dataset.rst
    reference.rst



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
