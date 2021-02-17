"""Create RIT18 data set files.

This tool will look for the following files in the input directory
and download them if necessary:

- rit18_data.mat

See also:
    https://github.com/rmkemker/RIT-18

Warning:
    Images, labels, and masks are numpy arrays, not images!

"""
import os.path as pt
import numpy as np

from ..writer import FileWriter
from . import MaskedImageSegmentationData
from .RIT18 import CROP_SIZE
from ..tools.matlab import loadmat
from ..tools import split_array
from ..tools import document_keys


__doc__ += document_keys(MaskedImageSegmentationData)


FILES = {
    'mat': {
        'path': 'rit18_data.mat',
        'url': 'http://www.cis.rit.edu/~rmk6217/rit18_data.mat',
        'md5': '783ffe651310352e9c09b8ac389876c7',
    }
}


def write(writer, img, labels, mask, filename):
    writer.write(MaskedImageSegmentationData(
        filename,
        img,
        labels,
        mask,
    ))


def write_train(outdir, dataset, args):
    # Training-Split -> give whole image
    train_labels = dataset['train_labels'].astype(np.int64)
    train_data = dataset['train_data']
    train_mask = train_data[-1].astype(np.uint8)
    train_img = train_data[:6].astype(np.uint16)
    outfile = pt.join(outdir, 'train.msgpack')
    with FileWriter(outfile, total=1, overwrite=args.no_confirm) as writer:
        write(writer, train_img, train_labels, train_mask, "train")


def write_set(outdir, split, labels, data, args, crop_size):
    # Validation & Test-Split -> give splitted images
    labels = np.expand_dims(labels, axis=0)
    gen = enumerate(zip(split_array(data, *crop_size),
                        split_array(labels, *crop_size)))

    outfile = pt.join(outdir, split + '.msgpack')
    with FileWriter(outfile, overwrite=args.no_confirm) as writer:
        for idx, (sub_data, sub_label) in gen:
            sub_label = np.array(sub_label[0]).astype(np.int64)  # squeeze again!
            sub_mask = np.array(sub_data[-1]).astype(np.uint8)
            sub_img = np.array(sub_data[:6]).astype(np.uint16)
            write(writer, sub_img, sub_label, sub_mask, "%s_%s" % (split, idx))


def write_sets(files, outdir, args, crop_size=(CROP_SIZE, CROP_SIZE)):
    dataset = loadmat(files['mat']['path'])

    try:
        write_train(outdir, dataset, args)
    except FileExistsError:
        pass

    for split in ("val",):
        data = dataset['%s_data' % (split,)]
        if split == "val":
            labels = dataset['val_labels']
        else:
            labels = np.zeros(np.array(data).shape)
        try:
            write_set(outdir, split, labels, data, args, crop_size)
        except FileExistsError:
            pass


def main():
    from ..tools.argparse import make_parser
    from ..tools import prepare_indir

    parser = make_parser(__doc__, shuffle=False)
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
