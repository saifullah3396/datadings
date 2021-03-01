from pathlib import Path
import sqlite3
import io
from hashlib import md5
import itertools as it
from math import ceil
from math import sqrt
import multiprocessing as mp

from PIL import Image
import requests
import numpy as np
import zmq
from simplejpeg import decode_jpeg
from simplejpeg import decode_jpeg_header
from simplejpeg import encode_jpeg

from ..writer import RawWriter
from ..tools.msgpack import packb
from ..tools.msgpack import unpackb
# from ..tools import document_keys


# __doc__ += document_keys(ImageSegmentationData)


AWS_URL_PREFIX = 'https://multimedia-commons.s3-us-west-2.amazonaws.com'
FILES = {
    'yfcc': {
        'url': AWS_URL_PREFIX+'/tools/etc/yfcc100m_dataset.sql',
        'path': 'yfcc100m_dataset.sql',
        'md5': 'b8e3fa7f40ee2f309d63b8de8d755495',
    },
}
TOTAL = {
    'yfcc': 100_000_000,
}


def encode_fast(
        arr,
        quality=85,
        colorspace='RGB',
        colorsubsampling='422',
        target_size=(500, 375),
):
    target_pixels = target_size[0] * target_size[1]
    h, w = arr.shape[:2]
    # enforce full color resolution for small images
    if h*w <= 0.5*target_pixels:
        colorsubsampling = '444'
    # downscale big images
    if h*w > 1.5*target_pixels:
        s = max(w, h)
        r = max(target_size)/s
        w, h = int(round(r*w)), int(round(r*h))
        pil = Image.fromarray(arr, 'RGB')
        arr = np.array(pil.resize((w, h), resample=Image.LANCZOS))
    return encode_jpeg(
        arr,
        quality=quality,
        colorspace=colorspace,
        colorsubsampling=colorsubsampling,
    )


def decode_fast(data):
    try:
        # decode JPEGs at reduced size for speedup
        return data, False, decode_jpeg(
            data,
            'gray',
            fastdct=True,
            fastupsample=True,
            min_height=100,
            min_width=100,
            min_factor=1,
        )
    except ValueError:
        # use pillow in case anything goes wrong
        # and re-encode the image
        bio = io.BytesIO(data)
        im = Image.open(bio)
        data = encode_fast(np.array(im.convert('RGB')))
        return data, True, np.array(im.convert('L'))


def validate_image(data):
    try:
        data, compressed, im = decode_fast(data)
        # if the compressed image is very small
        # and less than 5% of all lines have significant variance
        # the image is most likely garbage
        if len(data) < 20000 and np.percentile(im.var(0), 95) < 50:
            return None, False
        return data, compressed
    except (ValueError, IOError, OSError):
        return None, False


BYTE_MAP = {'%02x' % v: '%x' % v for v in range(256)}


# noinspection PyDefaultArgument
def yfcc_hash(url, __bm=BYTE_MAP):
    h = md5(url.encode('utf-8')).hexdigest()
    return ''.join(__bm[h[x:x+2]] for x in range(0, 32, 2))


def generate_samples_from_db(path, table='yfcc100m_dataset'):
    conn = sqlite3.connect(path)
    # get column names
    result = conn.execute(f'select * from {table} limit 0').description
    cols = [c[0] for c in result]
    # some settings that hopefully speed up the query over NFS
    conn.execute(f'PRAGMA query_only = YES')
    conn.execute(f'PRAGMA journal_mode = OFF')
    conn.execute(f'PRAGMA locking_mode = EXCLUSIVE')
    conn.execute(f'PRAGMA page_size = 4096')
    conn.execute(f'PRAGMA mmap_size = {4*1024*1024}')
    conn.execute(f'PRAGMA cache_size = 10000')
    # retrieve rows in order
    result = conn.execute(f'select * from {table}')
    for row in result:
        row = dict(zip(cols, row))
        row['key'] = yfcc_hash(row['downloadurl'])
        yield row


def read(*paths):
    path = Path(*paths)
    if path.exists():
        with path.open('rb') as f:
            return f.read()
    return None


def download(*paths):
    return requests.get('/'.join(paths)).content


def is_image(row):
    return row['marker'] == 0


class SampleMaker:
    def __init__(
            self,
            data_directory,
            url_prefix,
            try_flickr,
            compress,
            target_pixels=375*500,
    ):
        self.data_directory = data_directory
        self.url_prefix = url_prefix
        self.try_flickr = try_flickr
        self.compress = compress
        self.target_pixels = target_pixels
        self.target_size = int(ceil(sqrt(target_pixels)))

    def get_data(self, row):
        kind = ('images',) if is_image(row) else ('videos', 'mp4')
        ext = '.jpg' if is_image(row) else '.mp4'
        h = row['key']
        parts = 'data', *kind, h[:3], h[3:6], h+ext
        data = None
        # try to read from disk first
        if self.data_directory is not None:
            data = read(self.data_directory, *parts)
        # next try AWS
        if data is None:
            data = download(self.url_prefix, *parts)
            # AWS returned XML instead of image
            if data.startswith(b'<?xml'):
                data = None
        # finally, try Flickr if enabled
        if data is None and self.try_flickr:
            data = download(row['downloadurl'])
        # early reject images based on data size
        # very small image are most likely garbage
        # 9218 bytes is a Flickr placeholder image
        if data is None or len(data) < 2600:  # or len(data) == 9218:
            data = None
        return data

    def create_sample(self, row):
        data = self.get_data(row)
        if data is None:
            return None
        data, compressed = validate_image(data)
        if data is None:
            return None
        if self.compress and not compressed:
            h, w, _, _ = decode_jpeg_header(data)
            if h * w > 0.5 * self.target_pixels:
                ts = self.target_size
                arr = decode_jpeg(data, min_width=ts, min_height=ts)
                data = encode_fast(arr)
        row['image' if is_image(row) else 'video'] = data
        # TODO get real rowid from original dataset
        return row


