"""Create Pascal VOC 2012 dataset files.

This tool will look for the following files in the input directory
and download them if necessary:

- VOCtrainval_11-May-2012.tar

See also:
    http://host.robots.ox.ac.uk/pascal/VOC/voc2012/
"""
import os.path as pt
import tarfile
import random
import io
from PIL import Image

import numpy as np

from ..writer import FileWriter
from ..tools import make_printer
from . import ImageSegmentationData
from .VOC2012 import COLORS
from ..tools import document_keys


__doc__ += document_keys(ImageSegmentationData)


BASE_URL = 'http://host.robots.ox.ac.uk/pascal/VOC/voc2012/'
FILES = {
    'trainval': {
        'url': BASE_URL+'VOCtrainval_11-May-2012.tar',
        'path': 'VOCtrainval_11-May-2012.tar',
        'md5': '6cd6e144f989b92b3379bac3b3de84fd',
    },
}
TOTAL = {
    'train': 1464,
    'val': 1449,
}


def imagedata_to_array(data):
    bio = io.BytesIO(data)
    im = Image.open(bio).convert('RGB')
    return np.array(im)


def array_to_imagedata(im, format, **kwargs):
    bio = io.BytesIO()
    Image.fromarray(im, 'L').save(bio, format, **kwargs)
    return bio.getvalue()


def single_value(a):
    s = a.shape[:-1]
    b = np.zeros(s, dtype=np.uint32)
    np.bitwise_or(b, a[..., 0], out=b)
    np.left_shift(b, 8, out=b)
    np.bitwise_or(b, a[..., 1], out=b)
    np.left_shift(b, 8, out=b)
    np.bitwise_or(b, a[..., 2], out=b)
    return b


MSINGLE = single_value(COLORS)


def map_color_image(im):
    im = single_value(im)
    h, w = im.shape
    im = im.reshape((h, w, 1))
    m = MSINGLE.reshape((1, 1, -1))
    return (im == m).argmax(axis=2).astype(np.uint8)


def write_image(writer, filename, im, seg):
    seg = imagedata_to_array(seg)
    seg = map_color_image(seg)
    seg = array_to_imagedata(seg, 'PNG', optimize=True)
    writer.write(ImageSegmentationData(
        filename,
        im,
        seg,
    ))


def extract(tar, path):
    return extractmember(tar, tar.getmember(path))


def extractmember(tar, member):
    return tar.extractfile(member).read()


def get_imageset(tar, path):
    return extract(tar, path).decode('utf-8').strip('\n').split('\n')


def _prepare_indir():
    root_dir = pt.join('VOCdevkit', 'VOC2012')
    sets_dir = pt.join(root_dir, 'ImageSets', 'Segmentation')
    image_dir = pt.join(root_dir, 'JPEGImages')
    seg_dir = pt.join(root_dir, 'SegmentationClass')
    return sets_dir, image_dir, seg_dir


def write_set(tar, split, outdir, args):
    sets_dir, image_dir, seg_dir = _prepare_indir()
    outpath = pt.join(outdir, split+'.msgpack')
    with FileWriter(outpath, total=TOTAL[split],
                    overwrite=args.no_confirm) as writer:
        sets_path = pt.join(sets_dir, '%s.txt' % split)
        images = get_imageset(tar, sets_path)
        if args.shuffle:
            random.shuffle(images)
        for name in images:
            im = extract(tar, pt.join(image_dir, name) + '.jpg')
            seg = extract(tar, pt.join(seg_dir, name) + '.png')
            write_image(writer, name, im, seg)


def write_sets(files, outdir, args):
    with tarfile.TarFile(files['trainval']['path']) as tar:
        for split in ('train', 'val'):
            try:
                write_set(tar, split, outdir, args)
            except FileExistsError:
                pass


def class_counts(gen, **kwargs):
    counts = np.float64([])
    printer = make_printer(desc='class counts', **kwargs)
    with printer:
        for segmap in gen:
            printer()
            cs = np.bincount(segmap.ravel()).astype(np.float64) / segmap.size
            if len(cs) <= len(counts):
                counts[:len(cs)] += cs
            else:
                cs[:len(counts)] += counts
                counts = cs
    print('%d samples analyzed' % printer.n)
    counts = {int(c): float(counts[c]) for c in np.nonzero(counts)[0]}
    return counts


def print_values(prefix, values):
    print('%s = [' % prefix)
    for v in values:
        print('    {},'.format(v))
    print(']')


def sorted_values(d):
    return [d[k] for k in sorted(d)]


def _segmap(tar, seg_dir, name):
    return map_color_image(
        imagedata_to_array(
            extract(tar, pt.join(seg_dir, name) + '.png')
        )
    )


def calculate_set_weights(files):
    sets_dir, _, seg_dir = _prepare_indir()
    with tarfile.TarFile(files['trainval']['path']) as tar:
        for split in ('train', 'val'):
            print(split, 'weights')
            sets_path = pt.join(sets_dir, '%s.txt' % split)
            images = get_imageset(tar, sets_path)
            gen = (_segmap(tar, seg_dir, name) for name in images)
            counts = class_counts(gen)
            print_values('INDEXES', sorted(counts))
            print_values('COUNTS', sorted_values(counts))


def main():
    from ..tools.argparse import make_parser
    from ..tools.argparse import argument_calculate_weights
    from ..tools import prepare_indir

    parser = make_parser(__doc__)
    argument_calculate_weights(parser)
    args = parser.parse_args()
    outdir = args.outdir or args.indir

    files = prepare_indir(FILES, args)

    if args.calculate_weights:
        calculate_set_weights(files)
    else:
        write_sets(files, outdir, args)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
