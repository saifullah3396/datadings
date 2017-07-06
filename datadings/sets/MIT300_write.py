"""Create MIT300 data set files.

The data set is described here:
    http://saliency.mit.edu/results_mit300.html

This tool will look for the following files in the input directory
and download them if necessary:
    - BenchmarkIMAGES.zip
"""
from __future__ import print_function, division

import os.path as pt
import zipfile
import random

from datadings.writer import FileWriter
from datadings.tools import FrequencyPrinter
from datadings.tools import download_if_not_found
from datadings.sets import SaliencyData


def write_image(imagezip, stimuluspath, writer):
    stimulusdata = imagezip.read(stimuluspath)
    item = SaliencyData(
        stimulusdata,
        None,
        stimuluspath,
    )
    writer.write(item)


def _isimage(f):
    return f.endswith('.jpg') and 'SM' not in f and not f.startswith('__')


def write_sets(indir, outdir, shuffle=True):
    imagepath = pt.join(indir, 'BenchmarkIMAGES.zip')
    download_if_not_found(
        'http://saliency.mit.edu/BenchmarkIMAGES.zip',
        imagepath
    )
    printer = FrequencyPrinter()
    with zipfile.ZipFile(imagepath) as imagezip:
        with FileWriter(pt.join(outdir, 'MIT300.msgpack')) as writer:
            names = [f for f in imagezip.namelist() if _isimage(f)]
            if shuffle:
                random.shuffle(names)
            for path in names:
                write_image(imagezip, path, writer)
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
        help='directory that contains MIT300 files'
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
