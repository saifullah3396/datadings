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
import os.path as pt
import gzip
import tarfile
import io
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import cpu_count

import numpy as np
from PIL import Image
from simplejpeg import decode_jpeg
from simplejpeg import decode_jpeg_header
from simplejpeg import encode_jpeg as encode_jpeg

from ..writer import FileWriter
from ..tools import verify_files
from ..tools import yield_threaded
from . import ImageClassificationData
from .ILSVRC2012_synsets import SYNSETS


FILES = {
    'train': {
        'url': None,
        'path': 'ILSVRC2012_img_train.tar',
        'md5': '1d675b47d978889d74fa0da5fadfb00e',
    },
    'val': {
        'url': None,
        'path': 'ILSVRC2012_img_val.tar',
        'md5': '29b22e2961454d5413ddabcf34fc5622',
    },
}
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


def verify_image(
        data,
        quality=None,
        short_side=375,
        long_side=500,
        colorsubsampling='422',
):
    target_size = 3 * short_side * long_side

    # try to decode data using simplejpeg
    try:
        h, w, colorspace, _ = decode_jpeg_header(data)
        # decode images to match at least target size
        im = decode_jpeg(
            data,
            min_width=short_side if w < h else long_side,
            min_height=short_side if h < w else long_side
        )
        # encode quality is given
        # and image is big enough to not suffer from re-encoding
        compress = quality is not None and im.size > 0.5*target_size
    # simplejpeg could not decode image, fall back to Pillow
    # could be faulty JPEG or other image format, e.g. PNG
    except ValueError:
        bio = io.BytesIO(data)
        im = np.array(Image.open(bio).convert('RGB'))
        colorspace = 'RGB'  # converted to RGB guaranteed
        compress = True  # force compression since simplejpeg failed

    # if images are CMYK or
    if colorspace == 'CMYK' or compress:
        # for CMYK or non-JPEG images,
        # quality might not be given, so assume 99
        if quality is None:
            quality = 98
        # default to subsampling 422
        # use full color resolution for small images
        # or if compression is disabled,
        # i.e. for CMYK images or if simplejpeg failed to decode
        if not compress or im.size <= 0.5*target_size:
            colorsubsampling = '444'
        # downscale large images
        if im.size > target_size*1.5:
            h, w = im.shape[:2]
            s = max(h, w)
            r = long_side/s
            h, w = int(round(r*h)), int(round(r*w))
            pil = Image.fromarray(im, 'RGB')
            im = np.array(pil.resize((w, h), resample=Image.LANCZOS))
        return encode_jpeg(im, quality=quality, colorsubsampling=colorsubsampling)
    else:
        return data


TOTAL = {'train': 1281167, 'val': 50000, 'test': 100000}


def write_set(split, outdir, gen, quality, subsampling, threads):
    outfile = pt.join(outdir, split + '.msgpack')
    with FileWriter(outfile, total=TOTAL[split]) as writer:
        def __verify_inner(item):
            key, data, label = item
            data = verify_image(data, quality, colorsubsampling=subsampling)
            return ImageClassificationData(key, data, label)
        pool = ThreadPool(threads)
        for sample in pool.imap_unordered(__verify_inner, gen):
            writer.write(sample)


def write_sets(indir, outdir, quality, subsampling, threads, verification):
    if verification:
        verify_files(FILES, indir)
    for split in ('train', 'val'):
        tarpath = pt.join(indir, 'ILSVRC2012_img_%s.tar' % split)
        with tarfile.open(tarpath, bufsize=READ_SIZE) as tar:
            gen = yield_threaded(yield_samples(split, tar))
            write_set(split, outdir, gen, quality, subsampling, threads)


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
        "-s", "--skip-verification",
        action="store_true",
        help="If you're feeling lucky."
    )
    parser.add_argument(
        '-c', '--compress',
        nargs='?',
        default=None,
        const=85,
        choices=range(101),
        metavar='quality 0-100',
        type=int,
        help='use JPEG compression with optional quality; '
             'default quality is 85; '
             'big images are resized to roughly fit 500x375; '
             '444 color is forced for very small images'
    )
    parser.add_argument(
        '-s', '--subsampling',
        default='422',
        choices=('444', '422', '420', '440', '411', 'Gray'),
        type=str,
        help='color subsampling factor used with compress option'
    )
    cpus = cpu_count()
    default_cpu = min(8, cpus)
    parser.add_argument(
        '-t', '--threads',
        default=default_cpu,
        choices=range(cpus+1),
        metavar='0-%d' % cpus,
        type=int,
        help='number of threads used to verify images; '
             '0 uses all available CPUs; '
             'default is %d' % default_cpu
    )
    args = parser.parse_args()
    outdir = args.outdir or args.indir
    threads = args.threads
    threads = min(threads, cpus) if threads > 0 else cpus
    write_sets(
        args.indir,
        outdir,
        args.compress,
        args.subsampling,
        threads,
        not args.skip_verification,
    )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
