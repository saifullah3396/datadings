"""Create MIT300 data set files.

This tool will look for the following files in the input directory
and download them if necessary:

- BenchmarkIMAGES.zip

See also:
    http://saliency.mit.edu/results_mit300.html
"""
import os.path as pt
from zipfile import ZipFile
import random

from ..writer import FileWriter
from . import ImageData
from ..tools import document_keys


__doc__ += document_keys(ImageData)


FILES = {
    'zip': {
        'path': 'BenchmarkIMAGES.zip',
        'url': 'http://saliency.mit.edu/BenchmarkIMAGES.zip',
        'md5': '03ed32bdf5e4289950cd28df89451260',
    }
}


def write_image(imagezip, stimuluspath, writer):
    stimulusdata = imagezip.read(stimuluspath)
    item = ImageData(
        stimuluspath,
        stimulusdata
    )
    writer.write(item)


def _isimage(f):
    return f.endswith('.jpg') and 'SM' not in f and not f.startswith('__')


def write_sets(files, outdir, args):
    with ZipFile(files['zip']['path']) as imagezip:
        names = [f for f in imagezip.namelist() if _isimage(f)]
        with FileWriter(pt.join(outdir, 'MIT300.msgpack'),
                        total=len(names), overwrite=args.no_confirm) as writer:
            if args.shuffle:
                random.shuffle(names)
            for path in names:
                write_image(imagezip, path, writer)


def main():
    from ..tools.argparse import make_parser
    from ..tools import prepare_indir

    parser = make_parser(__doc__)
    args = parser.parse_args()
    outdir = args.outdir or args.indir

    files = prepare_indir(FILES, args)

    try:
        write_sets(files, outdir, args)
    except FileExistsError:
        pass


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
