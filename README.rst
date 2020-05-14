Wat?
====

datadings is a collection of tools to prepare public datasets
for machine learning, based on simple principles.

    Datasets are collections of individual data samples.
    A sample is a dictionary with descriptive keys.

E.g., for supervised training each sample is a dictionary
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



Already Included Datasets
-------------------------

For an up-to-date list of datasets look into the `datadings/sets <datadings/sets>`_ folder!

================  ============================
Dataset           Short Description           
================  ============================
ADE20k_           Scene Parsing, Segmentation
ANP460_           own Eye-Tracking dataset (Jalpa)
CAMVID_           Motion-based Segmentation
CAT2000_          MIT Saliency
CIFAR_            32x32 color image classification with 10/100 classes
Cityscape_        Segmentation, Semantic understanding of urban street scenes
Coutrot1_         Eye-Tracking, Saliency
FIGRIMFixation_   Eye-Tracking, Saliency
ILSVRC2012_       Imagenet Large Scale Visual Recognition Challenge
InriaBuildings_   Inria Areal Image Labeling Dataset (Buildings), Segmentation, Remote Sensing
MIT1003_          Eye-Tracking, Saliency, Learning to predict where humans look
MIT300_           Eye-Tracking, Saliency
Places2017_       MIT Places, Scene Recognition
Places365_        MIT Places365, Scene Recognition
RIT18_            High-Res Multispectral Semantic Segmentation, Remote Sensing
SALICON_          Saliency in Context, Eye-Tracking
VOC2012_          Pascal Visual Object Classes Challenge
Vaihingen_        Remote Sensing, Semantic Object Classification, Segmentation
YFCC100m_         Yahoo Flickr Creative Commons 100 M pics
iSUN_             Large-Scale Scene Understanding, Saliency
================  ============================


.. _ADE20k: http://groups.csail.mit.edu/vision/datasets/ADE20K/
.. _ANP460: 
.. _CAMVID: http://mi.eng.cam.ac.uk/research/projects/VideoRec/CamVid/
.. _CAT2000: http://saliency.mit.edu/results_cat2000.html
.. _CIFAR: https://www.cs.toronto.edu/~kriz/cifar.html
.. _Cityscape: https://www.cityscapes-dataset.com/
.. _Coutrot1: http://antoinecoutrot.magix.net/public/databases.html
.. _FIGRIMFixation: http://figrim.mit.edu/index_eyetracking.html
.. _ILSVRC2012: http://www.image-net.org/challenges/LSVRC/2012/
.. _InriaBuildings: https://project.inria.fr/aerialimagelabeling/
.. _MIT1003: http://people.csail.mit.edu/tjudd/WherePeopleLook/index.html
.. _MIT300: http://saliency.mit.edu/results_mit300.html
.. _Places2017: http://places.csail.mit.edu/
.. _Places365: http://places2.csail.mit.edu/
.. _RIT18: https://github.com/rmkemker/RIT-18
.. _SALICON: http://salicon.net/
.. _VOC2012: http://host.robots.ox.ac.uk/pascal/VOC/voc2012/
.. _Vaihingen: http://www2.isprs.org/commissions/comm3/wg4/2d-sem-label-vaihingen.html
.. _YFCC100m: http://yfcc100m.appspot.com/about
.. _iSUN: http://lsun.cs.princeton.edu/2017/



Usage
-----

Each dataset defines modules to read and write in the
``datadings.sets`` package.
Let's consider the *MIT1003* dataset as an example.

``MIT1003_write`` is an executable that creates dataset files.
It can be called directly or through *datadings-write*.
Three files will be written:

* ``MIT1003.msgpack`` contains sample data
* ``MIT1003.msgpack.index`` contains offsets for random access
* ``MIT1003.msgpack.md5`` contains MD5 hashes of both files

Reading all samples sequentially,
using a ``MsgpackReader`` as a context manager::

    with MsgpackReader('MIT1003.msgpack') as reader:
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
Optionally, a ``FOO`` module can define custom sample classes
and a ``FOOReader``.

A custom sample type should be called ``FOOData`` and must be a
subclass of dict.

For msgpack-based datasets ``MsgpackReader`` usually provides
all required functionality out of the box.
If a custom ``FOOReader`` is necessary it must be a subclass of
``datadings.reader.Reader``.
