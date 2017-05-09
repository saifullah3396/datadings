"""Create CAT2000 data set files.

Download and image archives found here:
    http://saliency.mit.edu/results_cat2000.html

Image ZIP-files have to be left as-is."""
from __future__ import print_function, division

import io
import os
import os.path as pt
import zipfile
import random

import scipy.io
import numpy as np
from PIL import Image
from PIL import ImageChops

from datadings.writer import ImageWriter
from datadings.tools import FrequencyPrinter
from datadings.sets import SaliencyData
from datadings.sets import SaliencyExperiment


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
        Image.BICUBIC,
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
    buf = io.BytesIO(data)
    return scipy.io.loadmat(buf)['fixLocs']


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
        stimulusdata,
        [SaliencyExperiment(locations, None)],
        filename,
    )
    writer.write(item)


def __is_stimulus(path):
    return 'Stimuli' in path and 'Output' not in path and path.endswith('.jpg')


def write_sets(indir, outdir, shuffle=True):
    for name in ('train', 'test'):
        print(name)
        printer = FrequencyPrinter()
        with zipfile.ZipFile(pt.join(indir, name + 'Set.zip')) as imagezip:
            with ImageWriter(pt.join(outdir, name + '.msgpack')) as writer:
                names = imagezip.namelist()
                if shuffle:
                    random.shuffle(names)
                for path in names:
                    if __is_stimulus(path):
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
