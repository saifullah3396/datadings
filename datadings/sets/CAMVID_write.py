"""
https://github.com/alexgkendall/SegNet-Tutorial/archive/fcaf7c4978dd8d091ec67db7cb7fdd225f5051c5.zip
"""
from __future__ import print_function, division

import os.path as pt
import zipfile
import random

from datadings.writer import FileWriter
from datadings.tools import FrequencyPrinter
from datadings.tools import download_if_not_found
from datadings.sets import SegmentationData
from datadings.sets.CAMVID import CLASSES


def write_image(imagezip, writer, inpath, outpath):
    indata = imagezip.read(inpath)
    outdata = imagezip.read(outpath)
    filename = pt.basename(inpath)
    item = SegmentationData(
        indata,
        outdata,
        filename,
        CLASSES,
        [1]*len(CLASSES),
    )
    writer.write(item)


def write_sets(indir, outdir, shuffle=True):
    imagepath = pt.join(indir, 'CAMVID.zip')
    download_if_not_found(
        'https://github.com/alexgkendall/SegNet-Tutorial/'
        'archive/fcaf7c4978dd8d091ec67db7cb7fdd225f5051c5.zip',
        imagepath
    )
    root_dir = 'SegNet-Tutorial-fcaf7c4978dd8d091ec67db7cb7fdd225f5051c5'
    printer = FrequencyPrinter()
    with zipfile.ZipFile(imagepath) as imagezip:
        for split in ('test', 'val', 'train'):
            with FileWriter(pt.join(outdir, 'CAMVID_%s.msgpack' % split)) as writer:
                pairs_path = pt.join(root_dir, 'CamVid', '%s.txt' % split)
                pairs = [pair.replace('\n', '').replace('/SegNet', root_dir).split(' ')
                         for pair in imagezip.open(pairs_path)]
                if shuffle:
                    random.shuffle(pairs)
                for pair in pairs:
                    write_image(imagezip, writer, *pair)
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
        help='directory that contains MIT1003 archives'
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
