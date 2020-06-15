"""Run a read benchmark on a given dataset file.
"""
import time
import os.path as pt

from ..reader import MsgpackReader
from ..reader import DirectoryReader
from ..reader import Shuffler
from ..tools import make_printer


def bench(reader, args, num_bytes):
    printer = make_printer(desc='bench ' + pt.basename(args.infile), total=len(reader))
    if args.shuffle:
        reader = Shuffler(reader)
    a = time.time()
    if args.raw:
        for _ in reader.rawiter():
            printer()
    else:
        for _ in reader:
            printer()
    d = time.time() - a
    n = printer.n
    s = n / d
    b = num_bytes / d / 1024 / 1024
    printer.close()
    print('%s samples read in %.2f seconds, %.2f samples/s, %.2f MB/s'
          % (n, d, s, b), end='')


def bench_msgpack(args):
    kwargs = {'buffering': args.buffering} if args.buffering else {}
    r = MsgpackReader(args.infile, **kwargs)
    bench(r, args, pt.getsize(args.infile))


def bench_directory(args):
    r = DirectoryReader(
        args.infile,
        separator=args.separator,
        include=tuple(args.include),
        exclude=tuple(args.exclude),
        root_dir=args.root_dir,
    )
    bench(r, args, 0)


def main():
    from datadings.argparse import make_parser_simple
    from datadings.argparse import argument_infile

    parser = make_parser_simple(__doc__)
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
    parser.add_argument(
        '--separator',
        type=str,
        default='\t',
        help='Buffer size of reader.',
    )
    parser.add_argument(
        '--root-dir',
        type=str,
        default=None,
        help='Buffer size of reader.',
    )
    args, unknown = parser.parse_known_args()
    if args.infiles.endswith('.msgpack'):
        bench_msgpack(args)
    elif args.infiles.endswith('.zip'):
        raise NotImplementedError('ZIP benchmark not implemented yet')
    else:
        bench_directory(args)


def entry():
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()


if __name__ == '__main__':
    entry()
