"""Create ILSVRC 2012 data set files.

The data set is described here:
    http://image-net.org/challenges/LSVRC/2012/index

The tar files need to be unpacked.
"""
from __future__ import print_function

import threading as th
import os
import os.path as pt
import io
import gzip
import random
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import cpu_count

try:
    from turbojpeg import decode_jpeg
    from turbojpeg import encode_jpeg as _encode_jpeg

    def encode_jpeg(image):
        return _encode_jpeg(image, 85, colorsubsampling='422')
except ImportError:
    from PIL import Image

    def decode_jpeg(data):
        b = io.BytesIO(data)
        im = Image.open(b)
        im.load()
        return im

    def encode_jpeg(data):
        b = io.BytesIO(data)
        data.convert('RGB').save(b, format='JPEG', quality=85, subsampling=1)
        return b.getvalue()

from ..writer import FileWriter
from . import ImageClassificationData
from ..tools import IntervalPrinter


def __yield_ilsvrc2012_metadata(name, shuffle):
    path = pt.join(pt.abspath(pt.dirname(__file__)),
                   'ILSVRC2012_%s.txt.gz' % name)
    with gzip.open(path, 'rt', encoding='utf8') as f:
        items = (l.strip('\n').split(' ', 1) for l in f)
        if shuffle:
            items = list(items)
            random.shuffle(items)
        for item in items:
            yield item


def __verify_image(data, compress):
    im = decode_jpeg(data)
    return encode_jpeg(im) if compress else data


def write_sets(indir, outdir, shuffle=True, compress=False):
    if not pt.exists(outdir):
        os.makedirs(outdir)
    for name in ('train', 'val'):
        print(name)
        printer = IntervalPrinter()
        datadir = pt.join(indir, name)
        gen = __yield_ilsvrc2012_metadata(name, shuffle)
        lock = th.Lock()
        with FileWriter(pt.join(outdir, name + '.msgpack')) as writer:
            def write_image(item):
                filename, label = item
                path = pt.join(datadir, filename)
                with io.FileIO(path) as f:
                    data = __verify_image(f.read(), compress)
                    image = ImageClassificationData(
                        data,
                        int(label),
                        filename,
                    )
                with lock:
                    writer.write(image)
                printer.update()
            pool = ThreadPool(cpu_count()*4)
            result = pool.map_async(write_image, gen)
            while not result.ready():
                result.wait(1000)
        printer.print_total_updates()


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'indir',
        metavar='INPATH',
        help='directory that contains ILSRCV 2012 image directories and lists'
    )
    parser.add_argument(
        '-o', '--outdir',
        metavar='OUTPATH',
        help='output directory; defaults to indir'
    )
    parser.add_argument(
        '--compress',
        action='store_true',
        help='recompress images as JPEG with quality 85 and 422 color '
             'subsampling'
    )
    args = parser.parse_args()
    outdir = args.outdir or args.indir
    write_sets(args.indir, outdir, compress=args.compress)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
