"""Create CityScapes data set files.

This tool will look for the following files in the input directory:

- disparity_trainvaltest.zip
- gtFine_trainvaltest.zip
- leftImg8bit_trainvaltest.zip

Note:
    Registration is required to download this dataset.
    Please visit the website to download it.

See also:
    https://www.cityscapes-dataset.com/
"""
import os.path as pt
import zipfile
import random

from ..writer import FileWriter
from ..tools import yield_threaded
from . import ImageDisparitySegmentationData
from ..tools import document_keys


__doc__ += document_keys(ImageDisparitySegmentationData)


FILES = {
    'left': {
        'path': 'leftImg8bit_trainvaltest.zip',
        'md5': '0a6e97e94b616a514066c9e2adb0c97f',
    },
    'disparity': {
        'path': 'disparity_trainvaltest.zip',
        'md5': '2c8272766993c983321f34c73daada5c',
    },
    'gt': {
        'path': 'gtFine_trainvaltest.zip',
        'md5': '4237c19de34c8a376e9ba46b495d6f66',
    },
}


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


def write_sets(files, outdir, args):
    def z(file):
        return zipfile.ZipFile(files[file]['path'])
    with z('left') as left, z('disparity') as disparity, z('gt') as gt:
        for split in ('train', 'val', 'test'):
            keys = get_keys(left, split)
            if args.shuffle:
                random.shuffle(keys)
            gen = yield_threaded(yield_samples(keys, left, disparity, gt))
            write_set(outdir, split, gen, len(keys))


def main():
    from ..tools.argparse import make_parser
    from ..tools.argparse import argument_threads
    from ..tools import prepare_indir

    parser = make_parser(__doc__)
    argument_threads(parser)
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
