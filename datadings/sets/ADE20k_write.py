"""Create Vaihingen data set files.

The data set is described here:
    http://groups.csail.mit.edu/vision/datasets/ADE20K/ADE20K_2016_07_26.zip

This tool will look for the following files in the input directory
and download them if necessary:
    - ADE20K_2016_07_26.zip

"""
from __future__ import print_function, division

import os.path as pt
import zipfile
import io
import json

import numpy as np
from PIL import Image

from . import ImageSegmentationData
from ..writer import FileWriter
from ..tools import FrequencyPrinter
from ..tools import download_if_not_found
from ..matlab import loadmat
from ..matlab import iter_fields
from .VOC2012_write import imagedata_to_array
from .VOC2012_write import class_counts
from .VOC2012_write import sorted_values
from .ADE20k import WEIGHTS


DATASET_URL = 'http://groups.csail.mit.edu/vision/datasets/' \
              'ADE20K/ADE20K_2016_07_26.zip'
DATASET_FILE = 'ADE20K_2016_07_26.zip'


def load_index(imagezip):
    data = imagezip.read(pt.join('ADE20K_2016_07_26', 'index_ade20k.mat'))
    index = loadmat(data)['index']
    return {k: v for k, v in iter_fields(index)}


def get_classes(index):
    return np.concatenate(index['objectnames'][0, 0].flatten()).tolist()


def array_to_image(array, format, dtype, mode):
    im = Image.fromarray(array.astype(dtype), mode)
    bio = io.BytesIO()
    im.save(bio, format=format)
    return bio.getvalue()


def array_to_png16(array):
    return array_to_image(array, 'png', np.int32, 'I')


def segmentation_map(im):
    segmap = np.zeros(im.shape[:2], dtype=np.uint16)
    segmap[...] = im[:, :, 0] // 10
    segmap *= 256
    segmap += im[:, :, 1]
    return segmap


def imagedata_to_segpng(data):
    im = imagedata_to_array(data)
    segmap = segmentation_map(im)
    segpng = array_to_png16(segmap)
    return segpng


def instance_map(im):
    return im[:, :, 2]


def yield_images(names):
    prefixes = (n.rstrip('.jpg') for n in names if n.endswith('.jpg'))
    for p in prefixes:
        parts = []
        i = 0
        part = p + 'parts_%d.png' % i
        while part in names:
            parts.append(part)
            i += 1
            part = p + 'parts_%d.png' % i
        yield p + '.jpg', p + '_seg.png', parts


def write_set(imagezip, outdir, name, classes, class_weights):
    print(name)
    printer = FrequencyPrinter()
    with FileWriter(pt.join(outdir, name + '.msgpack')) as writer:
        for im, seg, parts in yield_images(imagezip.namelist()):
            if name not in im:
                continue
            imdata = imagezip.read(im)
            segdata = imagezip.read(seg)
            # partsdata = [imagezip.read(p) for p in parts]
            writer.write(ImageSegmentationData(
                imdata,
                imagedata_to_segpng(segdata),
                pt.basename(im),
                classes,
                class_weights
            ))
            printer.update()
    printer.print_total_updates()


def write_sets(indir, outdir):
    datapath = pt.join(indir, DATASET_FILE)
    download_if_not_found(DATASET_URL, datapath)
    with zipfile.ZipFile(datapath) as imagezip:
        index = load_index(imagezip)
        classes = get_classes(index)
        for name in ('training', 'validation'):
            write_set(imagezip, outdir, name, classes, WEIGHTS)


def _segmap(imagezip, path):
    return segmentation_map(imagedata_to_array(imagezip.read(path)))


def calculate_weights(indir, outdir):
    datapath = pt.join(indir, DATASET_FILE)
    download_if_not_found(DATASET_URL, datapath)
    with zipfile.ZipFile(datapath) as imagezip:
        gen = (
            _segmap(imagezip, path)
            for _, seg, parts in yield_images(imagezip.namelist())
            if 'training' in seg
            for path in parts + [seg]
        )
        counts = class_counts(gen)
    with open(pt.join(outdir, 'ADE20k_counts.json'), 'w') as f:
        json.dump({
            'INDEXES': sorted(counts.keys()),
            'COUNTS': sorted_values(counts)
        }, f)


def extract_scenelabels(indir, outdir):
    datapath = pt.join(indir, DATASET_FILE)
    download_if_not_found(DATASET_URL, datapath)
    with zipfile.ZipFile(datapath) as imagezip:
        index = load_index(imagezip)
        scenes = sorted(set(np.concatenate(index['scene'][0, 0][0])))
    with open(pt.join(outdir, 'ADE20k_scenelabels.json'), 'w') as f:
        json.dump(scenes, f)


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
        help='directory that contains Vaihingen Dataset files'
    )
    parser.add_argument(
        '-o', '--outdir',
        metavar='OUTPATH',
        help='output directory; defaults to indir'
    )
    parser.add_argument(
        '--calculate-weights',
        action='store_true',
        help='calculate median-frequency class weights'
    )
    parser.add_argument(
        '--scenelabels',
        action='store_true',
        help='extract list of scene labels'
    )
    args = parser.parse_args()
    outdir = args.outdir or args.indir
    if args.calculate_weights:
        calculate_weights(args.indir, outdir)
    elif args.scenelabels:
        extract_scenelabels(args.indir, outdir)
    else:
        write_sets(args.indir, outdir)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
