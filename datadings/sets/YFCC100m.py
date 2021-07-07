"""
The Yahoo Flickr Creative Commons 100 Million (YFCC100m) dataset.

Important:
    Only images are included.
    No videos or metadata.

See also:
    https://multimediacommons.wordpress.com/yfcc100m-core-dataset/

Warning:
    This code is intended to load a pre-release version of the
    YFCC100m dataset.
    Please complain if you want to use the release version available
    from amazon:
    https://multimediacommons.wordpress.com/yfcc100m-core-dataset/
"""

import os
import os.path as pt
import zipfile
import re
import io
from collections import defaultdict

import numpy as np
from simplejpeg import decode_jpeg
from PIL import Image

from ..reader import Reader
from ..tools.msgpack import unpack
from ..tools.msgpack import make_packer
from . import ImageData
from .YFCC100m_counts import FILE_COUNTS
from .YFCC100m_counts import FILES_TOTAL
from ..tools import document_keys
from ..tools.open import open_comp


__doc__ += document_keys(ImageData)


ROOT = pt.abspath(pt.dirname(__file__))
REJECTED_PATH = pt.join(ROOT, 'YFCC100m_rejected_images.msgpack.xz')


def noop(data):
    return data


def decode_fast(data):
    try:
        # decode JPEGs at reduced scale for speedup
        return decode_jpeg(
            data,
            'gray',
            fastdct=True,
            fastupsample=True,
            min_height=1,
            min_width=1
        )
    except ValueError:
        # use pillow in case anything goes wrong
        bio = io.BytesIO(data)
        return np.array(Image.open(bio).convert('L'))


def validate_image(data):
    if len(data) < 2600 or len(data) == 9218:
        return None
    try:
        im = decode_fast(data)
        # if only small amounts of data, check for meaningful content,
        # i.e., at least 5% of all lines in image show some variance
        if len(data) < 20000 and np.percentile(im.var(0), 95) < 50:
            return None
        return data
    except (ValueError, IOError, OSError):
        return None


def _find_zip_key(rejected, zips, key):
    z, f = key.split(os.sep)
    try:
        zip_index = zips.index(z)
    except ValueError:
        raise IndexError('ZIP file {!r} not found'.format(z))

    partial_index = 0
    for z, count in FILE_COUNTS[:zip_index]:
        partial_index += count - len(rejected[z])

    return zip_index, f, partial_index


def _find_zip_index(rejects, index):
    total = FILES_TOTAL
    for z, _ in FILE_COUNTS:
        total -= len(rejects[z])
    if index < 0:
        index += total
    if index < 0 or index >= total:
        raise IndexError('index {} out of range for {} items'.format(
            index, total - 1
        ))
    partial_index = 0
    for i, (z, count) in enumerate(FILE_COUNTS):
        count -= len(rejects[z])
        if partial_index + count > index:
            return i, index - partial_index, partial_index
        partial_index += count


def _filter_zipinfo(infos):
    p = re.compile(r'/[0-9a-f]+$')
    return [info for info in infos if p.search(info.filename)]


def _find_member_image(members, rejected, start_image):
    if not start_image:
        return members
    for i, m in enumerate(members):
        if m.filename.split(os.sep)[1] == start_image:
            if i in rejected:
                raise IndexError(
                    '{!r} is on the rejected list'.format(m.filename)
                )
            return i
    raise IndexError('{!r} not found'.format(start_image))


def _find_member_index(rejected, start_index):
    for r in rejected:
        if start_index > r:
            start_index += 1
        else:
            break
    return start_index


def _find_start(
        path,
        rejected,
        start_key='',
        start_index=0
):
    if start_index and start_key:
        raise ValueError('cannot set both start_key and start_index')

    zips = [f for f, _ in FILE_COUNTS]
    # find out which zipfile to start from
    if start_index:
        zip_index, start_index, partial_index = _find_zip_index(rejected, start_index)
        start_image = ''
    elif start_key:
        zip_index, start_image, partial_index = _find_zip_key(rejected, zips, start_key)
    else:
        return zips, 0, 0

    z = zips[zip_index]
    r = rejected[z]
    with zipfile.ZipFile(pt.join(path, z) + '.zip') as imagezip:
        # z must be bytes so the set of rejected images is found in py3
        # filter out non-image members
        members = _filter_zipinfo(imagezip.infolist())
    if start_index:
        start_index = _find_member_index(r, start_index)
    elif start_image:
        start_index = _find_member_image(members, r, start_image)
    return zips[zip_index:], start_index, partial_index