class Process(mp.Process):
    def __init__(self, **kwargs):
        super().__init__()
        self.daemon = True
        self._running = mp.Value('b')
        self.running = True

    @property
    def running(self):
        return self._running.value > 0

    @running.setter
    def running(self, value):
        self._running.value = bool(value)

    def stop(self):
        self.running = False


class Producer(Process):
    def __init__(self, dbpath, work_addr):
        super().__init__()
        self.dbpath = dbpath
        self.work_addr = work_addr

    def run(self):
        ctx = zmq.Context(io_threads=1)
        # noinspection PyUnresolvedReferences
        work = ctx.socket(zmq.PUSH)
        # noinspection PyUnresolvedReferences
        work.setsockopt(zmq.SNDHWM, 1000)
        work.bind(self.work_addr)
        gen = generate_samples_from_db(self.dbpath)
        while self.running:
            work.send(packb(next(gen)))


class Worker(Process):
    error_message = b'Break it down! Oh-oh. Stop! Error time!'

    def __init__(self, samplemaker, work_addr, result_addr):
        super().__init__()
        self.samplemaker = samplemaker
        self.work_addr = work_addr
        self.result_addr = result_addr

    def run(self):
        ctx = zmq.Context(io_threads=1)
        # noinspection PyUnresolvedReferences
        work = ctx.socket(zmq.PULL)
        work.connect(self.work_addr)
        # noinspection PyUnresolvedReferences
        result = ctx.socket(zmq.PUSH)
        result.connect(self.result_addr)
        # noinspection PyBroadException
        try:
            while self.running:
                row = unpackb(work.recv(copy=False))
                sample = self.samplemaker.create_sample(row)
                if sample is not None:
                    data = packb(sample)
                    result.send_multipart((sample['key'].encode('utf-8'), data))
        except:
            work.send_multipart(b'', self.error_message)


def iter_socket(sock):
    while True:
        key, sample = sock.recv_multipart(copy=False)
        yield str(key, encoding='utf-8'), sample


def start_processes(*procs):
    for proc in procs:
        proc.start()


def stop_processes(*procs):
    for proc in procs:
        proc.stop()
    for proc in procs:
        proc.terminate()


def write(files, outdir, args):
    work_addr = f'ipc://yfcc_work.ipc'
    result_addr = f'ipc://yfcc_result.ipc'
    ctx = zmq.Context(io_threads=1)
    # noinspection PyUnresolvedReferences
    result = ctx.socket(zmq.PULL)
    result.bind(result_addr)
    maker = SampleMaker(
        data_directory=args.data_directory,
        url_prefix=args.url_prefix,
        try_flickr=args.try_flickr,
        compress=args.compress,
    )
    producer = Producer(files['yfcc']['path'], work_addr)
    workers = [Worker(maker, work_addr, result_addr) for _ in range(args.threads)]
    start_processes(producer, *workers)

    try:
        result_iter = iter_socket(result)
        for i in range(1000):
            path = Path(outdir, 'yfcc.msgpack.%06d' % i)
            writer = RawWriter(path, total=100_000, overwrite=args.no_confirm)
            with writer:
                for key, sample in it.islice(result_iter, 100_000):
                    if sample == Worker.error_message:
                        raise RuntimeError('a worker encountered an error')
                    writer.write(key, sample)
    finally:
        stop_processes(producer, *workers)


def main():
    from ..tools.argparse import make_parser
    from ..tools.argparse import argument_threads
    from ..tools import prepare_indir

    parser = make_parser(__doc__, shuffle=False)
    parser.add_argument(
        '--data-directory',
        type=str,
        default=None,
        help='Directory to check for image/video files.'
    )
    parser.add_argument(
        '--kind',
        nargs='+',
        choices=('images', 'videos'),
        default=('images',),
        help='Kinds of files to include.'
    )
    parser.add_argument(
        '--selector',
        type=eval,
        default=lambda x: x,
        help='Lambda function to select samples.'
    )
    parser.add_argument(
        '--url-prefix',
        default=AWS_URL_PREFIX,
        help='Data url prefix.'
    )
    parser.add_argument(
        '--try-flickr',
        action='store_true',
        help='Try to download from Flickr '
             'if image is not available on AWS.'
    )
    parser.add_argument(
        '--compress',
        action='store_true',
        help='Re-compress images with quality 85 and 422 subsampling.'
    )
    argument_threads(parser, default=8, max_threads=1000)
    args = parser.parse_args()
    outdir = args.outdir or args.indir

    files = prepare_indir(FILES, args)
    write(files, outdir, args)


if __name__ == '__main__':
    main()
