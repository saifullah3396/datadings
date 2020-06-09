"""Create CityScapes data set files.

The data set is described here:
    https://www.cityscapes-dataset.com/

This tool will look for the following files in the input directory:
    - disparity_trainvaltest.zip
    - gtFine_trainvaltest.zip
    - leftImg8bit_trainvaltest.zip

An account is required to download this dataset.
Please visit the website to download it.
"""
import os.path as pt
import zipfile

from ..writer import FileWriter
from ..tools import yield_threaded
from . import ImageDisparitySegmentationData


LEFT = 'leftImg8bit_trainvaltest.zip'
DISPARITY = 'disparity_trainvaltest.zip'
GT = 'gtFine_trainvaltest.zip'


def get_keys(leftzip, split):
    keys = [name.replace('_leftImg8bit.png', '').replace('leftImg8bit/', '')
            for name in leftzip.namelist()
            if name.endswith('_leftImg8bit.png')]
    return [key for key in keys if key.startswith(split)]


def yield_samples(keys, leftzip, disparityzip, gtzip):
    for key in keys:
        image = leftzip.read('leftImg8bit/' + key + '_leftImg8bit.png')
        label_image = gtzip.read('gtFine/' + key + '_gtFine_labelIds.png')
        disparity_image = disparityzip.read('disparity/' + key + '_disparity.png')
        yield key, image, label_image, disparity_image


def write_set(outdir, split, gen, total):
    outpath = pt.join(outdir, split + '.msgpack')
    with FileWriter(outpath, total=total) as writer:
        for sample in gen:
            writer.write(ImageDisparitySegmentationData(*sample))


def write_sets(indir, outdir):
    def z(path):
        return zipfile.ZipFile(pt.join(indir, path))
    with z(LEFT) as left, z(DISPARITY) as disparity, z(GT) as gt:
        for split in ('train', 'val', 'test'):
            keys = get_keys(left, split)
            gen = yield_threaded(yield_samples(keys, left, disparity, gt))
            write_set(outdir, split, gen, len(keys))


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
        help='directory that contains Cityscapes files'
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
