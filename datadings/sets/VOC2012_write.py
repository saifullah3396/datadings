"""Create CAMVID data set files.

The adaptation of the data set is described here:
    https://github.com/alexgkendall/SegNet-Tutorial

This tool will look for the following files in the input directory
and download them if necessary:
    - VOCtrainval_11-May-2012.tar from
          http://host.robots.ox.ac.uk/pascal/VOC/voc2012/
          VOCtrainval_11-May-2012.tar
"""
from __future__ import print_function, division

import os.path as pt
import tarfile
import random
import io
from PIL import Image
from collections import defaultdict

import numpy as np

from datadings.writer import FileWriter
from datadings.tools import FrequencyPrinter
from datadings.tools import download_if_not_found
from datadings.tools import print_over
from datadings.sets import SegmentationData
from datadings.sets.VOC2012 import CLASSES
from datadings.sets.VOC2012 import M


def calculate_weights(tar):
    printer = FrequencyPrinter()
    weights = defaultdict(lambda: 0)
    for m in tar.getmembers():
        if 'SegmentationClass' not in m.path \
                or not m.path.endswith('.png'):
            continue
        segim = imagedata_to_array(extractmember(tar, m))
        segmap = map_color_image(segim)
        counts = np.bincount(segmap.flatten())
        for c in np.nonzero(counts)[0]:
            weights[c] += counts[c]
        printer.update()
    print_over('%d samples analyzed' % printer.total_updates)
    total = sum(weights.values())
    freq = {c: n/total for c, n in weights.items()}
    median_freq = np.median(list(freq.values()))
    # cannot serialize numpy scalars,
    # classes & weights must be Python numbers!
    weights = {int(c): float(median_freq/f) for c, f in freq.items()}
    return weights


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

MSINGLE = single_value(M)


def map_color_image(im):
    im = single_value(im)
    h, w = im.shape
    im = im.reshape((h, w, 1))
    m = MSINGLE.reshape((1, 1, -1))
    return (im == m).argmax(axis=2).astype(np.uint8)


def write_image(writer, filename, im, seg):
    seg = imagedata_to_array(seg)
    seg = map_color_image(seg, )
    seg = array_to_imagedata(seg, 'PNG')
    item = SegmentationData(
        im,
        seg,
        filename,
        CLASSES,
        [1]*len(CLASSES),
    )
    writer.write(item)


def extract(tar, path):
    return extractmember(tar, tar.getmember(path))


def extractmember(tar, member):
    with tar.extractfile(member) as f:
        return f.read()


def get_imageset(tar, path):
    return extract(tar, path).decode('utf-8').strip('\n').split('\n')


def write_sets(indir, outdir, shuffle=True):
    datapath = pt.join(indir, 'VOCtrainval_11-May-2012.tar')
    download_if_not_found(
        'http://host.robots.ox.ac.uk/pascal/VOC/voc2012/'
        'VOCtrainval_11-May-2012.tar',
        datapath
    )
    root_dir = pt.join('VOCdevkit', 'VOC2012')
    sets_dir = pt.join(root_dir, 'ImageSets', 'Segmentation')
    image_dir = pt.join(root_dir, 'JPEGImages')
    seg_dir = pt.join(root_dir, 'SegmentationClass')
    with tarfile.TarFile(datapath) as tar:
        # weights = calculate_weights(tar)
        for split in ('train', 'val'):
            print(split)
            printer = FrequencyPrinter()
            outpath = pt.join(outdir, 'VOC2012_%s.msgpack' % split)
            with FileWriter(outpath) as writer:
                sets_path = pt.join(sets_dir, '%s.txt' % split)
                images = get_imageset(tar, sets_path)
                if shuffle:
                    random.shuffle(images)
                for name in images:
                    im = extract(tar, pt.join(image_dir, name) + '.jpg')
                    seg = extract(tar, pt.join(seg_dir, name) + '.png')
                    write_image(writer, name, im, seg)
                    printer.update()
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
        default='.',
        help='directory that contains MIT1003 archives'
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