def _yield_from_zips(
        path,
        zips,
        rejected,
        start_index,
        validator=noop,
):
    for z in zips:
        with zipfile.ZipFile(pt.join(path, z) + '.zip') as imagezip:
            r = rejected[z]
            # filter out non-image members
            members = _filter_zipinfo(imagezip.infolist())
            for i, m in enumerate(members[start_index:], start_index):
                if i in r:
                    continue
                f = m.filename
                yield validator(imagezip.read(f)), f, z, i
        start_index = 0


def _parse_rejected(path, rejected):
    try:
        with open_comp(path, "rb") as f:
            new_rejected = unpack(f)
        for z, r in new_rejected.items():
            rejected[z].update(r)
        return rejected
    except ValueError:
        with open_comp(path, "rt", encoding="utf-8") as f:
            for line in f:
                z, i = line.strip("\n").split(' ')
                rejected[z].add(int(i))
        return rejected


class DevNull(object):
    def read(self, *_):
        pass

    def write(self, *_):
        pass

    def close(self):
        pass


class YFCC100mReader(Reader):
    """
    Special reader for the YFCC100m dataset only.
    It reads images from 10000 ZIP files of roughly 10000 images
    each.

    One pass over the whole dataset was made to filter out irrelevant
    images if one of the following conditions is met:

    - Image is damaged/incomplete.
    - Less than 2600 bytes.
    - Exactly 9218 bytes - a placeholder image from Flickr.
    - Less than 20000 bytes and less than 5% of lines in the image
      have a variance less than 50.

    Which images are rejected is controlled by the files given as
    ``reject_file_paths``.
    Set this to None or empty list to iterate over the whole dataset.

    Parameters:
        image_packs_dir: Path to directory with image ZIP files.
        validator: Callable
                   ``validator(data: bytes) -> Union[bytes, None]``.
                   Validates images before they are returned.
                   Receives image data and returns data or ``None``.

    Warning:
        A validating reader cannot be copied and it is strongly
        discourages to copy readers with ``error_file`` paths.

    Warning:
        Methods``get``, ``slice``, ``find_index``, ``find_key``,
        ``seek_index``, and ``seek_key`` are considerably slower
        for this reader compared to others.
        Use iterators and large ``slice`` ranges instead.
    """
    _do_not_copy = ('_gen', '_error_file')

    def __init__(
            self,
            image_packs_dir,
            validator=noop,
            reject_file_paths=(REJECTED_PATH,),
            error_file=None,
            error_file_mode='a',
    ):
        super().__init__()
        self._path = image_packs_dir
        if not callable(validator):
            raise ValueError('validator must be callable, not %r'
                             % validator)
        self._validator = validator
        self._rejected = defaultdict(lambda: set())
        for path in reject_file_paths or ():
            self._rejected = _parse_rejected(path, self._rejected)
        self._packer = make_packer()
        self._error_file_args = error_file, error_file_mode
        self._error_file = None
        self.open_error_file_()
        self._gen = None
        self.seek_index(0)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def __del__(self):
        if hasattr(self, '_error_file'):
            self._error_file.close()

    def __len__(self):
        return FILES_TOTAL - sum(len(r) for r in self._rejected.values())

    def __contains__(self, key):
        try:
            self.find_index(key)
            return True
        except IndexError:
            return False

    def __copy__(self):
        if self._validator != noop:
            raise RuntimeError('cannot copy a validating reader')
        reader = super().__copy__()
        reader.open_error_file_()
        reader.seek_index(self._i)
        return reader

    def open_error_file_(self):
        error_file, error_file_mode = self._error_file_args
        if error_file is None:
            self._error_file = DevNull()
        else:
            self._error_file = open(error_file, error_file_mode)

    def _get_next_sample(self, gen):
        while True:
            sample, key, z, i = next(gen)
            if i in self._rejected[z]:
                continue
            if sample is None:
                self._rejected[z].add(i)
                self._error_file.write('%s %d\n' % (z, i))
            else:
                break
        return ImageData(key, sample)

    def next(self):
        return self._get_next_sample(self._gen)

    __next__ = next

    def rawnext(self):
        return self._packer.pack(self.next())

    def find_index(self, key):
        zips, start_index, index = _find_start(
            self._path, self._rejected, start_key=key
        )

        # count up to start_index in zip and all samples
        # that are not in rejected to index
        r = self._rejected[zips[0]]
        for i in range(start_index):
            if i not in r:
                index += 1

        if index != 0 and self._validator != noop:
            raise RuntimeError('found index may be incorrect while validating')

        return start_index

    def find_key(self, index):
        if index != 0 and self._validator != noop:
            raise RuntimeError('found key may be incorrect while validating')

        zips, start_index, _ = _find_start(
            self._path, self._rejected, start_index=index
        )
        gen = _yield_from_zips(
            self._path, zips, self._rejected, start_index, self._validator,
        )
        sample, key, _, _ = next(gen)
        return key

    def seek_index(self, index):
        if index != 0 and self._validator != noop:
            raise RuntimeError('can only seek to start while validating')

        zips, start_index, _ = _find_start(
            self._path, self._rejected, start_index=index
        )

        self._gen = _yield_from_zips(
            self._path, zips, self._rejected, start_index, self._validator,
        )
        self._i = index

    def seek_key(self, key):
        zips, start_index, index = _find_start(
            self._path, self._rejected, start_key=key
        )

        # count up to start_index in zip and all samples
        # that are not in rejected to index
        r = self._rejected[zips[0]]
        for i in range(start_index):
            if i not in r:
                index += 1

        if index != 0 and self._validator != noop:
            raise RuntimeError('can only seek to start while validating')

        self._gen = _yield_from_zips(
            self._path, zips, self._rejected, start_index, self._validator,
        )
        self._i = index

    def get(self, index, yield_key=False, raw=False, copy=True):
        if index != 0 and self._validator != noop:
            raise RuntimeError('can only seek to start while validating')

        zips, start_index, _ = _find_start(
            self._path, self._rejected, start_index=index
        )

        gen = _yield_from_zips(
            self._path, zips, self._rejected, start_index, self._validator,
        )
        return self._get_next_sample(gen)

    def _iter_impl(
            self,
            start=None,
            stop=None,
            yield_key=False,
            raw=False,
            copy=True,
            chunk_size=16,
    ):
        if start != 0 and self._validator != noop:
            raise RuntimeError('can only seek to start while validating')

        start, stop, _ = slice(start, stop).indices(len(self))

        zips, start_index, _ = _find_start(
            self._path, self._rejected, start_index=start
        )
        gen = _yield_from_zips(
            self._path, zips, self._rejected, start_index, self._validator,
        )

        if raw:
            pack = self._packer.pack
        else:
            pack = noop

        if yield_key:
            for i in range(start, stop):
                sample = self._get_next_sample(gen)
                self._i = i
                yield sample['key'], pack(sample)
        else:
            for i in range(start, stop):
                sample = self._get_next_sample(gen)
                self._i = i
                yield pack(sample)

    def slice(self, start, stop=None, yield_key=False, raw=False, copy=True):
        return self._iter_impl(start, stop, yield_key, raw, copy)


def main():
    import argparse

    from ..tools import make_printer
    from ..tools import print_over

    parser = argparse.ArgumentParser(
        description='Load and decode every image from given image packs. '
                    'If an image either does not decode properly or does '
                    'not contain useful content, its containing zip file '
                    'and name are written to the reject file.')
    parser.add_argument(
        'image_packs',
        type=str,
        help='path to directory of image zip files',
    )
    parser.add_argument(
        '-r', '--rejectfile',
        type=str,
        help='path to rejected images log file',
    )

    args = parser.parse_args()

    printer = make_printer(total=100000000)
    reader = YFCC100mReader(
        args.image_packs,
        validator=validate_image,
        reject_file_paths=(),
        error_file=args.rejectfile
    )
    for key, data in reader.iter(yield_key=True):
        if data['image'] is None:
            print('rejected', key)
        printer.update()
    print_over(printer.total_updates, 'images passed testing')


if __name__ == '__main__':
    main()
