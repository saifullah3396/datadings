"""Run a read benchmark on a given dataset file.
"""
import time
import os.path as pt

from ..reader import MsgpackReader
from ..reader import Shuffler
from ..tools import make_printer


def bench(infile, raw, shuffle, buffering):
    kwargs = {'buffering': buffering} if buffering else {}
    r = MsgpackReader(infile, **kwargs)
    if shuffle:
        r = Shuffler(r)
    printer = make_printer(desc='bench ' + pt.basename(infile), total=len(r))
    a = time.time()
    if raw:
        for _ in r.rawiter():
            printer()
    else:
        for _ in r:
            printer()
    d = time.time() - a
    n = printer.n
    s = n / d
    b = pt.getsize(infile) / d / 1024 / 1024
    printer.close()
    print('%s samples read in %.2f seconds, %.2f samples/s, %.2f MB/s'
          % (n, d, s, b), end='')


def main():
    from ..argparse import make_parser
    from ..argparse import argument_infile

    parser = make_parser(__doc__)
    argument_infile(parser)
    parser.add_argument(
        '-r', '--raw',
        help='Do not decode samples. '
             'This is representative of performance in a multi-process '
             'environment, where workers take over decoding.',
        action='store_true',
    )
    parser.add_argument(
        '-s', '--shuffle',
        help='Shuffle the reader.',
        action='store_true',
    )
    parser.add_argument(
        '-b', '--buffering',
        type=int,
        help='Buffer size of reader.',
    )
    args, unknown = parser.parse_known_args()
    bench(args.infile, args.raw, args.shuffle, args.buffering)


def entry():
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()


if __name__ == '__main__':
    entry()
