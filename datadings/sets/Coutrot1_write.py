"""Create Coutrot 1 data set files.

The data set is described here:
    http://antoinecoutrot.magix.net/public/databases.html

Download video ZIP-file and Matlab files manually.
Video files must be unzipped.
Note that samples are NOT SHUFFLED!
"""
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

from datadings.writer import FileWriter
from datadings.tools import FrequencyPrinter
from datadings.tools import print_over
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


def iter_video_frames_opencv(path):
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


def iter_frames_with_fixpoints(frame_gen, experiments):
    for key, frame in frame_gen:
        yield key, frame, [ex[key] for ex in experiments]


def write_video(name_prefix, frame_gen, experiments, writer, printer,
                min_fixpoints=30, write_delta=10, max_fixpoint_age=60):
    tracker = LucasKanade()
    last_written = 0
    for key, frame in frame_gen:
        for s, experiment in enumerate(experiments):
            try:
                tracker.track(experiment[key], (s, key))
            except IndexError:
                continue
        for s, age in list(tracker.points.keys()):
            if key - age > max_fixpoint_age:
                tracker.points.pop((s, age))
        points = tracker.update(frame)
        if key - last_written < write_delta:
            continue
        groups = __group_points(points)
        tracked_experiments = [
            SaliencyExperiment(group, None)
            for group in groups
            if len(group) >= min_fixpoints
        ]
        if not tracked_experiments:
            continue
        success, data = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        if not success:
            continue
        jpegdata = data.tostring()
        item = SaliencyData(
            jpegdata,
            tracked_experiments,
            pt.join('ERB3_Stimuli', name_prefix + '_%06d' % key),
        )
        writer.write(item)
        last_written = key
        printer.update()


def write_sets(indir, outdir, shuffle=False):
    printer = FrequencyPrinter()
    mat = loadmat(pt.join(indir, 'coutrot_database1.mat'))
    clip_data = __parse_mat(mat['Coutrot_Database1'])
    with FileWriter(pt.join(outdir, 'Coutrot1.msgpack')) as writer:
        for path in os.listdir(pt.join(indir, 'ERB3_Stimuli')):
            path = pt.join(indir, 'ERB3_Stimuli', path)
            # TODO shuffle if possible
            if not path.endswith('.avi'):
                continue
            name = path.split(os.sep)[-1].split('.')[0]
            print_over('\r' + name)
            clip = name.split('.')[0]
            experiments = clip_data[clip]
            frame_gen = iter_video_frames_opencv(path)
            write_video(name, frame_gen, experiments, writer, printer)
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
        help='directory that contains Coutrot DB 1 files'
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
