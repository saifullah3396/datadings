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



Already Included Datasets
-------------------------

For an up-to-date list of datasets look into the `datasets/sets <datasets/sets>`_ folder!

================  ============================
Dataset           Short Description           
================  ============================
ADE20k_           Scene Parsing, Segmentation
ANP460_           own Eye-Tracking dataset (Jalpa)
CAMVID_           Motion-based Segmentation
CAT2000_          MIT Saliency
Cityscape_        Segmentation, Semantic understanding of urban street scenes
Coutrot1_         Eye-Tracking, Saliency
FIGRIMFixation_   Eye-Tracking, Saliency
ILSVRC2012_       Imagenet Large Scale Visual Recognition Challenge
InriaBuildings_   Inria Areal Image Labeling Dataset (Buildings), Segmentation, Remote Sensing
MIT1003_          Eye-Tracking, Saliency, Learning to predict where humans look
MIT300_           Eye-Tracking, Saliency
Places2017_       MIT Places, Scene Recognition
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
.. _Cityscape: https://www.cityscapes-dataset.com/
.. _Coutrot1: http://antoinecoutrot.magix.net/public/databases.html
.. _FIGRIMFixation: http://figrim.mit.edu/index_eyetracking.html
.. _ILSVRC2012: http://www.image-net.org/challenges/LSVRC/2012/
.. _InriaBuildings: https://project.inria.fr/aerialimagelabeling/
.. _MIT1003: http://people.csail.mit.edu/tjudd/WherePeopleLook/index.html
.. _MIT300: http://saliency.mit.edu/results_mit300.html
.. _Places2017: http://places.csail.mit.edu/
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

