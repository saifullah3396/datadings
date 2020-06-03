"""Create ILSVRC 2012 data set files.

The data set is described here:
    http://image-net.org/challenges/LSVRC/2012/index

Important:
    For performance reasons shuffling is not available.
    You can use datadings-shuffle to create a shuffled copy.

This tool will look for the following files in the input directory:
    - ILSVRC2012_img_train.tar
    - ILSVRC2012_img_val.tar

Registration is required to download this dataset.
Please visit the website to download it.
"""
import threading as th
import os.path as pt
import gzip
import tarfile
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import cpu_count

import numpy as np
from PIL import Image
from simplejpeg import decode_jpeg
from simplejpeg import decode_jpeg_header
from simplejpeg import encode_jpeg as encode_jpeg

from ..writer import FileWriter
from . import ImageClassificationData
from .ILSVRC2012_synsets import SYNSETS


SET_ROOT = pt.abspath(pt.dirname(__file__))
READ_SIZE = 4 * 1024 * 1024


def yield_train(tar):
    for synset in tar:
        label = SYNSETS[pt.splitext(synset.name)[0]]
        with tarfile.open(fileobj=tar.extractfile(synset),
                          bufsize=READ_SIZE) as images:
            for image in images:
                yield image.name, images.extractfile(image).read(), label


def yield_val(tar):
    path = pt.join(SET_ROOT, 'ILSVRC2012_val.txt.gz')
    with gzip.open(path, 'rt', encoding='utf8') as f:
        labels = dict(l.strip('\n').split(' ', 1) for l in f)
    for image in tar:
        yield image.name, tar.extractfile(image).read(), labels[image.name]


def yield_samples(split, tar):
    if split == 'train':
        return yield_train(tar)
    elif split == 'val':
        return yield_val(tar)
    elif split == 'test':
        raise ValueError('test set not supported')


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


def write_set(split, outdir, gen, compress):
    quality = 85 if compress else None
    lock = th.Lock()
    outfile = pt.join(outdir, split + '.msgpack')
    with FileWriter(outfile, total=TOTAL[split]) as writer:
        def write_image(item):
            key, data, label = item
            data = verify_image(data, quality)
            image = ImageClassificationData(data, label, key)
            with lock:
                writer.write(image)
        pool = ThreadPool(min(8, cpu_count()))
        result = pool.map_async(write_image, gen)
        while not result.ready():
            result.wait(1000)


def write_sets(indir, outdir, compress=False):
    for split in ('val', 'train', ):
        tarpath = pt.join(indir, 'ILSVRC2012_img_%s.tar' % split)
        with tarfile.open(tarpath, bufsize=READ_SIZE) as tar:
            gen = yield_samples(split, tar)
            write_set(split, outdir, gen, compress)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'indir',
        metavar='INPATH',
        help='directory that contains ILSRCV 2012 tar files'
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
