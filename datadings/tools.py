from __future__ import print_function, division

import time
import sys
import os
import os.path as pt

import wget
import numpy as np

from itertools import product


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


class FrequencyPrinter(object):
    """ Convenient printer for frequencies.
        Call update every time something happens
        to regularly print the current frequency.
    """
    def __init__(self,
                 interval=2,
                 formatstring='%12d samples, %.2f samples/s',
                 printlines=False):
        """ @param interval: Interval in seconds between print output
            @param formatstring: String format used to print;
                                 must have exactly one float placeholder
            @param printlines: if True, print new results on new line;
                               if False, current line is reused
        """
        self.interval = interval
        if not printlines:
            formatstring = formatstring
        self.formatstring = formatstring
        self.end = None if printlines else ''
        self.new_updates = 0
        self.total_updates = 0
        self.last_print = 0
        self.start = 0
        self._maxlen = 0

    def update(self, info=[]):
        """ Call update every time a new frame is shown
            to regularly print the current framerate.
            @param info: [str] additional information to be printed as suffix
        """
        self.new_updates += 1
        self.total_updates += 1
        now = time.time()
        if self.start is None:
            self.start = now
            self.last_print = now
        if now - self.last_print > self.interval:
            seconds = now - self.start
            print_over(
                " | ".join(
                    [self.formatstring % (self.total_updates, self.new_updates / seconds)]
                    + [str(i) for i in info]
                )
            , end=self.end, flush=True)
            self.last_print = now
            self.start = now
            self.new_updates = 0

    def print_total_updates(self):
        print_over('\r%d samples written' % self.total_updates)


class MovingAveragePrinter(object):
    # TODO cleanup + remove redundant code
    """ Convenient printer for moving averages.
        Call update every time something happens
        to regularly print the current frequency.
    """
    def __init__(
            self,
            interval=2,
            formatstring='{num:12d} updates, {freq:.2f} updates/s, avg {value}',
            printlines=False,
            alpha=0.9
    ):
        """ @param interval: Interval in seconds between print output
            @param formatstring: String format used to print;
                                 must have exactly one float placeholder
            @param printlines: if True, print new results on new line;
                               if False, current line is reused
        """
        self.interval = interval
        if not printlines:
            formatstring = formatstring
        self.formatstring = formatstring
        self.end = None if printlines else ''
        self.new_updates = 0
        self.total_updates = 0
        self.last_print = 0
        self.start = 0
        self._maxlen = 0
        self.alpha = alpha
        self.value = None

    def update(self, value=None):
        """ Call update every time a new frame is shown
            to regularly print the current framerate.
        """
        if self.value is None:
            self.value = value
        if value is not None:
            self.value = self.alpha*self.value + (1-self.alpha)*value
        self.new_updates += 1
        self.total_updates += 1
        now = time.time()
        if self.start is None:
            self.start = now
            self.last_print = now
        if now - self.last_print > self.interval:
            seconds = now - self.start
            print_over(self.formatstring.format(
                num=self.total_updates,
                freq=self.new_updates / seconds,
                value=self.value,
            ), end=self.end, flush=True)
            self.last_print = now
            self.start = now
            self.new_updates = 0

    def print_total_updates(self):
        print_over('\r%d samples written' % self.total_updates)


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

        def _progress(current, total, width=80, _snapshots=snapshots, _fmt=fmt, _fmt_first=fmt_first):
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


def pack_array(arr):
    return arr.dtype.char, arr.shape, arr.tobytes()


def split_array(img, h_pixels, v_pixels, indices=(1, 2)):
    i_ = np.arange(img.shape[indices[0]]) // v_pixels
    j_ = np.arange(img.shape[indices[1]]) // h_pixels
    for i, j in product(np.unique(i_), np.unique(j_)):
        yield img[:, i_ == i][:, :, j_ == j]

