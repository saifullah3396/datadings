"""Create CIFAR 10 data set files.

The data set is described here:
    https://www.cs.toronto.edu/~kriz/cifar.html
"""
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

import io
import os.path as pt
import random
import tarfile

from six.moves.cPickle import load

from PIL import Image

from ..tools import download_if_not_found
from ..writer import FileWriter
from . import ImageClassificationData


def row2image(row):
    arr = row.reshape((3, 32, 32)).transpose((1, 2, 0))
    im = Image.fromarray(arr, 'RGB')
    bio = io.BytesIO()
    im.save(bio, 'PNG')
    return bio.getvalue()


def __yield_rows(files):
    for f in files:
        d = load(f, encoding='bytes')
        for row, label, filename in zip(
                d[b'data'], d[b'labels'], d[b'filenames']
        ):
            filename = filename.decode('utf-8')
            image = row2image(row)
            yield image, label, filename


def __write_sets(outdir, train_names, test_names, shuffle):
    for name, files in (('train', train_names), ('test', test_names)):
        gen = __yield_rows(files)
        if shuffle:
            gen = list(gen)
            random.shuffle(gen)
        with FileWriter(pt.join(outdir, name + '.msgpack'), total=len(files)) as writer:
            for data, label, filename in gen:
                writer.write(ImageClassificationData(
                    data,
                    int(label),
                    filename,
                ))


def get_files(tar, prefix, names):
    return [tar.extractfile(pt.join(prefix, n)) for n in names]


def write_sets(indir, outdir, shuffle=True):
    download_if_not_found(
        'https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz',
        pt.join(indir, 'cifar-10-python.tar.gz')
    )
    train_names = ['data_batch_%d' % i for i in range(1, 6)]
    test_names = ['test_batch']
    with tarfile.open(pt.join(indir, 'cifar-10-python.tar.gz'), 'r:gz') as tar:
        __write_sets(
            outdir,
            get_files(tar, 'cifar-10-batches-py', train_names),
            get_files(tar, 'cifar-10-batches-py', test_names),
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
