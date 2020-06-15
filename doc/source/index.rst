datadings
=========

Dealing with different datasets can be tedious for machine learning
practitioners.
Two datasets almost never share the same directory structure and often
custom file formats are used.
How datadings fits into the picture is best explained by XKCD #927:

.. image:: https://imgs.xkcd.com/comics/standards.png
   :alt: XKCD #927
   :width: 500
   :target: https://xkcd.com/927/

Slightly less cynically, datadings aims to make dealing with datasets
fast and easy.
One command lets you download all necessary files and convert them to
the datadings format.
And since it's based on the excellent
`msgpack <http://msgpack.org>`_, it's space-efficient, blazingly fast,
does not require schema, and you can use it with any of the over 50
supported languages.
As long as you use Python, datadings does also not care what kind of
learning framework you are going to use.



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

Once converted into the datadings format, you can easily saturate
10G ethernet reading well over 20000 samples/s using the
:py:class:`MsgpackReader <datadings.reader.msgpack.MsgpackReader>`.

To top it all off, it also takes over 7 seconds to start reading from
the directory tree, whereas is takes less than 0.7 seconds to start
reading from msgpack files.
This makes debugging a breeze.
Check out the
:ref:`file format description<file-format>`
if you want to know more.



Where do I start?
-----------------

Right now datadings includes code to (down)load over 20 different
datasets for image classification, segmentation, saliency prediction,
and remote sensing.



Reference
=========

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   file_format.rst
   generated/datadings.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
