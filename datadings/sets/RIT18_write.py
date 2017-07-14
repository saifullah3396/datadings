"""Create RIT18 data set files.

The data set is described here:
    https://github.com/rmkemker/RIT-18

This tool will look for the following files in the input directory
and download them if necessary:
    - rit18_data.mat

"""
from __future__ import print_function, division

import os.path as pt
import numpy as np

from datadings.writer import FileWriter
from datadings.tools import FrequencyPrinter
from datadings.tools import download_if_not_found
from datadings.sets import MaskedSegmentationData
from datadings.sets.RIT18 import CLASSES
from datadings.sets.RIT18 import CROP_SIZE
from datadings.matlab import loadmat
from itertools import product


def pack_array(arr):
    return arr.dtype.char, arr.shape, arr.tobytes()


def split_array(img, h_pixels, v_pixels):
    i_ = np.arange(img.shape[1]) // v_pixels
    j_ = np.arange(img.shape[2]) // h_pixels
    for i, j in product(np.unique(i_), np.unique(j_)):
        yield img[:, i_ == i][:, :, j_ == j]


def write(outpath, img, labels, mask, filename=""):
    with FileWriter(outpath) as writer:
        item = MaskedSegmentationData(
            pack_array(img),
            pack_array(labels),
            pack_array(mask),
            filename,
            CLASSES,
            [1] * len(CLASSES),
        )
        writer.write(item)


def write_sets(indir, outdir, crop_size=(CROP_SIZE, CROP_SIZE)):
    imagepath = pt.join(indir, 'rit18_data.mat')
    download_if_not_found(
        'http://www.cis.rit.edu/~rmk6217/rit18_data.mat',
        imagepath
    )
    printer = FrequencyPrinter()
    dataset = loadmat(imagepath)

    # Training-Split -> give whole image
    train_labels = dataset['train_labels'].astype(np.int64)
    train_data = dataset['train_data']
    train_mask = train_data[-1].astype(np.uint8)
    train_img = train_data[:6].astype(np.uint16)

    write(pt.join(outdir, 'RIT18_train.msgpack'),
          train_img, train_labels, train_mask)
    printer.update()

    # Validation & Test-Split -> give splitted images
    for split in ("val", "test"):
        data = dataset['%s_data' %(split)]
        if split == "val":
            labels = dataset['val_labels']
        else:
            labels = np.zeros(np.array(data).shape)

        labels = np.expand_dims(labels, axis=0)
        for sub_data, sub_label in zip(split_array(data, *crop_size),
                                       split_array(labels, *crop_size)):
            sub_label = sub_label[0] # squeeze again!
            sub_mask = sub_data[-1]
            sub_img = sub_data[:6]
            write(pt.join(outdir, 'RIT18_%s.msgpack' %(split)),
                  sub_img, sub_label, sub_mask)
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
        help='directory that contains RIT18.mat file'
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
