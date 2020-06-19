Data conventions
================

datadings is built around two basic principles:

    Datasets are collections of individual data samples.

    Each sample is a dictionary with descriptive keys.

E.g., for supervised training with images each sample is a dictionary
``{'key': unique_key, 'image': imagedata, 'label': label)``.
Depending on the type of dataset different keys are used.
There is no schema to dictate which keys are allowed and what they
stand for, with the exception of the ``"key"`` which is always a
unique identifier of that sample in the dataset.
datadings follows the best-effort principle that the kind of data
associated with a certain key remains the same across datasets.
These are some common keys and their meanings:

- ``"key"``: Unique identifier of this sample.
- ``"image"``: Contents of an image file.
  Use any standard image library to get pixel data.
- ``"label"``: Numerical label for the whole sample.
- ``"*_image"``: Same as image, but different semantics.
  For example, ``"label_image"`` with per-pixel segmentation
  labels, or ``"instance_image"`` for instance segmentation.
- ``"experiments"``: A list of experiments, usually saliency.
  Type depends on dataset.
- ``"locations"``: List of (x,y) coordinates.
- ``"map"``: Fixation map as image.
- ``"fixations"``: List of (x,y) fixation points.
