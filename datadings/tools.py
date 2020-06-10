import sys
import os
import os.path as pt
from itertools import product
import threading as th
from queue import Queue
from queue import Full
from queue import Empty
import hashlib

import requests
import gdown
import numpy as np
import tqdm


# noinspection PyIncorrectDocstring
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


def hash_md5hex(path, read_size=64*1024, progress=False):
    """
    Calculate the (hexadecimal) MD5 hash of a file.

    @param path: file path
    @param read_size: read-ahead size
    @param progress: if True, display progress
    @return: hexadecimal MD5 hash as string
    """
    printer = make_printer(
        bar_format=DOWNLOAD_BAR,
        total=os.stat(path).st_size,
        unit_scale=True,
        unit='B',
        disable=not progress,
    )
    with open(path, 'rb', read_size) as f, printer:
        md5 = hashlib.md5()
        while 1:
            data = f.read(read_size)
            if not data:
                break
            md5.update(data)
            printer.update(len(data))
        return md5.hexdigest()


def load_md5file(path):
    """
    Load a text-based "md5".

    :param path: path to md5 file
    :return: dict {file: hash}
    """
    with open(path, encoding='utf-8') as f:
        return dict(l.strip().split('  ')[::-1] for l in f)


DOWNLOAD_BAR = '{rate_fmt}, ' \
               '{n_fmt} of {total_fmt} ' \
               '({percentage:3.0f}%) ' \
               '{elapsed}<{remaining}'


def __download_requests_inner(url, path, chunk_size=256*1024):
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


def __download_requests(url, path):
    try:
        __download_requests_inner(url, path)
    except (ConnectionError, IOError, OSError) as e:
        print(e)
        sys.exit(1)
    print()


def __download_gdown(url, path):
    gdown.download(url, path)


def download_if_not_found(url, path):
    if not pt.exists(path):
        parent = pt.dirname(path)
        if parent and not pt.exists(parent):
            os.makedirs(parent, mode=0o777)
        filename = pt.basename(path)
        print('downloading', filename, '-->', path)
        if 'drive.google.com' in url:
            __download_gdown(url, path)
        else:
            __download_requests(url, path)


def download_files_if_not_found(files, indir):
    for _, meta in files.items():
        path = pt.join(indir, meta['path'])
        if meta.get('url'):
            download_if_not_found(meta['url'], path)


def verify_file(meta, indir):
    path = pt.join(indir, meta['path'])
    expected = meta['md5']
    name = pt.basename(meta['path'])
    print('Verifying ' + name)
    got = hash_md5hex(path, progress=True)
    if got != expected:
        print('could not verify MD5 for %s: expected %s, got %s'
              % (name, expected, got))
        sys.exit(1)


def verify_files(files, indir):
    for _, meta in files.items():
        verify_file(meta, indir)


def locate_files(files, indir):
    return {name: dict(meta, path=pt.join(indir, meta['path']))
            for name, meta in files.items()}


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
    def __init__(self, gen, queue, end, error):
        super().__init__()
        self.daemon = True
        self.running = True
        self.gen = gen
        self.queue = queue
        self.end = end
        self.error = error

    def run(self):
        try:
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
        finally:
            self.queue.put(self.error, timeout=1)

    def stop(self):
        self.running = False


def yield_threaded(gen):
    """
    Run a generator in a background thread and yield its
    output in the current thread.

    :param gen: generator
    """
    end = object()
    error = object()
    queue = Queue(maxsize=3)
    yielder = Yielder(gen, queue, end, error)
    try:
        yielder.start()
        while True:
            try:
                obj = queue.get(timeout=1)
                if obj is end:
                    break
                if obj is error:
                    raise RuntimeError()
                yield obj
            except Empty:
                pass
    finally:
        yielder.stop()


def query_user(question, default='yes', answers=('yes', 'no', 'abort')):
    """
    Ask user a question via input() and return their answer.

    Adapted from http://code.activestate.com/recipes/577097/

    :param question: String that is presented to the user.
    :param default: Presumed answer if the user just hits <Enter>.
                    Must be one of ``prompts`` or ``None`` (meaning
                    an answer is required of the user).
    :param answers: answers the user can give
    :returns: one of ``prompts``
    """
    if not(default is None or default in answers):
        raise ValueError("invalid default answer: '%s'" % default)

    valid = {'': default}
    for a in answers:
        valid.update({a[:i]: a for i in range(1, len(a) + 1)})

    prompt = '/'.join('%s' % (a[0].upper() if a == default else a[0])
                      for a in answers)
    prompt = question + ' [%s]' % (prompt + '/?')

    while 1:
        print(prompt, flush=True, end=' ')
        answer = valid.get(input().lower())
        if answer:
            return answer
        else:
            print('You can choose', ', '.join(answers), flush=True)
