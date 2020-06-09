"""Create CAMVID data set files.

The adaptation of the data set is described here:
    https://github.com/alexgkendall/SegNet-Tutorial

This tool will look for the following files in the input directory
and download them if necessary:
    - CAMVID.zip from:
        https://github.com/alexgkendall/SegNet-Tutorial/
        archive/fcaf7c4978dd8d091ec67db7cb7fdd225f5051c5.zip
"""
import os.path as pt
import zipfile
import random
import io
import numpy as np

from PIL import Image

from .VOC2012_write import class_counts
from .VOC2012_write import sorted_values
from .VOC2012_write import print_values
from .VOC2012 import median_frequency_weights
from ..writer import FileWriter
from ..tools import download_if_not_found
from . import ImageSegmentationData


def imagedata_to_array(data):
    bio = io.BytesIO(data)
    im = Image.open(bio)
    return np.array(im)


def _prepare_indir(indir):
    datapath = pt.join(indir, 'CAMVID.zip')
    download_if_not_found(
        'https://github.com/alexgkendall/SegNet-Tutorial/'
        'archive/fcaf7c4978dd8d091ec67db7cb7fdd225f5051c5.zip',
        datapath
    )
    root_dir = 'SegNet-Tutorial-fcaf7c4978dd8d091ec67db7cb7fdd225f5051c5'
    pairs_dir = pt.join(root_dir, 'CamVid')
    return datapath, root_dir, pairs_dir


def write_image(imagezip, writer, inpath, outpath):
    indata = imagezip.read(inpath)
    outdata = imagezip.read(outpath)
    filename = pt.basename(inpath)
    item = ImageSegmentationData(
        filename,
        indata,
        outdata,
    )
    writer.write(item)


def _get_pairs(fp, root_dir):
    return [
        pair.decode('utf-8').rstrip().replace('/SegNet', root_dir).split()
        for pair in fp
    ]


def write_sets(indir, outdir, shuffle=True):
    datapath, root_dir, pairs_dir = _prepare_indir(indir)
    with zipfile.ZipFile(datapath) as imagezip:
        for split in ('test', 'val', 'train'):
            outpath = pt.join(outdir, 'CAMVID_%s.msgpack' % split)
            pairs_path = pt.join(pairs_dir, '%s.txt' % split)
            pairs = _get_pairs(imagezip.open(pairs_path), root_dir)
            with FileWriter(outpath, total=len(pairs)) as writer:
                if shuffle:
                    random.shuffle(pairs)
                for pair in pairs:
                    write_image(imagezip, writer, *pair)


def _segmap(imagezip, path):
    return imagedata_to_array(imagezip.read(path))


def calculate_weights(indir):
    datapath, root_dir, pairs_dir = _prepare_indir(indir)
    with zipfile.ZipFile(datapath) as imagezip:
        for split in ('test', 'val', 'train'):
            print(split, 'weights')
            pairs_path = pt.join(pairs_dir, '%s.txt' % split)
            pairs = _get_pairs(imagezip.open(pairs_path), root_dir)
            gen = (_segmap(imagezip, path) for _, path in pairs)
            counts = class_counts(gen)
            weights = median_frequency_weights(counts)
            print_values('INDEXES', sorted(counts))
            print_values('COUNTS', sorted_values(counts))
            print_values('WEIGHTS', sorted_values(weights))


def main():
    from datadings.argparse import make_parser
    from datadings.argparse import argument_indir
    from datadings.argparse import argument_outdir
    from datadings.argparse import argument_calculate_weights

    parser = make_parser(__doc__)
    argument_indir(parser)
    argument_outdir(parser)
    argument_calculate_weights(parser)
    args = parser.parse_args()
    outdir = args.outdir or args.indir
    if args.calculate_weights:
        calculate_weights(args.indir)
    else:
        write_sets(args.indir, outdir)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
