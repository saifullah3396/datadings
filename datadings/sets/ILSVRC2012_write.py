"""Create ILSVRC 2012 data set files.

The data set is described here:
    http://image-net.org/challenges/LSVRC/2012/index

The tar files need to be unpacked.
"""
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

import threading as th
import os
import os.path as pt
import io
import gzip
import random
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import cpu_count

import numpy as np
from PIL import Image
from simplejpeg import decode_jpeg
from simplejpeg import decode_jpeg_header
from simplejpeg import encode_jpeg as encode_jpeg

from ..writer import FileWriter
from . import ImageClassificationData


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


def verify_image(data, quality=None, normal_size=3*375*500, long_side=500):
    im = decode_jpeg(data)
    _, _, colorspace, _ = decode_jpeg_header(data)
    # if images are CMYK or encode quality is given and they are big enough
    if colorspace == 'CMYK' or (quality is not None and im.size > 0.5*normal_size):
        # for CMYK images, quality might not be given, so assume 99
        if quality is None:
            quality = 99
        # default to subsampling 422
        # use full color resolution for small images
        colorsubsampling = '422'
        if im.size <= 0.5*normal_size:
            colorsubsampling = '444'
        # downscale large images
        if im.size > normal_size*1.5:
            h, w = im.shape[:2]
            s = max(h, w)
            r = long_side/s
            h, w = int(round(r*h)), int(round(r*w))
            pil = Image.fromarray(im, 'RGB')
            im = np.array(pil.resize((w, h), resample=Image.LANCZOS))
        return encode_jpeg(im, quality=quality, colorsubsampling=colorsubsampling)
    else:
        return data


TOTAL = {'train': 1280000, 'val': 50000, 'test': 100000}


def write_sets(indir, outdir, shuffle=True, compress=False):
    if not pt.exists(outdir):
        os.makedirs(outdir)
    quality = 85 if compress else None
    for name in ('val', 'train', ):
        datadir = pt.join(indir, name)
        gen = __yield_ilsvrc2012_metadata(name, shuffle)
        lock = th.Lock()
        with FileWriter(pt.join(outdir, name + '.msgpack'), total=TOTAL[name]) as writer:
            def write_image(item):
                filename, label = item
                path = pt.join(datadir, filename)
                with io.FileIO(path) as f:
                    data = verify_image(f.read(), quality)
                    image = ImageClassificationData(
                        data,
                        int(label),
                        filename,
                    )
                with lock:
                    writer.write(image)
            pool = ThreadPool(cpu_count()*4)
            result = pool.map_async(write_image, gen)
            while not result.ready():
                result.wait(1000)


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
        metavar='OUTDIR',
        help='output directory; defaults to indir'
    )
    parser.add_argument(
        '--compress',
        action='store_true',
        help='recompress images as JPEG with q=85 and 422 color subsampling'
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
