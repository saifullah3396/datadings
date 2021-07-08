"""Create Places2017 data set files.

This tool will look for all or parts of the following files in the input
directory, depending on the given command, and download them if necessary:

- images.tar
- sceneparsing.tar
- annotations_instance.tar
- boundaries.tar
- objectInfo150.txt
- color150.mat

Additionally, ADE20K_2016_07_26.zip from the ADE20k dataset is required
to extract scene labels with the ``--scenelabels`` option.

See also:
    https://github.com/CSAILVision/placeschallenge

Warning:
    OpenCV 2.4+ is required to create this dataset.
    If you are unsure how to install OpenCV you can use pip:

        pip install opencv-python

"""
import csv
import os
import os.path as pt
from zipfile import ZipFile
from tarfile import TarFile
import json
from collections import defaultdict
from itertools import chain
from itertools import zip_longest
import io
import random
import gzip

import numpy as np
from PIL import Image
try:
    import cv2
except ImportError:
    print("""
OpenCV could not be imported.
OpenCV 2.4+ is required to create this dataset.
If you are unsure how to install OpenCV you can use pip:

    pip install opencv-python

""")
    import sys
    sys.exit(1)

from ..writer import FileWriter
from ..tools.matlab import loadmat
from .VOC2012_write import imagedata_to_array
from .VOC2012_write import class_counts
from .VOC2012_write import sorted_values
from .VOC2012_write import print_values
from .VOC2012_write import extractmember
from .VOC2012_write import extract
from .ADE20k_write import FILES as FILES_ADE20k
from .ADE20k_write import load_index
from .ADE20k import SCENELABELS
from . import Places2017Data
from .tools import load_json
from ..tools import document_keys


__doc__ += document_keys(Places2017Data)


BASE_URL = 'http://placeschallenge.csail.mit.edu/data/ChallengeData2017/'
COMMIT_PREFIX = 'https://raw.githubusercontent.com/CSAILVision/' \
            'placeschallenge/69bbf9dc82621bd4b4f981ac47659ba8d74e8a27/' \
            'sceneparsing/'
FILES = {
    'images': {
        'path': 'images.tar',
        'url': BASE_URL+'images.tar',
        'md5': '5c55d03495a7541407cb940a3be07d32',
    },
    'classes': {
        'path': 'sceneparsing.tar',
        'url': BASE_URL+'sceneparsing.tar',
        'md5': '6556305fe8a1ac817d5d426ff4cb35f3',
    },
    'instances': {
        'path': 'annotations_instance.tar',
        'url': BASE_URL+'annotations_instance.tar',
        'md5': '4d6628c4d17f68dc36efb6a79fce30a9',
    },
    'boundaries': {
        'path': 'boundaries.tar',
        'url': BASE_URL+'boundaries.tar',
        'md5': '7cd81ad176aad64eff1dbca02ab0550a',
    },
    'class_info': {
        'path': 'objectInfo150.txt',
        'url': COMMIT_PREFIX+'objectInfo150.txt',
        'md5': '4fb6ef9f025e48ad9cdf451e2b96c510',
    },
    'colors': {
        'path': 'color150.mat',
        'url': COMMIT_PREFIX+'visualizationCode/color150.mat',
        'md5': '851aba69b499726c2b8ff5da1e147d02',
    },
}


def array_to_image(array, format, dtype, mode, **kwargs):
    im = Image.fromarray(array.astype(dtype), mode)
    bio = io.BytesIO()
    im.save(bio, format=format, **kwargs)
    return bio.getvalue()


def array_to_png(array):
    return array_to_image(array, 'png', np.uint8, 'L', optimize=True)


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
    boundaries = []
    for m in mat:
        _, contours, _ = cv2.findContours(
            m[0].toarray('C'),
            cv2.RETR_LIST,
            cv2.CHAIN_APPROX_TC89_L1
        )
        boundaries.append([c.reshape((-1, 2)) for c in contours])
    return boundaries


def extract_scene(scenes, name):
    return scenes[pt.basename(name)]


