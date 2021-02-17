"""Create CAT2000 data set files.

This tool will look for the following files in the input directory
and download them if necessary:

- trainSet.zip
- testSet.zip

See also:
    http://saliency.mit.edu/results_cat2000.html
"""
import os
import os.path as pt
import zipfile
import random
from multiprocessing.dummy import Pool as ThreadPool

import numpy as np
from PIL import Image
from PIL import ImageChops
from simplejpeg import decode_jpeg
from simplejpeg import encode_jpeg

from ..writer import FileWriter
from ..tools.matlab import loadmat
from ..tools import yield_threaded
from . import SaliencyData
from . import SaliencyExperiment
from ..tools import document_keys


__doc__ += document_keys(
    SaliencyData,
    postfix=document_keys(
        SaliencyExperiment,
        block='',
        prefix='Each experiment has the following keys:'
    )
)


BASE_URL = 'http://saliency.mit.edu/'
FILES = {
    'train': {
        'path': 'trainSet.zip',
        'url': BASE_URL+'trainSet.zip',
        'md5': '56ad5c77e6c8f72ed9ef2901628d6e48',
    },
    'test': {
        'path': 'testSet.zip',
        'url': BASE_URL+'testSet.zip',
        'md5': '903ec668df2e5a8470aef9d8654e7985',
    }
}


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


def __decode(data):
    return Image.fromarray(decode_jpeg(
        data, fastupsample=False, fastdct=False
    ), 'RGB')


def __crompress(image, quality=90):
    return encode_jpeg(np.array(image), quality=quality)


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


def yield_samples(imagezip, names):
    for stimuluspath in names:
        with imagezip.open(stimuluspath) as f:
            stimulusdata = f.read()
            try:
                response = __load_fixmap(imagezip, stimuluspath)
            except KeyError:
                response = None
        yield stimuluspath, stimulusdata, response


def create_sample(item):
    stimuluspath, stimulusdata, response = item
    stimulus = __decode(stimulusdata)
    bbox = __find_bbox(stimulus)
    r, cropped = __transform_image(stimulus, bbox)
    stimulusdata = __crompress(cropped)
    if response is not None:
        locations = transform_points(find_fixpoints(response), bbox, r)
        locations = filter_invalid_fixpoints(locations, cropped.size)
    else:
        locations = None
    filename = os.sep.join(stimuluspath.split(os.sep)[-2:])
    return SaliencyData(
        filename,
        stimulusdata,
        [SaliencyExperiment(locations, None)],
    )


def __is_stimulus(path):
    return 'Stimuli' in path and 'Output' not in path and path.endswith('.jpg')


def write_set(imagezip, outdir, split, args):
    names = [f for f in imagezip.namelist() if __is_stimulus(f)]
    if args.shuffle:
        random.shuffle(names)

    gen = yield_threaded(yield_samples(imagezip, names))

    outfile = pt.join(outdir, split + '.msgpack')
    with FileWriter(outfile, total=len(names), overwrite=args.no_confirm) as writer:
        pool = ThreadPool(args.threads)
        for sample in pool.imap_unordered(create_sample, gen):
            writer.write(sample)


def write_sets(files, outdir, args):
    for split in ('train', 'test'):
        with zipfile.ZipFile(files[split]['path']) as imagezip:
            try:
                write_set(imagezip, outdir, split, args)
            except FileExistsError:
                pass


def main():
    from ..tools.argparse import make_parser
    from ..tools.argparse import argument_threads
    from ..tools import prepare_indir

    parser = make_parser(__doc__)
    argument_threads(parser)
    args = parser.parse_args()
    outdir = args.outdir or args.indir

    files = prepare_indir(FILES, args)

    write_sets(files, outdir, args)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
