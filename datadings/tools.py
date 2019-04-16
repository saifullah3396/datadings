from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

import time
import sys
import os
import os.path as pt
from itertools import product

import wget
import numpy as np
import tqdm


string_types = (type(b''), type(u''))


def print_over(*args, **kwargs):
    """ Wrapper around print that replaces the current line.
        It prints from the start of the line and clears remaining
        characters.
        Accepts the same kwargs as the print function.

        @param flush: if True, flush after printing
    """
    end = kwargs.pop('end', '\n')
    kwargs['end'] = ''
    flush = kwargs.pop('flush', False)
    stream = kwargs.pop('file', sys.stdout)
    # return cursor to front and print
    print('\r', *args, **kwargs)
    # clear rest of the line
    print('\033[K', end=end)
    if flush:
        stream.flush()


BAR_FORMAT = '{desc} {percentage:3.0f}% {elapsed}<{remaining}, {rate_fmt}{postfix}'


class ProgressPrinter(tqdm.tqdm):
    def __call__(self, **kwargs):
        self.set_postfix(refresh=False, **kwargs)
        self.update()


def make_printer(bar_format=BAR_FORMAT, miniters=0,
                 mininterval=0.5, smoothing=0.1, **kwargs):
    tqdm.tqdm.monitor_interval = 0
    p = ProgressPrinter(bar_format=bar_format, miniters=miniters,
                        mininterval=mininterval, smoothing=smoothing,
                        **kwargs)
    return p


def find_best_unit(value, multiples, units):
    for m, unit in zip(multiples, units):
        if value > m:
            value /= m
        else:
            return value, unit


def find_byte_unit(value):
    return find_best_unit(value, [1024]*5, ['B', 'KB', 'MB', 'GB', 'TB'])


def format_time(seconds):
    parts = []
    for divisor in (86400, 3600, 60, 1):
        t = seconds // divisor
        seconds -= t * divisor
        parts.append(t)
    units = ['days', 'hours', 'minutes', 'seconds']
    for unit in units:
        if parts[0] > 0:
            break
        parts.pop(0)
    s = ':'.join('%02d' % p for p in parts) + ' ' + unit
    if len(s) > 1:
        s.lstrip('0')
    return s


def _estimate_speed(snapshots):
    if not snapshots:
        return None
    time_a, rem_a = snapshots[0]
    time_b, rem_b = snapshots[-1]
    loaded = rem_a - rem_b
    seconds = time_b - time_a
    if seconds <= 1:
        return None
    return loaded / seconds


def download_if_not_found(url, path):
    if not pt.exists(path):
        parent = pt.dirname(path)
        if parent and not pt.exists(parent):
            os.makedirs(parent, mode=0o777)
        snapshots = []
        filename = pt.basename(path)
        fmt_first = ' %s / %s      '
        fmt = ' %s / %s, %s/s, %s left      '

        def _progress(current, total, width=80, _snapshots=snapshots,
                      _fmt=fmt, _fmt_first=fmt_first):
            s_current = '%7.2f %s' % find_byte_unit(current)
            s_total = '%.2f %s' % find_byte_unit(total)
            rem = total - current
            _snapshots.append((time.time(), rem))
            _snapshots = _snapshots[:-10]
            speed = _estimate_speed(_snapshots)
            if not speed:
                return _fmt_first % (s_current, s_total)
            s_rem = format_time(rem / speed)
            s_speed = '%6.1f %s' % find_byte_unit(speed)
            return _fmt % (s_current, s_total, s_speed, s_rem)

        print('downloading', filename, '-->', path)
        wget.download(url, path, bar=_progress)
        print()


def split_array(img, h_pixels, v_pixels, indices=(1, 2)):
    i_ = np.arange(img.shape[indices[0]]) // v_pixels
    j_ = np.arange(img.shape[indices[1]]) // h_pixels
    for i, j in product(np.unique(i_), np.unique(j_)):
        yield img[:, i_ == i][:, :, j_ == j]


def tiff_to_nd_array(file_path, type=np.int8):
    from osgeo import gdal
    dataset = gdal.Open(file_path, gdal.GA_ReadOnly)
    return np.array([dataset.GetRasterBand(idx+1).ReadAsArray()
                        for idx in range(dataset.RasterCount)]).astype(type)