def write_set(
        imagetar, classtar, instancetar, boundarytar,
        outdir, name, members, scenes, overwrite
):
    outfile = pt.join(outdir, name + '.msgpack')
    with FileWriter(outfile, total=len(members),
                    overwrite=overwrite) as writer:
        for m in members:
            writer.write(Places2017Data(
                pt.basename(m.name),
                extractmember(imagetar, m),
                extract_class(classtar, m.name),
                extract_scene(scenes, m.name),
                extract_instance(instancetar, m.name),
                extract_boundary(boundarytar, m.name),
            ))


def write_sets(files, outdir, args):
    scenes = load_json('Places2017_scenelabels.json.xz')
    with TarFile(files['images']['path']) as imagetar, \
            TarFile(files['classes']['path']) as classtar, \
            TarFile(files['instances']['path']) as instancetar, \
            TarFile(files['boundaries']['path']) as boundarytar:
        sets = find_sets(imagetar)
        for name, members in sets.items():
            if args.shuffle:
                random.shuffle(members)
            try:
                write_set(
                    imagetar, classtar, instancetar, boundarytar,
                    outdir, name, members, scenes, args.no_confirm
                )
            except FileExistsError:
                pass


def _segmap(segtar, member):
    return imagedata_to_array(extractmember(segtar, member))


def create_counts(files, outdir):
    with TarFile(files['classes']['path']) as segtar:
        members = find_sets(segtar)['training']
        gen = (_segmap(segtar, m) for m in members)
        counts = class_counts(gen, total=len(members))
    with open(pt.join(outdir, 'Places2017_counts.json'), 'w') as f:
        json.dump({
            'INDEXES': sorted(counts.keys()),
            'COUNTS': sorted_values(counts)
        }, f)


def create_color_map(files, outdir):
    colors = loadmat(files['colors']['path'])['colors']
    # RGB -> BGR
    colors[..., 0], colors[..., 2] = colors[..., 2], colors[..., 0]
    with open(pt.join(outdir, 'Places2017_colors.json'), 'w') as f:
        json.dump([[0, 0, 0]] + colors.tolist(), f)


def print_classes(files):
    with open(files['class_info']['path']) as f:
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


def extract_scenelabels(files, outdir):
    with ZipFile(files['all']['path']) as imagezip:
        index = load_index(imagezip)
    int_labels = {label: i for i, label in enumerate(SCENELABELS)}
    scenes = {
        name: int_labels[scene]
        for name, scene in zip(index['filename'], index['scene'])
    }
    outfile = pt.join(outdir, 'Places2017_scenelabels.json')
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(scenes, f)


def main():
    from ..tools.argparse import make_parser
    from ..tools import prepare_indir

    parser = make_parser(__doc__)
    parser.add_argument(
        '--class-counts',
        action='store_true',
        help='Count pixels per class and write to Places2017_counts.json.'
    )
    parser.add_argument(
        '--color-map',
        action='store_true',
        help='Create color map and write to Places2017_colors.json.'
    )
    parser.add_argument(
        '--classes',
        action='store_true',
        help='Print the class list.'
    )
    parser.add_argument(
        '--scenelabels',
        action='store_true',
        help='Extract the scene labels from ADE20k dataset '
             'and write to Places2017_scenelabels.json. '
             'This will look for ADE20K_2016_07_26.zip '
             'in indir and download if necessary.'
    )
    args = parser.parse_args()
    outdir = args.outdir or args.indir

    if args.class_counts:
        files = prepare_indir({'classes': FILES['classes']}, args)
        create_counts(files, outdir)
    elif args.color_map:
        files = prepare_indir({'colors': FILES['colors']}, args)
        create_color_map(files, outdir)
    elif args.classes:
        files = prepare_indir({'class_info': FILES['class_info']}, args)
        print_classes(files)
    elif args.scenelabels:
        files = prepare_indir(FILES_ADE20k, args)
        extract_scenelabels(files, outdir)
    else:
        files = prepare_indir(FILES, args)
        write_sets(files, outdir, args)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
