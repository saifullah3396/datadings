PyTorch integration
===================

datadings provides experimental integration with PyTorch.
There are two options:

#. :py:class:`~datadings.torch.Dataset`
#. :py:class:`~datadings.torch.IterableDataset`

These implement the respective PyTorch dataset classes and
work as expected with the PyTorch ``DataLoader``.


.. note::
    ``persistent_workers=True`` must be used to let
    :py:class:`~datadings.torch.IterableDataset` track the
    current epoch.


.. warning::
    :py:class:`~datadings.torch.Dataset` can be significantly
    slower than :py:class:`~datadings.torch.IterableDataset`.
    If shuffling is necessary consider using
    :py:class:`~datadings.reader.augment.QuasiShuffler` instead.


Example usage with the PyTorch ``DataLoader``::

    from datadings.reader import MsgpackReader
    from datadings.torch import IterableDataset
    from datadings.torch import CompressedToPIL
    from datadings.torch import dict2tuple
    from datadings.torch import Compose

    from tqdm import tqdm
    from torch.utils.data import DataLoader
    from torchvision.transforms import ToTensor
    from torchvision.transforms import RandomResizedCrop
    from torchvision.transforms import RandomHorizontalFlip


    def main():
        path = '.../train.msgpack'
        batch_size = 256
        transforms = {'image': Compose(
            CompressedToPIL(),
            RandomResizedCrop((224, 224)),
            RandomHorizontalFlip(),
            ToTensor(),
        )}
        reader = MsgpackReader(path)
        ds = IterableDataset(
            reader,
            transforms=transforms,
            batch_size=batch_size,
        )
        train = DataLoader(
            dataset=ds,
            batch_size=batch_size,
            num_workers=4,
            persistent_workers=True,
        )
        for epoch in range(3):
            print('Epoch', epoch)
            for x, y in dict2tuple(tqdm(train)):
                pass


    if __name__ == "__main__":
        main()


In our example ``transforms`` is a dictionary with one key ``'image'``.
That means the given transformation is applied to the value
with this key.
You can add more keys and transforms to apply functions to
different keys.

.. note::
    There will be warnings that transforms only accept varargs
    when using non-functional torchvision
    `transforms <https://pytorch.org/vision/stable/transforms.html>`_
    due to their opaque call signatures.
    This is fine, since these transforms only need the value as
    input.
    Other transforms may not work though.

If you need to share randomness between transformations (e.g. to
synchronize augmentation steps between image and mask in semantic
segmentation) you can use functions that accept randomness as
parameters, like
`functional transforms <https://pytorch.org/vision/stable/transforms.html#functional-transforms>`_
from torchvision.
Datasets accept a callable ``rng`` parameter with signature
``rng(sample: dict) -> dict``.
``sample`` is the sample that is going to be transformed and the
returned dictionary must contain all positional parameters
required by the transform functions.
The :py:class:`~datadings.torch.Compose` object reads the function
signatures of your transforms to determine which parameters are
required.
A minimal example for how this works::

    import random
    from datadings.torch import Compose
    from datadings.torch import Dataset
    from datadings.reader import ListReader

    def add(v, number):
        return v + number

    def sub(x, value):
        return x - value

    def rng(_):
        return {
            'number': random.randrange(1, 10),
            'value': random.randrange(1, 10),
        }

    samples = [{'a': 0, 'b': 0, 'c': 0} for _ in range(10)]
    reader = ListReader(samples)
    transforms = {
        'a': Compose(add),
        'b': Compose(sub),
        'c': Compose((add, sub)),
    }
    dataset = Dataset(reader, transforms=transforms, rng=rng)
    for i in range(len(dataset)):
        print(dataset[i])


.. note::
    You can use :py:func:`functools.partial` (or similar)
    to set constant values for parameters and change defaults
    for keyword arguments instead of including them in your
    ``rng`` dictionary.

.. warning::
    Transform functions will receive the same value if they
    share parameter names.
    If this is not intended you must wrap one of those
    functions in another function with and change on of the
    parameter names.

Alternatively ``transforms`` may be a custom function with
signature ``t(sample: dict) -> dict``.
This allows you to use multiple values from the sample for a
transform, create new values based on the sample, etc.
