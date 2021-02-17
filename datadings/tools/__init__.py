import sys
import os
import os.path as pt
from itertools import product
import threading as th
from queue import Queue
from queue import Full
from queue import Empty
import hashlib
from struct import Struct
from hashlib import blake2s
import inspect
from pathlib import Path

import requests
import gdown
import numpy as np
import tqdm


# noinspection PyIncorrectDocstring
def print_over(*args, **kwargs):
    """
    Wrapper around print that replaces the current line.
    It prints from the start of the line and clears remaining
    characters.
    Accepts the same kwargs as the print function.

    Parameters:
        flush: If True, flush after printing.
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
    monitor_interval = 0
    __call__ = tqdm.tqdm.update


def make_printer(bar_format=BAR_FORMAT, miniters=0,
                 mininterval=0.5, smoothing=0.1, **kwargs):
    """
    Convenience function to create
    `tqdm <https://tqdm.github.io/docs/tqdm/>`_ objects with some
    default arguments.

    Returns:
        tqdm.tqdm object.
    """
    return ProgressPrinter(
        bar_format=bar_format,
        miniters=miniters,
        mininterval=mininterval,
        smoothing=smoothing,
        **kwargs
    )


def path_append(path: Path, string: str):
    """
    Append a string to the name of a pathlib Path.

    Parameters:
        path: the path
        string: the bit to append

    Returns:
        Path with stuff appended

    Raises:
        :py:class:`ValueError` if path does not have a name,
        e.g., root ``/``.
    """
    return path.with_name(path.name + string)


def path_append_suffix(path: Path, suffix: str):
    """
    Appends the given suffix to the path
    if the path does not end with said suffix::

        >>> path_append_suffix(Path('some.file'), '.file')
        >>> Path('some.file')
        >>> path_append_suffix(Path('some.file'), '.txt')
        >>> Path('some.file.txt')

    Behaves like ``path_append``
    if suffix does not startwith ``'.'`` (dot)::

        >>> path_append_suffix(Path('some.file'), 'txt')
        >>> Path('some.filetxt')

    Parameters:
        path: the base path
        suffix: suffix to append if necessary

    Returns:
        Path that ends with suffix.
    """
    if path.suffix != suffix:
        return path_append(path, suffix)
    else:
        return path


def hash_md5hex(path, read_size=64*1024, progress=False):
    """
    Calculate the (hexadecimal) MD5 hash of a file.

    Parameters:
        path: File to hash.
        read_size: Read-ahead size.
        progress: If True, display progress.

    Returns:
        Hexadecimal MD5 hash as string.
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
    Load a text files of MD5 hashes.

    Parameters:
        path: Path to MD5 file.

    Returns:
        Dict of (file, hash) pairs.
    """
    with open(path, encoding='utf-8') as f:
        return dict(l.strip().split('  ')[::-1] for l in f)


# noinspection PyIncorrectDocstring
def hash_string(s: str, salt: bytes = b'', __struct=Struct('>Q')) -> int:
    """
    Hash a string using the blake2s algorithm.

    Parameters:
        s: the string
        salt: optional salt, max 8 bytes

    Returns:
        first 8 bytes of the hash, interpreted as big-endian uint64
    """
    return __struct.unpack_from(blake2s(s.encode('utf-8'), salt=salt).digest())[0]


# noinspection PyIncorrectDocstring
def hash_string_bytes(s: str, salt: bytes = b'', __struct=Struct('>Q')) -> bytes:
    """
    Hash a string using the blake2s algorithm.

    Parameters:
        s: the string
        salt: optional salt, max 8 bytes

    Returns:
        first 8 bytes of the hash
    """
    return blake2s(s.encode('utf-8'), salt=salt).digest()[:8]


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
    """
    Check if ``path`` is a file,
    otherwise download from ``url`` to ``path``.
    """
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
    """
    Run :py:func:``download_if_not_found`` for multiple files.

    See also:
        :py:func:`datadings.tools.prepare_indir`
    """
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
    """
    Verify the integrity of the given files.

    See also:
        :py:func:`datadings.tools.prepare_indir`
    """
    for _, meta in files.items():
        verify_file(meta, indir)


def locate_files(files, indir):
    """
    Returns a copy of ``files`` where paths are replaced with
    concrete paths located in ``indir``.

    See also:
        :py:func:`datadings.tools.prepare_indir`
    """
    return {name: dict(meta, path=pt.join(indir, meta['path']))
            for name, meta in files.items()}


def prepare_indir(files, args):
    """
    Prepare a directory for dataset creation.
    ``files`` specifies with files need be downloaded and/or
    integrity checked.
    It is a dict of file descriptions like these::

        files = {
            'train': {
                'path': 'dataset.zip',
                'url': 'http://cool.dataset/dataset.zip',
                'md5': '56ad5c77e6c8f72ed9ef2901628d6e48',
            }
        }

    Once downloads and/or verification have finished, the relative
    paths are replaced with concrete paths in ``args.indir``.

    Parameters:
        files: Dict of file descriptions.
        args: Parsed argparse arguments object with ``indir``
              and ``skip_verification`` arguments.

    Returns:
        Files with paths located in args.indir.
    """
    download_files_if_not_found(files, args.indir)
    if not args.skip_verification:
        verify_files(files, args.indir)
    return locate_files(files, args.indir)


def split_array(img, v_pixels, h_pixels, indices=(1, 2)):
    """
    Split/tile an image/numpy array in horizontal and vertical direction.

    Parameters:
        img: The image to split.
        h_pixels: Width of each tile in pixels.
        v_pixels: Height of each tile in pixels.
        indices: 2-tuple of indices used to calculate number of tiles.

    Returns:
        Yields single tiles from the image as arrays.
    """
    i_ = np.arange(img.shape[indices[0]]) // v_pixels
    j_ = np.arange(img.shape[indices[1]]) // h_pixels
    for i, j in product(np.unique(i_), np.unique(j_)):
        yield img[:, i_ == i][:, :, j_ == j]


def tiff_to_nd_array(file_path, type=np.uint8):
    """
    Decode a TIFF image and returns all contained subimages as numpy array.
    The first dimension of the array indexes the subimages.

    Warning:
        Requires geo (GDAL) extra!

    Parameters:
        file_path: Path to TIFF file.
        type: Output dtype.

    Returns:
        TIFF image as numpy array.
    """
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

    Parameters:
        gen: Generator to yield from.
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

    Parameters:
        question: String that is presented to the user.
        default: Presumed answer if the user just hits <Enter>.
                 Must be one of ``prompts`` or ``None`` (meaning
                 an answer is required of the user).
        answers: Answers the user can give.

    Returns:
        One of ``prompts``.
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


def document_keys(
        typefun,
        block='Important:',
        prefix='Samples have the following keys:',
        postfix='',
):
    """
    Extract the keys that samples created by a type function have
    create a documentation string that lists them.
    For example, it produces the following documentation for
    :py:func:`ImageClassificationData <datadings.sets.types.ImageClassificationData>`::

        {block}
            {prefix}

            - ``"key"``
            - ``"image"``
            - ``"label"``

            {postfix}

    Parameters:
        typefun: Type function to analyze.
        block: Type of block to use. Defaults to "Important:".
        prefix: Text before parameter list.
        postfix: Text after parameter list.
    """
    sig = inspect.signature(typefun)
    sample = typefun(*((1,)*len(sig.parameters)))
    return (
        '{block}\n'
        + '    {prefix}\n\n    - '
        + ('\n    - '.join('``"%s"``' % k for k in sample))
        + '\n{postfix}'
    ).format(block=block, prefix=prefix, postfix=postfix)
