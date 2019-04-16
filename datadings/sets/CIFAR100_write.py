"""Create CIFAR 100 data set files.

The data set is described here:
    https://www.cs.toronto.edu/~kriz/cifar.html
"""
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

import tarfile
import os.path as pt
import random

from six.moves.cPickle import load

from ..tools import download_if_not_found
from ..writer import FileWriter
from .CIFAR100 import CIFAR100Data
from .CIFAR10_write import get_files
from .CIFAR10_write import row2image


def yield_rows(files):
    for f in files:
        d = load(f, encoding='bytes')
        for row, label, coarse_label, filename in zip(
                d[b'data'], d[b'fine_labels'],
                d[b'coarse_labels'], d[b'filenames']
        ):
            filename = filename.decode('utf-8')
            image = row2image(row)
            yield image, label, coarse_label, filename


def __write_sets(outdir, train_names, test_names, shuffle):
    for name, files in (('train', train_names), ('test', test_names)):
        gen = yield_rows(files)
        if shuffle:
            gen = list(gen)
            random.shuffle(gen)
        with FileWriter(pt.join(outdir, name + '.msgpack'), total=len(files)) as writer:
            for data, label, coarse_label, filename in gen:
                writer.write(CIFAR100Data(
                    data,
                    int(label),
                    int(coarse_label),
                    filename,
                ))


def write_sets(indir, outdir, shuffle=True):
    download_if_not_found(
        'https://www.cs.toronto.edu/~kriz/cifar-100-python.tar.gz',
        pt.join(indir, 'cifar-100-python.tar.gz')
    )
    train_names = ['train']
    test_names = ['test']
    with tarfile.open(pt.join(indir, 'cifar-100-python.tar.gz'), 'r:gz') as tar:
        __write_sets(
            outdir,
            get_files(tar, 'cifar-100-python', train_names),
            get_files(tar, 'cifar-100-python', test_names),
            shuffle
        )


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'indir',
        metavar='INPATH',
        help='directory that contains ILSRCV 2012 image directories and lists'
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
