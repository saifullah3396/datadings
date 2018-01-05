"""Create ILSVRC 2012 data set files.

The data set is described here:
    http://image-net.org/challenges/LSVRC/2012/index

The tar files needs to be unpacked.

Also download and unpack additional files provided by Caffe:
    https://github.com/BVLC/caffe/tree/master/data/ilsvrc12
"""
from __future__ import print_function

import threading as th
import os
import os.path as pt
import io
import random
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import cpu_count

from PIL import Image

from ..writer import FileWriter
from . import ImageClassificationData
from ..tools import IntervalPrinter


def __yield_ilsvrc2012_metadata(txtpath, shuffle):
    import codecs
    import csv
    with codecs.open(txtpath, encoding='utf8') as f:
        items = csv.reader(f, delimiter=' ')
        if shuffle:
            items = list(items)
            random.shuffle(items)
        for item in items:
            yield item


def __verify_image(data):
    buf = io.BytesIO(data)
    Image.open(buf).load()


def write_sets(indir, outdir, shuffle=True):
    for name in ('train', 'val'):
        print(name)
        printer = IntervalPrinter()
        datadir = pt.join(indir, name)
        gen = __yield_ilsvrc2012_metadata(
            pt.join(indir, name + '.txt'),
            shuffle,
        )
        lock = th.Lock()
        with FileWriter(pt.join(outdir, name + '.msgpack')) as writer:
            def write_image(item):
                filename, label = item
                path = pt.join(datadir, filename.replace('/', os.sep))
                with io.FileIO(path) as f:
                    data = f.read()
                    __verify_image(data)
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
    args = parser.parse_args()
    outdir = args.outdir or args.indir
    write_sets(args.indir, outdir)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
