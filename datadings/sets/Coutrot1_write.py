"""Create Coutrot 1 data set files.

This tool will look for the following files in the input directory
and download them if necessary:

- coutrot_database1.mat
- ERB3_Stimuli.zip

See also:
    http://antoinecoutrot.magix.net/public/databases.html

Note:
    ERB3_Stimuli.zip must be downloaded manually as it is hosted on mega.nz.

Warning:
    OpenCV 2.4+ is required to create this dataset.
    If you are unsure how to install OpenCV you can use pip:

        pip install opencv-python

Important:
    Samples are extracted from video frames and thus NOT SHUFFLED!
    If this is not desirable the datadings-shuffle command can be used to
    create a shuffled copy.
"""
import os
import os.path as pt
from math import floor
from math import log
import zipfile
from collections import defaultdict
from simplejpeg import encode_jpeg

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
import numpy as np

from ..writer import FileWriter
from ..tools import print_over
from . import SaliencyData
from . import SaliencyExperiment
from ..tools.matlab import loadmat
from ..tools.matlab import iter_fields
from ..tools import document_keys


__doc__ += document_keys(
    SaliencyData,
    postfix=document_keys(
        SaliencyExperiment,
        block='',
        prefix='Each experiment has the following keys:'
    )
)


THRESHOLD_GOOD = 1.
BASE_URL = 'http://antoinecoutrot.magix.net/public/assets/'
FILES = {
    'mat': {
        'path': 'coutrot_database1.mat',
        'url': BASE_URL+'coutrot_database1.mat',
        'md5': 'e32e408d4970e74607234df4133a4ae2',
    },
    'videos': {
        'path': 'ERB3_Stimuli.zip',
        'md5': 'e0007237c8e4cdae81f31e84ad9fb241',
    }
}


def _max_level(params, frame):
    """
    Compute a sensible maxlevel value for a frame, i.e.,
    ensure the smallest pyramid level is not too small.

    Parameters:
        params: Other tracker parameters.
        frame: Frame with shape (height, width, channels).

    Returns:
        Maxlevel as integer. At least 1.
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
        """
        Update the tracking result for a new frame.

        Parameters:
            frame: Next frame.

        Returns:
            Dict of (point, (x, y)) pairs.
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


def write_video(name_prefix, frame_gen, experiments, writer,
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
        jpegdata = encode_jpeg(frame, quality=95)
        item = SaliencyData(
            pt.join('ERB3_Stimuli', name_prefix + '_%06d' % key),
            jpegdata,
            tracked_experiments,
        )
        writer.write(item)
        last_written = key


def write_sets(files, indir, outdir, args):
    mat = loadmat(files['mat']['path'])
    clip_data = __parse_mat(mat['Coutrot_Database1'])
    writer = FileWriter(pt.join(outdir, 'Coutrot1.msgpack'),
                        overwrite=args.no_confirm)
    videozip = zipfile.ZipFile(files['videos']['path'])
    with videozip, writer:
        for name in videozip.namelist():
            if not name.endswith('.avi'):
                continue
            # extract the video file
            videozip.extract(name, path=indir)

            path = pt.join(indir, name)
            key = pt.splitext(pt.basename(name))[0]
            print_over('\r' + key)
            experiments = clip_data[key]
            frame_gen = iter_video_frames_opencv(path)
            write_video(name, frame_gen, experiments, writer)

            # video is done, delete file
            os.remove(path)


def main():
    from ..tools.argparse import make_parser
    from ..tools import prepare_indir

    parser = make_parser(__doc__, shuffle=False)
    args = parser.parse_args()
    outdir = args.outdir or args.indir

    files = prepare_indir(FILES, args)

    try:
        write_sets(files, args.indir, outdir, args)
    except FileExistsError:
        pass


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
