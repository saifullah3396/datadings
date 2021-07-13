from math import ceil
from io import BytesIO
from itertools import chain
from itertools import islice

from ..reader.reader import Reader

from PIL import Image
from simplejpeg import decode_jpeg
from torch.utils.data import Dataset as _Dataset
from torch.utils.data import IterableDataset as _IterableDataset
from torch.utils.data import get_worker_info
from torch.distributed import is_initialized
from torch.distributed import get_rank
from torch.distributed import get_world_size


def _noop(sample):
    return sample


def _transform_wrapper(f, key):
    def g(sample):
        sample[key] = f(sample[key])
        return sample
    return g


class DatasetBase:
    def __init__(
            self,
            reader: Reader,
            transform=None,
            transform_key='image',
    ):
        self.reader = reader
        if transform is not None:
            self.transform = _transform_wrapper(transform, transform_key)
        else:
            self.transform = _noop

    def __len__(self):
        return len(self.reader)


class Dataset(DatasetBase, _Dataset):
    """
    Implementation of ``torch.utils.data.Dataset``.

    .. warning::
        :py:class:`~datadings.torch.Dataset` can be significantly
        slower than :py:class:`~datadings.torch.IterableDataset`.
        If shuffling is necessary consider using
        :py:class:`~datadings.reader.augment.QuasiShuffler` instead.

    Example usage with the PyTorch ``DataLoader``::

        path = '.../train.msgpack'
        batch_size = 256
        transform = Compose((CompressedToPIL(), ..., ToTensor()))
        reader = MsgpackReader(path)
        ds = Dataset(reader, transform=transform)
        train = DataLoader(dataset=ds, batch_size=batch_size)
        for epoch in range(3):
            for x, y in dict2tuple(tqdm(train)):
                pass

    Parameters:
        reader: the datadings reader instance
        transform: the transform function, see torchvision
        transform_key: which dict key will be transformed, e.g., ``image``
    """
    def __getitem__(self, index):
        return self.transform(self.reader)


# noinspection PyAbstractClass
class IterableDataset(DatasetBase, _IterableDataset):
    """
    Implementation of ``torch.utils.data.IterableDataset``.

    .. note::
        Set ``batch_size`` must be the same for both dataset
        and ``DataLoader`` to avoid overlap between workers
        (and ranks in a distributed setup).

    .. note::
        In contrast to default PyTorch behavior, a small number of
        samples may be repeated per epoch if the number of samples
        in the dataset is not exactly divisible by batch size,
        number of workers, ... 

    .. warning::
        Set ``persistent_workers=True`` for the ``DataLoader``
        to let the dataset object track the current epoch.
        Without this option torch may create new worker processes
        at any time, which resets the dataset to its initial state.

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

    Parameters:
        reader: the datadings reader instance
        transform: the transform function, see torchvision
        transform_key: which dict key will be transformed, e.g., ``image``
        batch_size: same batch size as given to the ``DataLoader``
        epoch: starting epoch; only relevant when resuming
        copy: see :py:meth:`datadings.reader.reader.Reader.iter`
        chunk_size: see :py:meth:`datadings.reader.reader.Reader.iter`
        group: distributed process group to use (if not using the default)
    """
    def __init__(
            self,
            reader: Reader,
            transform=None,
            transform_key='image',
            batch_size=1,
            epoch=1,
            copy=True,
            chunk_size=16,
            group=None
    ):
        DatasetBase.__init__(self, reader, transform, transform_key)
        if is_initialized():
            self.rank = get_rank(group)
            self.world_size = get_world_size(group)
        else:
            self.rank = 0
            self.world_size = 1
        self.batch_size = batch_size
        self.epoch = epoch - 1
        self.copy = copy
        self.chunk_size = chunk_size

    def __iter__(self):
        info = get_worker_info()
        n = len(self.reader)
        ws = self.world_size
        bs = self.batch_size
        worker_iters = int(ceil(n / ws / info.num_workers / bs)) * bs
        rank_iters = worker_iters * info.num_workers
        epoch_offset = (self.epoch * rank_iters * ws) % n
        rank = (self.rank + self.epoch) % ws
        self.epoch += 1
        start = (rank * rank_iters + info.id * worker_iters + epoch_offset) % n
        r = self.reader
        it = r.iter(start, copy=self.copy, chunk_size=self.chunk_size)
        with self.reader:
            for sample in islice(chain(it, r.iter(0)), worker_iters):
                yield self.transform(sample)


class CompressedToPIL:
    """
    Compatible torchvision transform that takes a compressed
    image as bytes (or similar) and returns a PIL image.
    """
    def __call__(self, buf):
        try:
            img = Image.fromarray(decode_jpeg(buf), 'RGB')
        except ValueError:
            img = Image.open(BytesIO(buf)).convert('RGB')
        return img

    def __repr__(self):
        return self.__class__.__name__ + '()'


def dict2tuple(it, keys=('image', 'label')):
    """
    Utility function that extracts and yields the given keys
    from each sample in the given iterator.
    """
    for sample in it:
        yield tuple(sample[k] for k in keys)
