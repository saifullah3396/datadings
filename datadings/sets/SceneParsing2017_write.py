"""Create Vaihingen data set files.

The data set is described here:
    https://github.com/CSAILVision/placeschallenge/tree/master/sceneparsing

This tool will look for the following files in the input directory
and download them if necessary:
    - images.tar
    - sceneparsing.tar
"""
from __future__ import print_function, division

import csv
import os
import os.path as pt
import tarfile
import json
from collections import defaultdict
from itertools import chain

from six.moves import zip_longest

from datadings.sets import SegmentationData
from datadings.writer import FileWriter
from datadings.tools import FrequencyPrinter
from datadings.tools import download_if_not_found
from datadings.matlab import loadmat
from datadings.sets.VOC2012_write import imagedata_to_array
from datadings.sets.VOC2012_write import class_counts
from datadings.sets.VOC2012_write import sorted_values
from datadings.sets.VOC2012_write import print_values
from datadings.sets.VOC2012_write import extractmember
from datadings.sets.VOC2012_write import extract
from datadings.sets.SceneParsing2017 import WEIGHTS
from datadings.sets.SceneParsing2017 import CLASSES


DATASET_URL = 'http://placeschallenge.csail.mit.edu/data/ChallengeData2017/'
IMAGE_URL = DATASET_URL + 'images.tar'
SEG_URL = DATASET_URL + 'sceneparsing.tar'
CLASS_URL = 'https://raw.githubusercontent.com/CSAILVision/' \
            'placeschallenge/69bbf9dc82621bd4b4f981ac47659ba8d74e8a27/' \
            'sceneparsing/objectInfo150.txt'
COLOR_URL = 'https://github.com/CSAILVision/placeschallenge/raw/' \
            '1052a8d3a858a1face4f4bbaa7f5eb33e06482ac/sceneparsing/' \
            'visualizationCode/color150.mat'


def find_sets(tarfp):
    members = tarfp.getmembers()
    sets = defaultdict(lambda: [])
    for m in members:
        parts = m.name.split(os.sep)
        if len(parts) == 3:
            sets[parts[1]].append(m)
    return sets


def write_set(
        imagetar, segtar,
        outdir, name, members,
        classes, class_weights
):
    print(name)
    printer = FrequencyPrinter()
    with FileWriter(pt.join(outdir, name + '.msgpack')) as writer:
        for m in members:
            imdata = extractmember(imagetar, m)
            segname = m.name.replace('images', 'annotations_sceneparsing') \
                            .replace('.jpg', '.png')
            segdata = extract(segtar, segname)
            writer.write(SegmentationData(
                imdata,
                segdata,
                pt.basename(m.name),
                classes,
                class_weights
            ))
            printer.update()
    printer.print_total_updates()


def write_sets(indir, outdir):
    imagepath = pt.join(indir, 'images.tar')
    download_if_not_found(IMAGE_URL, imagepath)
    segpath = pt.join(indir, 'sceneparsing.tar')
    download_if_not_found(SEG_URL, segpath)
    with tarfile.TarFile(imagepath) as imagetar:
        sets = find_sets(imagetar)
        with tarfile.TarFile(segpath) as segtar:
            for name, members in sets.items():
                write_set(imagetar, segtar,
                          outdir, name, members,
                          CLASSES, WEIGHTS)


def _segmap(segtar, member):
    return imagedata_to_array(extractmember(segtar, member))


def calculate_counts(indir, outdir):
    segpath = pt.join(indir, 'sceneparsing.tar')
    download_if_not_found(SEG_URL, segpath)
    with tarfile.TarFile(segpath) as segtar:
        members = find_sets(segtar)['training']
        gen = (_segmap(segtar, m) for m in members)
        counts = class_counts(gen)
    with open(pt.join(outdir, 'SceneParsing2017_counts.json'), 'w') as f:
        json.dump({
            'INDEXES': sorted(counts.keys()),
            'COUNTS': sorted_values(counts)
        }, f)


def color_map(indir, outdir):
    colorpath = pt.join(indir, 'color150.mat')
    download_if_not_found(COLOR_URL, colorpath)
    colors = loadmat(colorpath)['colors']
    colors[..., 0], colors[..., 2] = colors[..., 2], colors[..., 0]
    with open(pt.join(outdir, 'SceneParsing2017_colors.json'), 'w') as f:
        json.dump([[0, 0, 0]] + colors.tolist(), f)


def classes(indir):
    classpath = pt.join(indir, 'objectInfo150.txt')
    download_if_not_found(CLASS_URL, classpath)
    with open(classpath) as f:
        classes = [
            l['Name'].split(', ')[0]
            for l in csv.DictReader(f, dialect='excel-tab')
        ]
    classes = zip_longest(*(classes[i::5] for i in range(5)))
    classes = chain(
        [repr('background')],
        [', '.join(map(repr, row)) for row in classes]
    )
    print_values('CLASSES', classes)


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
        help='directory that contains SceneParsing2017 files'
    )
    parser.add_argument(
        '-o', '--outdir',
        metavar='OUTPATH',
        help='output directory; defaults to indir'
    )
    parser.add_argument(
        '--calculate-counts',
        action='store_true',
        help='calculate pixel counts per class'
    )
    parser.add_argument(
        '--color-map',
        action='store_true',
        help='create color map'
    )
    parser.add_argument(
        '--classes',
        action='store_true',
        help='create class list'
    )
    args = parser.parse_args()
    outdir = args.outdir or args.indir
    if args.calculate_counts:
        calculate_counts(args.indir, outdir)
    elif args.color_map:
        color_map(args.indir, outdir)
    elif args.classes:
        classes(args.indir)
    else:
        write_sets(args.indir, outdir)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
