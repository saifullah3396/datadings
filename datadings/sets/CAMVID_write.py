"""Create CamVid data set files.

This tool will look for the following files in the input directory
and download them if necessary:

- CamVid.zip (https://github.com/alexgkendall/SegNet-Tutorial/archive/fcaf7c4978dd8d091ec67db7cb7fdd225f5051c5.zip)

See also:
    - http://mi.eng.cam.ac.uk/research/projects/VideoRec/CamVid/
    - https://github.com/alexgkendall/SegNet-Tutorial
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
from . import ImageSegmentationData
from ..tools import document_keys


__doc__ += document_keys(ImageSegmentationData)


BASE_URL = 'https://github.com/alexgkendall/SegNet-Tutorial/archive/'
FILES = {
    'all': {
        'path': 'CamVid.zip',
        'url': BASE_URL+'fcaf7c4978dd8d091ec67db7cb7fdd225f5051c5.zip',
        'md5': '11a475a60ed3006379e8272a3aca9884',
    }
}
ROOT_DIR = 'SegNet-Tutorial-fcaf7c4978dd8d091ec67db7cb7fdd225f5051c5'
PAIRS_DIR = pt.join(ROOT_DIR, 'CamVid')


def imagedata_to_array(data):
    bio = io.BytesIO(data)
    im = Image.open(bio)
    return np.array(im)


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


def _get_pairs(fp):
    return [
        pair.decode('utf-8').rstrip().replace('/SegNet', ROOT_DIR).split()
        for pair in fp
    ]


def write_set(imagezip, outdir, split, files, args):
    outpath = pt.join(outdir, 'CAMVID_%s.msgpack' % split)
    pairs_path = pt.join(PAIRS_DIR, '%s.txt' % split)
    pairs = _get_pairs(imagezip.open(pairs_path))
    with FileWriter(outpath, total=len(pairs), overwrite=args.no_confirm) as writer:
        if args.shuffle:
            random.shuffle(pairs)
        for pair in pairs:
            write_image(imagezip, writer, *pair)


def write_sets(files, outdir, args):
    with zipfile.ZipFile(files['all']['path']) as imagezip:
        for split in ('test', 'val', 'train'):
            try:
                write_set(imagezip, outdir, split, files, args)
            except FileExistsError:
                pass


def _segmap(imagezip, path):
    return imagedata_to_array(imagezip.read(path))


def calculate_weights(files):
    with zipfile.ZipFile(files['all']['path']) as imagezip:
        for split in ('test', 'val', 'train'):
            print(split, 'weights')
            pairs_path = pt.join(PAIRS_DIR, '%s.txt' % split)
            pairs = _get_pairs(imagezip.open(pairs_path))
            gen = (_segmap(imagezip, path) for _, path in pairs)
            counts = class_counts(gen)
            weights = median_frequency_weights(counts)
            print_values('INDEXES', sorted(counts))
            print_values('COUNTS', sorted_values(counts))
            print_values('WEIGHTS', sorted_values(weights))


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
        calculate_weights(files)
    else:
        write_sets(files, outdir, args)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
