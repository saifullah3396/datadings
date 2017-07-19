import os
import os.path as pt
import zipfile
import re
from collections import defaultdict
import gzip

import numpy as np
import cv2
import msgpack

from datadings.reader import Reader
from datadings.sets import UnsupervisedData as YFCC100mData
from datadings.sets.YFCC100m_counts import FILE_COUNTS
from datadings.sets.YFCC100m_counts import FILES_TOTAL


ROOT = pt.abspath(pt.dirname(__file__))


def noop(data):
    return data


def validate_image(data):
    if len(data) < 2600 or len(data) == 9218:
        return None
    try:
        # decode at reduced scale for speedup
        im = cv2.imdecode(
            np.frombuffer(data, dtype=np.uint8),
            cv2.IMREAD_REDUCED_GRAYSCALE_8
        )
        # image did not decode properly
        if im is None:
            return None
        # too little data, check for meaningful content
        if len(data) < 20000 and np.percentile(im.var(0), 95) < 50:
            # print()
            # print(len(data), np.percentile(im.var(0), 95))
            return None
        return data
    except cv2.error as e:
        print(e)
        if '!buf.empty() && buf.isContinuous() in function imdecode_' in str(e):
            return None
        else:
            raise e


def _find_zip_key(zips, key):
    z, f = key.split(os.sep)
    try:
        return zips.index(z+'.zip'), f
    except ValueError:
        return 0, ''


def _find_zip_index(rejects, index):
    for i, (f, count) in enumerate(FILE_COUNTS):
        count -= len(rejects[f])
        if count > index:
            return i, index
        index -= count
    raise IndexError('index %d exceeds %d samples'
                     % (index, FILES_TOTAL))


def _filter_zipinfo(infos):
    p = re.compile(r'/[0-9a-f]+$')
    return [info for info in infos if p.search(info.filename)]


def _find_member_image(members, start_image):
    if not start_image:
        return members
    for i, m in enumerate(members):
        if m.filename.split(os.sep)[1] == start_image:
            return i


def _find_member_index(members, rejected, start_index):
    z = members[0].filename.split(os.sep)[0]
    rejected = sorted(rejected[z])
    for r in rejected:
        if start_index > r:
            start_index += 1
        else:
            break
    return start_index


def yield_from_zips(
        path,
        rejected,
        start_key=os.sep,
        start_index=0,
        validator=noop,
):
    if start_index and start_key != os.sep:
        raise ValueError('cannot set both start_key and start_index')

    zips = [pt.splitext(f)[0] for f in sorted(os.listdir(path))
            if f.endswith('.zip')]
    # find out which zipfile to start from
    if start_index:
        zip_index, start_index = _find_zip_index(rejected, start_index)
        start_image = ''
    else:
        zip_index, start_image = _find_zip_key(zips, start_key)
    zips = zips[zip_index:]

    for z in zips:
        with zipfile.ZipFile(pt.join(path, z) + '.zip') as imagezip:
            # filter out non-image members
            members = _filter_zipinfo(imagezip.infolist())
            if start_index:
                start_index = _find_member_index(members, rejected, start_index)
            elif start_image:
                start_index = _find_member_image(members, start_image)
            r = rejected[z]
            for i, m in enumerate(members[start_index:], start_index):
                if i in r:
                    continue
                f = m.filename
                yield validator(imagezip.read(f)), f, z, i
            start_index = 0
            start_image = ''


def _parse_rejected(f, rejected=None):
    if rejected is None:
        rejected = defaultdict(lambda: set())
    for l in f:
        z, i = l.split()
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
    def __init__(
            self,
            image_packs_dir,
            validator=noop,
            reject_file_paths=(
                    pt.join(ROOT, 'YFCC100m_rejected_images.txt.gz'),
            ),
            error_file=None,
            error_file_mode='a',
    ):
        self._path = image_packs_dir
        if not callable(validator):
            raise ValueError('validator must be callable, not %r'
                             % validator)
        self._validator = validator
        self._next_sample = None
        self._rejected = None
        try:
            for path in reject_file_paths:
                if path is None:
                    continue
                ofunc = open
                if path.endswith('.gz'):
                    ofunc = gzip.open
                with ofunc(path) as f:
                    self._rejected = _parse_rejected(f, self._rejected)
        except IOError:
            pass
        if error_file is None:
            self._error_file = DevNull()
        else:
            self._error_file = open(error_file, error_file_mode)
        self._gen = yield_from_zips(
            image_packs_dir, self._rejected,
            validator=self._validator,
        )

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def __del__(self):
        if hasattr(self, '_error_file'):
            self._error_file.close()

    def __len__(self):
        return FILES_TOTAL - sum(len(r) for r in self._rejected.values())

    def _get_next_sample(self):
        while self._next_sample is None:
            next_sample = next(self._gen)
            sample, key, z, i = next_sample
            if sample is None:
                if i not in self._rejected[z]:
                    self._rejected[z].add(i)
                    self._error_file.write('%s %d\n' % (z, i))
            else:
                self._next_sample = sample, key
        return self._next_sample

    def next(self):
        sample = self._convert(self._get_next_sample())
        self._next_sample = None
        return sample

    __next__ = next

    def rawnext(self):
        return msgpack.packb(self.next(), encoding='utf8')

    def seek_index(self, index):
        self._gen = yield_from_zips(
            self._path, self._rejected,
            start_index=index,
            validator=self._validator,
        )

    seek = seek_index

    def seek_key(self, key):
        self._gen = yield_from_zips(
            self._path, self._rejected,
            start_key=key,
            validator=self._validator,
        )

    def get_key(self, index=None):
        return self._get_next_sample()[1]

    def _convert(self, item):
        return YFCC100mData(*item)


def main():
    from datadings.tools import FrequencyPrinter
    from datadings.tools import print_over
    printer = FrequencyPrinter(0.5)
    reader = YFCC100mReader(
        '/ds2/YFCC100m/image_packs/', validator=validate_image
    )
    # reader.seek(29232)
    n = 0
    for key, data in reader.iter(yield_key=True):
        if n > 0:
            print(key)
        if data.sample is None:
            print(key)
        printer.update()
        n -= 1
        if not n:
            break
    print_over(printer.total_updates)


if __name__ == '__main__':
    main()
