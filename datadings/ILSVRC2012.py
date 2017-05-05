from __future__ import print_function, division

import os
import os.path as pt
from collections import namedtuple
import codecs
import csv
import io
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import cpu_count
import threading as th

from PIL import Image

from datadings import ImageWriter
from datadings import Reader
from datadings.tools import FrequencyPrinter


ILSVRC2012Image = namedtuple(
    'ILSVRC2012Image',
    ('label', 'dimensions', 'filename')
)


def convert_ilsvrc2012(item):
    jpegdata, image = item
    image = ILSVRC2012Image(*image)
    return jpegdata, image


class ILSVRC2012Reader(Reader):
    _convert = convert_ilsvrc2012


class ILSVRC2012Writer(ImageWriter):
    pass


def yield_ilsvrc2012_metadata(txtpath):
    with codecs.open(txtpath, encoding='utf8') as f:
        for path, label in csv.reader(f, delimiter=' '):
            yield ILSVRC2012Image(int(label), (0, 0),  path)


def __get_dimensions(jpegdata):
    buf = io.BytesIO(jpegdata)
    return Image.open(buf).size


def write_ilsvrc2012(indir, outdir):
    import sys
    for name in ('train', 'val'):
        printer = FrequencyPrinter()
        datadir = pt.join(indir, name)
        sys.stdout.flush()
        gen = yield_ilsvrc2012_metadata(pt.join(indir, name + '.txt'))
        lock = th.Lock()
        with ILSVRC2012Writer(pt.join(outdir, name + '.msgpack')) as packer:
            def write_image(image):
                path = pt.join(datadir, image.filename.replace('/', os.sep))
                with io.FileIO(path) as f:
                    jpegdata = f.read()
                image = ILSVRC2012Image(
                    image.label,
                    __get_dimensions(jpegdata),
                    image.filename,
                )
                with lock:
                    packer.write(jpegdata, image)
                printer.update()
            pool = ThreadPool(cpu_count()*4)
            result = pool.map_async(write_image, gen)
            while not result.ready():
                result.wait(1000)
        print('done.')


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'indir',
        metavar='INPATH',
        help='directory that contains iSUN mat and zip files'
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
