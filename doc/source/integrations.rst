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

    from tqdm import tqdm
    from torch.utils.data import DataLoader
    from torchvision.transforms import ToTensor
    from torchvision.transforms import RandomResizedCrop
    from torchvision.transforms import RandomHorizontalFlip
    from torchvision.transforms import Compose


    def main():
        path = '.../train.msgpack'
        batch_size = 256
        transform = Compose((
            CompressedToPIL(),
            RandomResizedCrop((224, 224)),
            RandomHorizontalFlip(),
            ToTensor(),
        ))
        reader = MsgpackReader(path)
        ds = IterableDataset(
            reader,
            transform=transform,
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
