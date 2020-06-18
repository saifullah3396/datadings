datadings is a collection of tools to prepare public datasets
for machine learning, based on two basic principles:

    Datasets are collections of individual data samples.
    A sample is a dictionary with descriptive keys.

E.g., for supervised training with images each sample is a dictionary
``{'image': imagedata, 'label': label)``.
More images and meta-data may be added as required.

`msgpack <http://msgpack.org>`_ is used as an efficient storage
format for most supported datasets.



Supported datasets
==================

================  ============================
Dataset           Short Description           
================  ============================
ADE20k_           Scene Parsing, Segmentation
ANP460_           own Eye-Tracking dataset (Jalpa)
CAMVID_           Motion-based Segmentation
CAT2000_          MIT Saliency
CIFAR_            32x32 color image classification with 10/100 classes
Cityscapes_       Segmentation, Semantic understanding of urban street
                  scenes
Coutrot1_         Eye-Tracking, Saliency
FIGRIMFixation_   Eye-Tracking, Saliency
ILSVRC2012_       Imagenet Large Scale Visual Recognition Challenge
InriaBuildings_   Inria Areal Image Labeling Dataset (Buildings),
                  Segmentation, Remote Sensing
MIT1003_          Eye-Tracking, Saliency, Learning to predict where
                  humans look
MIT300_           Eye-Tracking, Saliency
Places2017_       MIT Places, Scene Recognition
Places365_        MIT Places365, Scene Recognition
RIT18_            High-Res Multispectral Semantic Segmentation,
                  Remote Sensing
SALICON2015_      Saliency in Context, Eye-Tracking
SALICON2017_      Saliency in Context, Eye-Tracking
VOC2012_          Pascal Visual Object Classes Challenge
Vaihingen_        Remote Sensing, Semantic Object Classification,
                  Segmentation
YFCC100m_         Yahoo Flickr Creative Commons 100 M pics
================  ============================


.. _ADE20k: http://groups.csail.mit.edu/vision/datasets/ADE20K/
.. _ANP460: 
.. _CAMVID: http://mi.eng.cam.ac.uk/research/projects/VideoRec/CamVid/
.. _CAT2000: http://saliency.mit.edu/results_cat2000.html
.. _CIFAR: https://www.cs.toronto.edu/~kriz/cifar.html
.. _Cityscapes: https://www.cityscapes-dataset.com/
.. _Coutrot1: http://antoinecoutrot.magix.net/public/databases.html
.. _FIGRIMFixation: http://figrim.mit.edu/index_eyetracking.html
.. _ILSVRC2012: http://www.image-net.org/challenges/LSVRC/2012/
.. _InriaBuildings: https://project.inria.fr/aerialimagelabeling/
.. _MIT300: http://saliency.mit.edu/results_mit300.html
.. _MIT1003: http://people.csail.mit.edu/tjudd/WherePeopleLook/index.html
.. _Places365: http://places2.csail.mit.edu/
.. _Places2017: http://places.csail.mit.edu/
.. _RIT18: https://github.com/rmkemker/RIT-18
.. _SALICON2015: http://salicon.net/challenge-2015/
.. _SALICON2017: http://salicon.net/challenge-2017/
.. _Vaihingen: http://www2.isprs.org/commissions/comm3/wg4/2d-sem-label-vaihingen.html
.. _VOC2012: http://host.robots.ox.ac.uk/pascal/VOC/voc2012/
.. _YFCC100m: http://yfcc100m.appspot.com/about



Command line tools
==================

* *datadings-write*
  creates new dataset files.
* *datadings-cat*
  prints the (abbreviated) contents of a dataset file.
* *datadings-shuffle*
  shuffles an existing dataset file.
* *datadings-merge*
  merges two or more dataset files.
* *datadings-split*
  splits a dataset file into two or more subsets.
* *datadings-bench*
  runs some basic read performance benchmarks.



Basic usage
===========

Each dataset defines modules to read and write in the
``datadings.sets`` package.
For most datasets the reading module only contains additional
metadata like class labels and distributions.

Let's consider the *MIT1003* dataset as an example.

``MIT1003_write`` is an executable that creates dataset files.
It can be called directly or through *datadings-write*.
Three files will be written:

* ``MIT1003.msgpack`` contains sample data
* ``MIT1003.msgpack.index`` contains index for random access
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

