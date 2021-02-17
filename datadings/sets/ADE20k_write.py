"""Create ADE20k data set files.

This tool will look for the following files in the input directory
and download them if necessary:

- ADE20K_2016_07_26.zip

See also:
    http://groups.csail.mit.edu/vision/datasets/ADE20K
"""
import os.path as pt
import zipfile
import io
import json
from multiprocessing.dummy import Pool as ThreadPool
from collections import Counter
import itertools as it
import random

import numpy as np
from PIL import Image

from . import ADE20kData
from ..writer import FileWriter
from ..tools import yield_threaded
from ..tools.matlab import loadmat
from ..tools.matlab import iter_fields
from .VOC2012_write import imagedata_to_array
from .VOC2012_write import class_counts
from .VOC2012_write import sorted_values
from ..tools import document_keys


__doc__ += document_keys(ADE20kData)


BASE_URL = 'http://groups.csail.mit.edu/vision/datasets/ADE20K/'
FILES = {
    'all': {
        'url': BASE_URL+'ADE20K_2016_07_26.zip',
        'path': 'ADE20K_2016_07_26.zip',
        'md5': '5d125f9457b1a3990adb96de45d03f60',
    },
}


def __array2list(a):
    c = Counter(i.dtype.kind for i in a[:50])
    kind, _ = c.most_common(1)[0]
    if kind == 'U':
        return [i.item() if i.size else '' for i in a]
    elif kind == 'O':
        return [__array2list(i.reshape(-1)) if i.size else [] for i in a]
    else:
        return a


def load_index(imagezip, *keys):
    data = imagezip.read(pt.join('ADE20K_2016_07_26', 'index_ade20k.mat'))
    index = loadmat(data)['index']
    index = {k: __array2list(v[0, 0].reshape(-1))
             for k, v in iter_fields(index) if not keys or k in keys}
    if keys:
        return [index[k] for k in keys]
    else:
        return index


def array_to_image(array, format, dtype, mode, **kwargs):
    im = Image.fromarray(array.astype(dtype), mode)
    bio = io.BytesIO()
    im.save(bio, format=format, **kwargs)
    return bio.getvalue()


def array_to_png16(array):
    return array_to_image(array, 'png', np.int32, 'I', optimize=True)


def segmentation_map(im):
    segmap = np.zeros(im.shape[:2], dtype=np.uint16)
    segmap[...] = im[:, :, 0] // 10
    segmap *= 256
    segmap += im[:, :, 1]
    return segmap


def imagedata_to_segpng(data):
    im = imagedata_to_array(data)
    segmap = segmentation_map(im)
    segpng = array_to_png16(segmap)
    return segpng


def instance_map(im):
    return im[:, :, 2]


def yield_images(names):
    allparts = set(n for n in names if '_parts_' in n and n.endswith('.png'))
    prefixes = (n.rstrip('.jpg') for n in names if n.endswith('.jpg'))
    for p in prefixes:
        parts = []
        for i in it.count(1):
            part = p + '_parts_%d.png' % i
            if part not in allparts:
                break
            parts.append(part)
        yield p + '.jpg', p + '_seg.png', parts


def write_set(imagezip, outdir, split, scenelabels, args):
    names = [n for n in imagezip.namelist() if split in n]
    total = len([1 for n in names if n.endswith('.jpg')])
    if args.shuffle:
        random.shuffle(names)

    gen = yield_threaded(
        (
            pt.basename(path),
            imagezip.read(path),
            imagezip.read(segpath),
            [imagezip.read(p) for p in parts]
        )
        for path, segpath, parts in yield_images(names)
    )

    def __inner(item):
        key, data, segdata, parts = item
        segdata = imagedata_to_segpng(segdata)
        parts = [imagedata_to_segpng(part) for part in parts]
        return ADE20kData(key, data, scenelabels[key], segdata, parts)

    outfile = pt.join(outdir, split + '.msgpack')
    with FileWriter(outfile, total=total, overwrite=args.no_confirm) as writer:
        pool = ThreadPool(args.threads)
        for sample in pool.imap_unordered(__inner, gen):
            writer.write(sample)


def write_sets(files, outdir, args):
    with zipfile.ZipFile(files['all']['path']) as imagezip:
        filenames, scenes = load_index(imagezip, 'filename', 'scene')
        scenelabels = {l: i for i, l in enumerate(sorted(set(scenes)))}
        scenelabels = {pt.basename(im): scenelabels[l]
                       for im, l in zip(filenames, scenes)}
        del filenames, scenes
        for split in ('training', 'validation'):
            try:
                write_set(imagezip, outdir, split, scenelabels, args)
            except FileExistsError:
                pass


def _segmap(segdata):
    return segmentation_map(imagedata_to_array(segdata))


def calculate_weights(files, outdir):
    with zipfile.ZipFile(files['all']['path']) as imagezip:
        gen = yield_threaded(
            _segmap(imagezip.read(path))
            for _, seg, parts in yield_images(imagezip.namelist())
            if 'training' in seg
            for path in parts + [seg]
        )
        counts = class_counts(gen)
    with open(pt.join(outdir, 'ADE20k_counts.json'), 'w') as f:
        json.dump({
            'INDEXES': sorted(counts.keys()),
            'COUNTS': sorted_values(counts)
        }, f)


def extract_scenelabels(files, outdir):
    with zipfile.ZipFile(files['all']['path']) as imagezip:
        scenes = sorted(set(load_index(imagezip, 'scene')['scene']))
    with open(pt.join(outdir, 'ADE20k_scenelabels.json'), 'w') as f:
        json.dump(scenes, f)


def main():
    from ..tools.argparse import make_parser
    from ..tools.argparse import argument_calculate_weights
    from ..tools.argparse import argument_threads
    from ..tools import prepare_indir

    parser = make_parser(__doc__)
    argument_threads(parser, default=8)
    argument_calculate_weights(parser)
    parser.add_argument(
        '--scenelabels',
        action='store_true',
        help='extract list of scene labels'
    )
    args = parser.parse_args()
    outdir = args.outdir or args.indir

    files = prepare_indir(FILES, args)

    if args.calculate_weights:
        calculate_weights(files, outdir)
    elif args.scenelabels:
        extract_scenelabels(files, outdir)
    else:
        write_sets(files, outdir, args)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
