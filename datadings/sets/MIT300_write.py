"""Create MIT300 data set files.

Download image ZIP-file from here:
    http://saliency.mit.edu/results_mit300.html

Image ZIP-file has to be left as-is."""
from __future__ import print_function, division

import os.path as pt
import zipfile

from datadings.writer import ImageWriter
from datadings.tools import FrequencyPrinter
from datadings.sets import SaliencyData


def write_image(imagezip, stimuluspath, writer):
    stimulusdata = imagezip.read(stimuluspath)
    item = SaliencyData(
        stimulusdata,
        None,
        stimuluspath,
    )
    writer.write(item)


def write_sets(indir, outdir):
    printer = FrequencyPrinter()
    with zipfile.ZipFile(pt.join(indir, 'BenchmarkIMAGES.zip')) as imagezip:
        with ImageWriter(pt.join(outdir, 'MIT300.msgpack')) as writer:
            for path in imagezip.namelist():
                if path.startswith('__') or not path.endswith('.jpg') or 'SM' in path:
                    continue
                write_image(imagezip, path, writer)
                printer.update()
        print('\r%d samples written                       ' % writer.written)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'indir',
        metavar='INPATH',
        help='directory that contains CAT2000 archives'
    )
    parser.add_argument(
        '-o', '--outdir',
        metavar='OUTPATH',
        help='output directory; defaults to indir'
    )
    args = parser.parse_args()
    outdir = args.outdir or args.indir
    try:
        write_sets(args.indir, outdir)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
