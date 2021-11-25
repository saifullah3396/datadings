from math import ceil
from io import BytesIO
from itertools import chain
from itertools import islice
from typing import Iterable
from typing import Callable
import inspect
import warnings

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


def _getargs(f):
    spec = inspect.getfullargspec(f)
    args = spec.args + spec.kwonlyargs
    # f must be callable
    if isinstance(f, Callable):
        # remove first arg for callables that are not functions
        # and warn if name of the arg is not self
        if not inspect.isfunction(f):
            if args:
                if args[0] != 'self':
                    warnings.warn(
                        f"expected first argument of {f!r} to be 'self', "
                        f"but found {args[0]!r}, arguments given to this "
                        "transform may be incorrect"
                    )
                args = args[1:]
    else:
        raise ValueError(f'transform must be callable, not {f!r}')
    # if there are args, return all but the first arg
    # warn if there are also varargs, which will be ignored
    if args:
        if spec.varargs:
            warnings.warn(f'varargs are ignored for {f!r}')
        return args[1:]
    # if there are no args check if there are varargs instead
    # this is the case for non-functional torchvision transforms
    # warn that this transform can only accept values and no parameters
    else:
        if spec.varargs:
            warnings.warn(f"{f!r} only accepts varargs so "
                          "it will only receive sample values")
        else:
            raise ValueError('transforms must accept at least one argument '
                             f'but {f!r} accepts none')
        return []


class Compose:
    """
    Compose a sequence of transform functions.
    Functions must accept the intended value from samples
    as first argument.
    They may have an arbitrary number of positional and
    keyword arguments.

    Example usage with :py:class:`.Dataset`::

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

    Parameters:
        transforms: sequence of transform functions,
                    either one iterable or varargs
        prefix: string prefix for parameter names, i.e.,
                if a function normally requires parameter
                ``size`` given ``prefix='mask_'``
                the parameter ``'mask_size'``
    """
    def __init__(self, *transforms, prefix=''):
        if len(transforms) == 1 and isinstance(transforms[0], Iterable):
            transforms = transforms[0]
        self.transforms = tuple(transforms)
        self.param_names = [
            tuple(prefix + arg for arg in _getargs(f))
            for f in transforms
        ]
        self.prefix = prefix

    def __call__(self, value, params):
        try:
            for f, ps in zip(self.transforms, self.param_names):
                value = f(value, **{p: params[p] for p in ps if p in params})
            return value
        except TypeError as e:
            raise KeyError('Required parameters for transform function are '
                           'missing. Incomplete rng function? Missing constants? '
                           + str(e))


def no_rng(_):
    return {}


class DatasetBase:
    def __init__(
            self,
            reader: Reader,
            transforms=None,
            rng=None,
    ):
        self.reader = reader
        self._rng = rng or no_rng
        self._transforms = transforms
        if transforms is not None:
            if isinstance(transforms, dict):
                self.transform = self._transform
            else:
                self.transform = transforms
        else:
            self.transform = _noop

    def _transform(self, sample):
        params = self._rng(sample)
        sample['__params__'] = params
        for k, f in self._transforms.items():
            sample[k] = f(sample[k], params)
        return sample

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
        reader = MsgpackReader(path)
        transforms = {'image': Compose(
            CompressedToPIL(),
            ...,
            ToTensor(),
        )}
        ds = Dataset(reader, transforms=transforms)
        train = DataLoader(dataset=ds, batch_size=batch_size)
        for epoch in range(3):
            for x, y in dict2tuple(tqdm(train)):
                pass

    Parameters:
        reader: the datadings reader instance
        transforms: Transforms applied to samples before they are returned.
                    Either a dict of transform functions or callable with
                    signature ``f(sample: dict) -> dict`` that is applied
                    directly to samples.
                    In the dict form keys correspond to keys in the sample
                    and values are callables with signature
                    ``t(value: any, params: dict) -> any`` (e.g., an
                    instance of :py:class:`.Compose`) with ``params`` the
                    value returned by the ``rng`` callable.
        rng: callable with signature ``rng(params: dict) -> dict`` that
             returns a dict of parameters applied to transforms
    """
    def __getitem__(self, index):
        return self.transform(self.reader.get(index))


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
        transforms = {'image': Compose(
            CompressedToPIL(),
            ...,
            ToTensor(),
        )}
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

    Parameters:
        reader: the datadings reader instance
        transforms: Transforms applied to samples before they are returned.
                    Either a dict of transform functions or callable with
                    signature ``f(sample: dict) -> dict`` that is applied
                    directly to samples.
                    In the dict form keys correspond to keys in the sample
                    and values are callables with signature
                    ``t(value: any, params: dict) -> any`` (e.g., an
                    instance of :py:class:`.Compose`) with ``params`` the
                    value returned by the ``rng`` callable.
        rng: callable with signature ``rng(params: dict) -> dict`` that
             returns a dict of parameters applied to transforms
        batch_size: same batch size as given to the ``DataLoader``
        epoch: starting epoch; only relevant when resuming
        copy: see :py:meth:`datadings.reader.reader.Reader.iter`
        chunk_size: see :py:meth:`datadings.reader.reader.Reader.iter`
        group: distributed process group to use (if not using the default)
    """
    def __init__(
            self,
            reader: Reader,
            transforms=None,
            rng=None,
            batch_size=1,
            epoch=1,
            copy=True,
            chunk_size=16,
            group=None
    ):
        DatasetBase.__init__(self, reader, transforms, rng)
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
        # try to get info for Dataloader worker
        # default to 1 worker of not available
        info = get_worker_info()
        if info is None:
            num_workers = 1
            worker_index = 0
        else:
            num_workers = info.num_workers
            worker_index = info.id

        n = len(self.reader)
        ws = self.world_size
        bs = self.batch_size
        worker_iters = int(ceil(n / ws / num_workers / bs)) * bs
        rank_iters = worker_iters * num_workers
        epoch_offset = (self.epoch * rank_iters * ws) % n
        rank = (self.rank + self.epoch) % ws
        self.epoch += 1
        start = (rank * rank_iters + worker_index * worker_iters + epoch_offset) % n
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
