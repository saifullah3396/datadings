"""Create ILSVRC 2012 challenge data set files.

This tool will look for the following files in the input directory:

- ILSVRC2012_img_train.tar
- ILSVRC2012_img_val.tar

See also:
    http://image-net.org/challenges/LSVRC/2012/index

Note:
    Registration is required to download this dataset.
    Please visit the website to download it.

Important:
    For performance reasons samples are read in same order as they are stored
    in the source tar files. It is recommended to use the datadings-shuffle
    command to create a shuffled copy.
"""
import os.path as pt
import tarfile
import io
from multiprocessing.dummy import Pool as ThreadPool

import numpy as np
from PIL import Image
from simplejpeg import decode_jpeg
from simplejpeg import decode_jpeg_header
from simplejpeg import encode_jpeg as encode_jpeg

from ..writer import FileWriter
from .tools import open_comp
from ..tools import yield_threaded
from . import ImageClassificationData
from .ILSVRC2012_synsets import SYNSETS
from ..tools import document_keys


__doc__ += document_keys(ImageClassificationData)


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
    with open_comp('ILSVRC2012_val.txt.xz', 'rt', encoding='utf8') as f:
        labels = dict(line.strip('\n').split(' ', 1) for line in f)
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


def write_set(split, outdir, gen, args):
    outfile = pt.join(outdir, split + '.msgpack')

    def __verify_inner(item):
        key, data, label = item
        data = verify_image(data, args.compress, colorsubsampling=args.subsampling)
        return ImageClassificationData(key, data, label)

    pool = ThreadPool(args.threads)
    with FileWriter(outfile, total=TOTAL[split]) as writer:
        for sample in pool.imap_unordered(__verify_inner, gen):
            writer.write(sample)


def write_sets(files, outdir, args):
    for split in ('train', 'val'):
        with tarfile.open(files[split]['path'], bufsize=READ_SIZE) as tar:
            gen = yield_threaded(yield_samples(split, tar))
            write_set(split, outdir, gen, args)


def main():
    from ..tools.argparse import make_parser
    from ..tools.argparse import argument_threads
    from ..tools import prepare_indir

    parser = make_parser(__doc__, shuffle=False)
    argument_threads(parser, default=1)
    parser.add_argument(
        '--compress',
        nargs='?',
        default=None,
        const=85,
        choices=range(101),
        metavar='quality 0-100',
        type=int,
        help='Use JPEG compression with optional quality. '
             'Default quality is 85. '
             'Big images are resized to roughly fit 500x375. '
    )
    parser.add_argument(
        '--subsampling',
        default='422',
        choices=('444', '422', '420', '440', '411', 'Gray'),
        type=str,
        help='Color subsampling factor used with compress option. '
             '444 is forced for small images to preserve details.'
    )
    args = parser.parse_args()
    outdir = args.outdir or args.indir

    files = prepare_indir(FILES, args)

    write_sets(files, outdir, args)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
