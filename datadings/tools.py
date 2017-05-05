from __future__ import print_function, division

import time
import sys


class FrequencyPrinter(object):
    """ Convenient printer for framerates.
        Call update every time a new frame is shown
        to regularly print the current framerate.
    """
    def __init__(self,
                 interval=2,
                 formatstring='%12d samples, %.2f samples/s           ',
                 printlines=False):
        """ @param interval: Interval in seconds between print output
            @param formatstring: String format used to print;
                                 must have exactly one float placeholder
            @param printlines: if True, print new results on new line;
                               if False, current line is reused
        """
        self.interval = interval
        if not printlines:
            formatstring = '\r'+formatstring
        self.formatstring = formatstring
        self.end = None if printlines else ''
        self.new_updates = 0
        self.total_updates = 0
        self.last_print = 0
        self.start = 0

    def update(self):
        """ Call update every time a new frame is shown
            to regularly print the current framerate.
        """
        self.new_updates += 1
        self.total_updates += 1
        now = time.time()
        if self.start is None:
            self.start = now
            self.last_print = now
        if now - self.last_print > self.interval:
            seconds = now - self.start
            print(self.formatstring % (self.total_updates,
                                       self.new_updates / seconds),
                  end='')
            sys.stdout.flush()
            self.last_print = now
            self.start = now
            self.new_updates = 0
