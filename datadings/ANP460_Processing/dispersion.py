import numpy as np


def _check_contiguous(gaze):
    samples = gaze[:, 0]
    valid_frame = (samples.ptp() > 0.05) and (samples.ptp() < 0.5)
    consistency = np.all(np.diff(samples)<0.04)
    return valid_frame & consistency

def _radius(gaze):
    return max(gaze[:, 1:3].ptp(axis=0)) / 2.

def _outer_circle(i, span, n, gaze, r_drift):
    for j in range(i + span + 1, n):
        if (_radius(gaze[i:j]) > r_drift) | (not _check_contiguous(gaze[i:j])) | (j == n-1):
            pos = gaze[i:j - 1, 1:3].mean(axis=0)
            x = [pos[0], pos[1]]
            i = j - 1
            return i, x

def dispersion(gaze, r_initial=20, r_drift=30, time=False):
    fixations = np.empty((1,2))
    n = gaze.shape[0]
    i = 0
    span = 3
    while i < n-3:
        while span < 15:
            if _check_contiguous(gaze[i:i + span]):
                if (_radius(gaze[i:i+span]) < r_initial) and (i+span+1<n):
                    i, x = _outer_circle(i, span, n, gaze, r_drift)
                    fixations = np.vstack((fixations, x))
                else:
                    break
            else:
                span += 1
        i += 1
        span = 3
    return fixations[1:,:]