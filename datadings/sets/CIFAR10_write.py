"""Create CIFAR 10 data set files.

This tool will look for the following files in the input directory
and download them if necessary:

- cifar-10-python.tar.gz

See also:
    https://www.cs.toronto.edu/~kriz/cifar.html
"""
import io
import os.path as pt
import random
import tarfile
from pickle import load

from PIL import Image

from ..writer import FileWriter
from . import ImageClassificationData
from ..tools import document_keys


__doc__ += document_keys(ImageClassificationData)


BASE_URL = 'https://www.cs.toronto.edu/~kriz/'
FILES = {
    'all': {
        'path': 'cifar-10-python.tar.gz',
        'url': BASE_URL+'cifar-10-python.tar.gz',
        'md5': 'c58f30108f718f92721af3b95e74349a',
    }
}


def row2image(row):
    arr = row.reshape((3, 32, 32)).transpose((1, 2, 0))
    im = Image.fromarray(arr, 'RGB')
    bio = io.BytesIO()
    im.save(bio, 'PNG', optimize=True)
    return bio.getvalue()


def yield_rows(files):
    for f in files:
        d = load(f, encoding='bytes')
        for row, label, filename in zip(
                d[b'data'], d[b'labels'], d[b'filenames']
        ):
            filename = filename.decode('utf-8')
            image = row2image(row)
            yield image, label, filename


def get_files(tar, prefix, names):
    return [tar.extractfile(pt.join(prefix, n)) for n in names]


def write_set(tar, outdir, split, args):
    filenames = {
        'train': ['data_batch_%d' % i for i in range(1, 6)],
        'test': ['test_batch'],
    }
    files = get_files(tar, 'cifar-10-batches-py', filenames[split])

    gen = yield_rows(files)
    if args.shuffle:
        gen = list(gen)
        random.shuffle(gen)

    outfile = pt.join(outdir, split + '.msgpack')
    with FileWriter(outfile, total=len(files), overwrite=args.no_confirm) as writer:
        for data, label, filename in gen:
            writer.write(ImageClassificationData(
                filename,
                data,
                int(label),
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
