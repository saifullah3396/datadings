"""Create Places2017 data set files.

The data set is described here:
    https://github.com/CSAILVision/placeschallenge

This tool will look for the following files in the input directory
and download them if necessary:
    - images.tar
    - sceneparsing.tar
    - annotations_instance.tar
    - boundaries.tar

May also look for/download, depending on options:
    - objectInfo150.txt
    - color150.mat
"""
from __future__ import print_function, division

import csv
import os
import os.path as pt
import tarfile
import json
from collections import defaultdict
from itertools import chain
import io
import random

from six.moves import zip_longest
import numpy as np
from PIL import Image

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
from datadings.sets.Places2017 import Places2017Data
from datadings.sets.Places2017 import Places2017Task
from datadings.sets.Places2017 import WEIGHTS
from datadings.sets.Places2017 import CLASSES


TAR_PREFIX = 'http://placeschallenge.csail.mit.edu/data/ChallengeData2017/'
IMAGE_FILE = 'images.tar'
IMAGE_TAR = TAR_PREFIX + IMAGE_FILE
CLASS_FILE = 'sceneparsing.tar'
CLASS_TAR = TAR_PREFIX + CLASS_FILE
INSTANCE_FILE = 'annotations_instance.tar'
INSTANCE_TAR = TAR_PREFIX + INSTANCE_FILE
BOUNDARY_FILE = 'boundaries.tar'
BOUNDARY_TAR = TAR_PREFIX + BOUNDARY_FILE
COMMIT_PREFIX = 'https://raw.githubusercontent.com/CSAILVision/' \
            'placeschallenge/69bbf9dc82621bd4b4f981ac47659ba8d74e8a27/' \
            'sceneparsing/'
CLASSES_FILE = 'objectInfo150.txt'
CLASSES_DEF = COMMIT_PREFIX + CLASSES_FILE
COLORS_FILE = 'color150.mat'
COLORS_DEF = COMMIT_PREFIX + 'visualizationCode/' + COLORS_FILE


def array_to_image(array, format, dtype, mode):
    im = Image.fromarray(array.astype(dtype), mode)
    bio = io.BytesIO()
    im.save(bio, format=format)
    return bio.getvalue()


def array_to_png(array):
    return array_to_image(array, 'png', np.uint8, 'L')


def find_sets(tarfp):
    members = tarfp.getmembers()
    sets = defaultdict(lambda: [])
    for m in members:
        parts = m.name.split(os.sep)
        if len(parts) == 3:
            sets[parts[1]].append(m)
    return sets


def _gt(name, target_dir, extension='.png'):
    d = 'annotations_' + target_dir
    return name.replace('images', d).replace('.jpg', extension)


def extract_class(classtar, name):
    return extract(classtar, _gt(name, 'sceneparsing', '.png'))


def extract_instance(instancetar, name):
    return extract(instancetar, _gt(name, 'instance', '.png'))


def extract_boundary(boundarytar, name):
    data = extract(boundarytar, _gt(name, 'boundary', '.mat'))
    mat = loadmat(data)['gt']['bdry'][0][0]
    out = mat[0][0]
    for m in mat[1:]:
        out += m[0]
    out = np.clip(out.toarray(), 0, 1)
    return array_to_png(out)


def write_set(
        imagetar, classtar, instancetar, boundarytar,
        outdir, name, members,
        classes, class_weights
):
    print(name)
    printer = FrequencyPrinter()
    with FileWriter(pt.join(outdir, name + '.msgpack')) as writer:
        for m in members:
            writer.write(Places2017Data(
                extractmember(imagetar, m),
                [
                    Places2017Task(
                        extract_class(classtar, m.name), class_weights),
                    Places2017Task(
                        extract_instance(instancetar, m.name), class_weights),
                    # TODO boundary weights
                    Places2017Task(
                        extract_boundary(boundarytar, m.name), None),
                ],
                pt.basename(m.name),
                classes,
            ))
            printer.update()
    printer.print_total_updates()


def write_sets(indir, outdir, shuffle=True):
    imagepath = pt.join(indir, 'images.tar')
    download_if_not_found(IMAGE_TAR, imagepath)
    classpath = pt.join(indir, CLASS_FILE)
    download_if_not_found(CLASS_TAR, classpath)
    instancepath = pt.join(indir, INSTANCE_FILE)
    download_if_not_found(INSTANCE_TAR, instancepath)
    boundarypath = pt.join(indir, BOUNDARY_FILE)
    download_if_not_found(BOUNDARY_TAR, boundarypath)
    with tarfile.TarFile(imagepath) as imagetar:
        sets = find_sets(imagetar)
        with tarfile.TarFile(classpath) as classtar:
            with tarfile.TarFile(instancepath) as instancetar:
                with tarfile.TarFile(boundarypath) as boundarytar:
                    for name, members in sets.items():
                        if shuffle:
                            random.shuffle(members)
                        write_set(
                            imagetar, classtar, instancetar, boundarytar,
                            outdir, name, members, CLASSES, WEIGHTS
                        )


def _segmap(segtar, member):
    return imagedata_to_array(extractmember(segtar, member))


def create_counts(indir, outdir):
    segpath = pt.join(indir, 'sceneparsing.tar')
    download_if_not_found(CLASS_TAR, segpath)
    with tarfile.TarFile(segpath) as segtar:
        members = find_sets(segtar)['training']
        gen = (_segmap(segtar, m) for m in members)
        counts = class_counts(gen)
    with open(pt.join(outdir, 'Places2017_counts.json'), 'w') as f:
        json.dump({
            'INDEXES': sorted(counts.keys()),
            'COUNTS': sorted_values(counts)
        }, f)


def create_color_map(indir, outdir):
    colorpath = pt.join(indir, COLORS_FILE)
    download_if_not_found(COLORS_DEF, colorpath)
    colors = loadmat(colorpath)['colors']
    # RGB -> BGR
    colors[..., 0], colors[..., 2] = colors[..., 2], colors[..., 0]
    with open(pt.join(outdir, 'Places2017_colors.json'), 'w') as f:
        json.dump([[0, 0, 0]] + colors.tolist(), f)


def print_classes(indir):
    classpath = pt.join(indir, CLASSES_FILE)
    download_if_not_found(CLASSES_DEF, classpath)
    with open(classpath) as f:
        cs = [
            l['Name'].split(', ')[0]
            for l in csv.DictReader(f, dialect='excel-tab')
        ]
    cs = zip_longest(*(cs[i::5] for i in range(5)))
    cs = chain(
        [repr('background')],
        [', '.join(map(repr, row)) for row in cs]
    )
    print_values('CLASSES', cs)


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
        help='directory that contains Places2017 files'
    )
    parser.add_argument(
        '-o', '--outdir',
        metavar='OUTPATH',
        help='output directory; defaults to indir'
    )
    parser.add_argument(
        '--calculate-counts',
        action='store_true',
        help='count pixels per class; '
             'creates Places2017_counts.json'
    )
    parser.add_argument(
        '--color-map',
        action='store_true',
        help='create color map; '
             'creates Places2017_colors.json'
    )
    parser.add_argument(
        '--classes',
        action='store_true',
        help='print the class list'
    )
    args = parser.parse_args()
    outdir = args.outdir or args.indir
    if args.calculate_counts:
        create_counts(args.indir, outdir)
    elif args.color_map:
        create_color_map(args.indir, outdir)
    elif args.classes:
        print_classes(args.indir)
    else:
        write_sets(args.indir, outdir)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
