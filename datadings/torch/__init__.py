from io import BytesIO

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


class Dataset(DatasetBase, _Dataset):
    def __getitem__(self, index):
        return self.transform(self.reader)


class IterableDataset(DatasetBase, _IterableDataset):
    def __init__(
            self,
            reader: Reader,
            transform=None,
            transform_key='image',
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
        self.copy = copy
        self.chunk_size = chunk_size

    def __len__(self):
        return len(self.reader)

    def __iter__(self):
        info = get_worker_info()
        n = len(self.reader)
        rank_iters = n // self.world_size
        worker_iters = rank_iters // info.num_workers
        start = self.rank * rank_iters + info.id * worker_iters
        with self.reader:
            for sample in self.reader.iter(
                    start=start,
                    stop=start+worker_iters,
                    copy=self.copy,
                    chunk_size=self.chunk_size
            ):
                yield self.transform(sample)


class CompressedToPIL:
    def __call__(self, buf):
        try:
            img = Image.fromarray(decode_jpeg(buf), 'RGB')
        except ValueError:
            img = Image.open(BytesIO(buf)).convert('RGB')
        return img

    def __repr__(self):
        return self.__class__.__name__ + '()'


def dict2tuple(it, keys=('image', 'label')):
    for sample in it:
        yield tuple(sample[k] for k in keys)
