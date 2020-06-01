"""Create RIT18 data set files.

The data set is described here:
    https://github.com/rmkemker/RIT-18

This tool will look for the following files in the input directory
and download them if necessary:
    - rit18_data.mat

"""
import os.path as pt
import numpy as np

from ..writer import FileWriter
from ..tools import download_if_not_found
from . import MaskedImageSegmentationData
from .RIT18 import CLASSES
from .RIT18 import CROP_SIZE
from ..matlab import loadmat
from ..tools import split_array


def write(writer, img, labels, mask, filename=""):
    item = MaskedImageSegmentationData(
        img,
        labels,
        mask,
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
    dataset = loadmat(imagepath)

    # Training-Split -> give whole image
    train_labels = dataset['train_labels'].astype(np.int64)
    train_data = dataset['train_data']
    train_mask = train_data[-1].astype(np.uint8)
    train_img = train_data[:6].astype(np.uint16)

    with FileWriter(pt.join(outdir, 'RIT18_train.msgpack')) as writer:
        write(writer, train_img, train_labels, train_mask, "train")

    # Validation & Test-Split -> give splitted images
    for split in ("val", ):
        file = pt.join(outdir, 'RIT18_%s.msgpack' % (split))
        with FileWriter(file) as writer:

            data = dataset['%s_data' %(split)]
            if split == "val":
                labels = dataset['val_labels']
            else:
                labels = np.zeros(np.array(data).shape)

            labels = np.expand_dims(labels, axis=0)
            for idx, (sub_data, sub_label) in \
                    enumerate(zip(split_array(data, *crop_size),
                                  split_array(labels, *crop_size))):
                sub_label = np.array(sub_label[0]).astype(np.int64)  # squeeze again!
                sub_mask = np.array(sub_data[-1]).astype(np.uint8)
                sub_img = np.array(sub_data[:6]).astype(np.uint16)
                write(writer, sub_img, sub_label, sub_mask, "%s_%s" % (split, idx))


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
