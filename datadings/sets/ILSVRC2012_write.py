"""Create ILSVRC 2012 data set files.

Download and unpack the image archives found here:
    http://image-net.org/challenges/LSVRC/2012/index

Also download and unpack additional files provided by Caffe:
    https://github.com/BVLC/caffe/tree/master/data/ilsvrc12"""

import sys
import threading as th
import os
import os.path as pt
import io
import random
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import cpu_count

from PIL import Image

from datadings.writer import ImageWriter
from datadings.sets import ClassificationData
from datadings.tools import FrequencyPrinter


def __yield_ilsvrc2012_metadata(txtpath, shuffle=True):
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


def write_ilsvrc2012(indir, outdir):
    for name in ('train', 'val'):
        print(name)
        printer = FrequencyPrinter()
        datadir = pt.join(indir, name)
        sys.stdout.flush()
        gen = __yield_ilsvrc2012_metadata(pt.join(indir, name + '.txt'))
        lock = th.Lock()
        with ImageWriter(pt.join(outdir, name + '.msgpack')) as packer:
            def write_image(item):
                filename, label = item
                path = pt.join(datadir, filename.replace('/', os.sep))
                with io.FileIO(path) as f:
                    data = f.read()
                    __verify_image(data)
                    image = ClassificationData(
                        data,
                        int(label),
                        filename,
                    )
                with lock:
                    packer.write(image)
                printer.update()
            pool = ThreadPool(cpu_count()*4)
            result = pool.map_async(write_image, gen)
            while not result.ready():
                result.wait(1000)
        print()


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
    try:
        write_ilsvrc2012(args.indir, outdir)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
