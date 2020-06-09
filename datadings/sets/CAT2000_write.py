"""Create CAT2000 data set files.

The data set is described here:
    http://saliency.mit.edu/results_cat2000.html

This tool will look for the following files in the input directory
and download them if necessary:
    - ALLSTIMULI.zip
    - DATA.zip
"""
import io
import os
import os.path as pt
import zipfile
import random

import numpy as np
from PIL import Image
from PIL import ImageChops

from ..writer import FileWriter
from ..tools import download_if_not_found
from ..matlab import loadmat
from . import SaliencyData
from . import SaliencyExperiment


def __find_bbox(im):
    bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 1.0, -20)
    return diff.getbbox()


def __transform_image(im, bbox, size=1024):
    cropped = im.crop(bbox)
    w, h = cropped.size
    d = max(w, h)
    r = size / d
    return r, cropped.resize(
        (int(round(w*r)), int(round(h*r))),
        Image.ANTIALIAS,
    )


def __crompress(image, format='jpeg', quality=90):
    buf = io.BytesIO()
    image.save(buf, format=format, quality=quality)
    return buf.getvalue()


def __load_fixmap(imagezip, stimuluspath):
    with imagezip.open(
            stimuluspath.replace('Stimuli', 'FIXATIONLOCS').replace('jpg', 'mat')
    ) as f:
        data = f.read()
    return loadmat(data)['fixLocs']


def find_fixpoints(arr):
    # must flip (x,y) coordinate
    return np.transpose(np.nonzero(arr)[::-1]).astype(np.float32)


def transform_points(points, offset, scale_factor):
    return (points - offset[:2]) * scale_factor


def filter_invalid_fixpoints(points, size):
    w, h = size
    ind = (points > 0).any(axis=1)
    ind = np.logical_and(ind, points[:, 0] < w)
    ind = np.logical_and(ind, points[:, 1] < h)
    return points[ind]


def write_image(imagezip, stimuluspath, writer):
    with imagezip.open(stimuluspath) as f:
        stimulus = Image.open(f)
        bbox = __find_bbox(stimulus)
        r, cropped = __transform_image(stimulus, bbox)
        stimulusdata = __crompress(cropped)
    try:
        response = __load_fixmap(imagezip, stimuluspath)
        locations = transform_points(find_fixpoints(response), bbox, r)
        locations = filter_invalid_fixpoints(locations, cropped.size)
    except KeyError:
        locations = None
    filename = os.sep.join(stimuluspath.split(os.sep)[-2:])
    item = SaliencyData(
        filename,
        stimulusdata,
        [SaliencyExperiment(locations, None)],
    )
    writer.write(item)


def __is_stimulus(path):
    return 'Stimuli' in path and 'Output' not in path and path.endswith('.jpg')


def write_sets(indir, outdir, shuffle=True):
    url_prefix = 'http://saliency.mit.edu/'
    for name in ('train', 'test'):
        imagepath = pt.join(indir, name + 'Set.zip')
        download_if_not_found(url_prefix + '%sSet.zip' % name, imagepath)
        with zipfile.ZipFile(imagepath) as imagezip:
            names = [f for f in imagezip.namelist() if __is_stimulus(f)]
            if shuffle:
                random.shuffle(names)
            with FileWriter(pt.join(outdir, name + '.msgpack'), total=len(names)) as writer:
                for path in names:
                    write_image(imagezip, path, writer)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'indir',
        metavar='INPATH',
        help='directory that contains CAT2000 files'
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
