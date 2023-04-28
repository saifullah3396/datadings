Supported datasets
==================

The following datasets are directly supports by datadings,
meaning they include code to convert them to the fast
msgpack format.
Where possible they will download files, though some datasets
like ILSVRC2012 require an account and need to be downloaded
manually.
Additionally all datasets include further metadata,
such as list of classes and mappings, frequencies etc.


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
ILSVRC2012_       Imagenet Large Scale Visual Recognition Challenge, 2012 version
ImageNet1k_       Alias for ILSVRC2012
ImageNet21k_      A superset of ILSVRC2012 with 11 M images for 10450 classes
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
.. _ImageNet1k: http://www.image-net.org/challenges/LSVRC/2012/
.. _ImageNet21k: https://image-net.org/download.php
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
.. _YFCC100m: https://multimediacommons.wordpress.com/yfcc100m-core-dataset/