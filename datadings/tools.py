import sys
import os
import os.path as pt
from itertools import product
import threading as th
from queue import Queue
from queue import Full
from queue import Empty

import requests
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


DOWNLOAD_BAR = '{rate_fmt}, ' \
               '{n_fmt} of {total_fmt} ' \
               '({percentage:3.0f}%) ' \
               '{elapsed}<{remaining}'


def __requests_download(url, path, chunk_size=256*1024):
    part_path = path + '.part'
    resume_header = {}
    existing_size = 0
    if pt.exists(part_path):
        existing_size = os.stat(part_path).st_size
        resume_header['Range'] = 'bytes=%d-' % existing_size
    try:
        r = requests.get(
            url,
            headers=resume_header,
            stream=True,
            verify=False,
            allow_redirects=True
        )
    except requests.exceptions.RequestException:
        raise OSError('Could not connect to %s' % url) from None
    if r.status_code in (200, 206):
        total_bytes = int(r.headers.get('content-length', 0)) or None
        printer = make_printer(
            initial=existing_size,
            bar_format=DOWNLOAD_BAR,
            total=total_bytes,
            unit_scale=True,
            unit='B'
        )
        with printer, open(part_path, 'ab' if r.status_code == 206 else 'wb') as f:
            for chunk in r.iter_content(chunk_size):
                f.write(chunk)
                printer.update(len(chunk))
    else:
        raise OSError('Download error HTTP status %r' % r.status_code)
    r.close()
    os.rename(path + '.part', path)


def download_if_not_found(url, path):
    if not pt.exists(path):
        parent = pt.dirname(path)
        if parent and not pt.exists(parent):
            os.makedirs(parent, mode=0o777)
        filename = pt.basename(path)
        print('downloading', filename, '-->', path)
        try:
            __requests_download(url, path)
        except (ConnectionError, IOError, OSError) as e:
            print(e)
            sys.exit(1)
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


class Yielder(th.Thread):
    def __init__(self, gen, queue, end):
        super().__init__()
        self.daemon = True
        self.running = True
        self.gen = gen
        self.queue = queue
        self.end = end

    def run(self):
        for obj in self.gen:
            if not self.running:
                break
            while True:
                try:
                    self.queue.put(obj, timeout=1)
                    break
                except Full:
                    pass
        else:
            self.queue.put(self.end, timeout=1)

    def stop(self):
        self.running = False


def yield_threaded(gen):
    """
    Run a generator in a background thread and yield its
    output in the current thread.

    :param gen: generator
    """
    end = object()
    queue = Queue(maxsize=3)
    yielder = Yielder(gen, queue, end)
    try:
        yielder.start()
        while True:
            try:
                obj = queue.get(timeout=1)
                if obj is end:
                    break
                yield obj
            except Empty:
                pass
    finally:
        yielder.stop()
