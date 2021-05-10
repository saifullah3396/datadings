PyTorch integration
===================

datadings provides experimental integration with PyTorch.
There are two options:

1. :py:class:`datadings.torch.Dataset`
1. :py:class:`datadings.torch.IterableDataset`

These work as expected with the PyTorch ``DataLoader``,
though ``persistent_workers=True`` must be used to let
``IterableDataset`` track the current epoch.

.. warning::
    ``Dataset`` can be significantly slower than ``IterableDataset``.
    If shuffling is necessary consider using
    :py:class:`~datadings.reader.augment.QuasiShuffler` instead.


Example usage with the PyTorch ``DataLoader``::

    path = '.../train.msgpack'
    batch_size = 256
    reader = MsgpackReader(path)
    transform = Compose((CompressedToPIL(), ..., ToTensor()))
    ds = IterableDataset(reader, transform=transform, batch_size=batch_size)
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
