"""Create Coutrot 1 data set files.

Download video ZIP-file and Matlab file from here:
    http://antoinecoutrot.magix.net/public/databases.html

Video files must be unzipped."""
from __future__ import print_function, division

import os
import os.path as pt
from math import floor
from math import log
from collections import defaultdict

try:
    import cv2
except ImportError:
    print('Install OpenCV 2.4+ to create video-based data sets')
    import sys
    sys.exit(1)
import numpy as np

from datadings.writer import ImageWriter
from datadings.tools import FrequencyPrinter
from datadings.sets import SaliencyData
from datadings.sets import SaliencyExperiment
from datadings.matlab import loadmat
from datadings.matlab import iter_fields


THRESHOLD_GOOD = 1.


def _max_level(params, frame):
    """ Compute a sensible maxlevel value for a frame, i.e.,
        ensure the smallest pyramid level is not too small.

        @param params: other tracker parameters
        @param frame: frame with shape (height, width, channels)
        @return: maxlevel int; at least 1
    """
    size = min(frame.shape[:2])
    target = max(params.get('winSize', (21, 21)))
    levels = int(floor(log(size / target, 2)))
    return max(levels, 1)


class LucasKanade(object):
    def __init__(self):
        self.frame_gray = None
        self.points = {}
        self.frame_idx = 0

    def track(self, xy, pointid):
        if not any(np.isnan(xy)):
            self.points[pointid] = tuple(xy)

    def update(self, frame):
        """ Update the tracking result for a new frame.

            @param frame: next frame
            @return: dict {point: (x, y)}
        """
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.frame_gray is not None and self.points:
            # attempt tracking
            img0, img1 = self.frame_gray, frame_gray
            pointids = list(self.points.keys())
            points = list(self.points.values())
            p0 = np.array(points, dtype=np.float32).reshape((-1, 1, 2))
            params = dict(
                winSize=(21, 21),
                criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
            )
            params['maxLevel'] = _max_level(params, frame_gray)

            # see: OPTFLOW_USE_INITIAL_FLOW
            p1, st, err = cv2.calcOpticalFlowPyrLK(img0, img1, p0, None, **params)
            p0r, st, err = cv2.calcOpticalFlowPyrLK(img1, img0, p1, None, **params)

            # check tracking quality
            d = np.abs(p0-p0r).reshape(-1, 2).max(-1)
            good = d < THRESHOLD_GOOD

            # update tracks
            new_points = {}
            for pointid, point, is_good \
                    in zip(pointids, p1.reshape(-1, 2), good):
                if is_good:
                    new_points[pointid] = point
            self.points = new_points
        self.frame_gray = frame_gray
        return dict(self.points)


def __parse_mat(mat):
    clips = {}
    for k, v in iter_fields(mat, ignore=['Header']):
        clips.update({
            k2: v2['data'][0, 0].transpose((2, 1, 0))
            for k2, v2 in iter_fields(v[0, 0][0, 0])
        })
    return clips


def __iter_video(path):
    video = cv2.VideoCapture(path)
    i = 0
    while video.isOpened():
        ret, frame = video.read()
        if ret:
            yield i, frame
            i += 1
        else:
            break


def __group_points(locations):
    groups = defaultdict(lambda: [])
    for (subject, _), xy in locations.items():
        groups[subject].append(xy)
    return list(groups.values())


def write_video(clip_data, path, writer, printer, min_fixpoints=1):
    clip = path.split(os.sep)[-1].split('.')[0]
    locations = clip_data[clip]
    tracker = LucasKanade()
    for i, frame in __iter_video(path):
        for s, subject in enumerate(locations):
            try:
                tracker.track(subject[i], (s, i))
            except IndexError:
                continue
        points = tracker.update(frame)
        groups = __group_points(points)
        experiments = [
            SaliencyExperiment(group, None)
            for group in groups
            if len(group) >= min_fixpoints
        ]
        if not experiments:
            continue
        jpegdata = bytes(cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95]))
        item = SaliencyData(
            jpegdata,
            experiments,
            pt.join('ERB3_Stimuli', '%s.avi_%06d' % (clip, i)),
        )
        writer.write(item)
        printer.update()


def write_sets(indir, outdir, shuffle=True):
    printer = FrequencyPrinter()
    mat = loadmat(pt.join(indir, 'coutrot_database1.mat'))
    clip_data = __parse_mat(mat['Coutrot_Database1'])
    with ImageWriter(pt.join(outdir, 'Coutrot1.msgpack')) as writer:
        for path in os.listdir(pt.join(indir, 'ERB3_Stimuli')):
            path = pt.join(indir, 'ERB3_Stimuli', path)
            # TODO shuffle if possible
            if not path.endswith('.avi'):
                continue
            write_video(clip_data, path, writer, printer)
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
