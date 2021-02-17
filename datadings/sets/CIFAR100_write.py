"""Create CIFAR 100 data set files.

This tool will look for the following files in the input directory
and download them if necessary:

- cifar-100-python.tar.gz

See also:
    https://www.cs.toronto.edu/~kriz/cifar.html
"""
import tarfile
import os.path as pt
import random
from pickle import load
from collections import defaultdict

from ..writer import FileWriter
from . import ImageCoarseClassificationData
from .CIFAR10_write import get_files
from .CIFAR10_write import row2image
from ..tools import document_keys


__doc__ += document_keys(ImageCoarseClassificationData)


BASE_URL = 'https://www.cs.toronto.edu/~kriz/'
FILES = {
    'all': {
        'path': 'cifar-100-python.tar.gz',
        'url': BASE_URL+'cifar-100-python.tar.gz',
        'md5': 'eb9058c3a382ffc7106e4002c42a8d85',
    }
}


def yield_rows(files):
    seen = defaultdict(lambda: 0)
    for f in files:
        d = load(f, encoding='bytes')
        for row, label, coarse_label, filename in zip(
                d[b'data'], d[b'fine_labels'],
                d[b'coarse_labels'], d[b'filenames']
        ):
            filename = filename.decode('utf-8')
            seen[filename] += 1
            # apparently some files occur multiple times...
            if seen[filename] > 1:
                filename += str(seen[filename])
            image = row2image(row)
            yield image, label, coarse_label, filename


def write_set(tar, outdir, split, args):
    files = get_files(tar, 'cifar-100-python', [split])

    gen = yield_rows(files)
    if args.shuffle:
        gen = list(gen)
        random.shuffle(gen)

    outfile = pt.join(outdir, split + '.msgpack')
    with FileWriter(outfile, total=len(files), overwrite=args.no_confirm) as writer:
        for data, label, coarse_label, filename in gen:
            writer.write(ImageCoarseClassificationData(
                filename,
                data,
                int(label),
                int(coarse_label),
            ))


def write_sets(files, outdir, args):
    with tarfile.open(files['all']['path'], 'r:gz') as tar:
        for split in ('train', 'test'):
            try:
                write_set(tar, outdir, split, args)
            except FileExistsError:
                pass


def main():
    from ..tools.argparse import make_parser
    from ..tools import prepare_indir

    parser = make_parser(__doc__)
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
