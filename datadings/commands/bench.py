"""Run a read benchmark on a given dataset.

Support reading from msgpack files or directory trees.

Note:
    For directory trees, please refer to the DirectoryReader
    documentation for details on how to specify the dataset structure.
"""
import time
import os.path as pt

from ..reader import MsgpackReader
from ..reader import DirectoryReader
from ..reader import Shuffler
from ..tools import make_printer


def bench(readerfun, args):
    # measure setup time
    a = time.time()
    reader, num_bytes = readerfun(args)
    if args.shuffle:
        reader = Shuffler(reader)
    d = time.time() - a
    print('setup time:', d, 'seconds')

    # the actual benchmark
    printer = make_printer(desc='bench ' + pt.basename(args.infile), total=len(reader))
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
    if not num_bytes and hasattr(reader, 'bytes_read'):
        num_bytes = reader.bytes_read
    b = num_bytes / d / 1024 / 1024
    printer.close()
    print('%s samples read in %.2f seconds, %.2f samples/s, %.2f MB/s'
          % (n, d, s, b), end='')


def reader_msgpack(args):
    kwargs = {'buffering': args.buffering} if args.buffering else {}
    return MsgpackReader(args.infile, **kwargs), pt.getsize(args.infile)


def reader_directory(args):
    return DirectoryReader(
        args.infile,
        separator=args.separator,
        include=tuple(args.include),
        exclude=tuple(args.exclude),
        root_dir=args.root_dir,
    ), 0  # TODO total file size for directory


def main():
    from ..tools.argparse import make_parser_simple
    from ..tools.argparse import argument_infile

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
        help='MsgpackReader only: Buffer size of reader.',
    )
    parser.add_argument(
        '--separator',
        type=str,
        default='\t',
        help='DirectoryReader only: separator for file input mode.',
    )
    parser.add_argument(
        '--root-dir',
        type=str,
        default='',
        help='DirectoryReader only: root directory for file input mode.',
    )
    parser.add_argument(
        '--include',
        nargs='+',
        type=str,
        default=(),
        help='DirectoryReader only: Include patterns.',
    )
    parser.add_argument(
        '--exclude',
        nargs='+',
        type=str,
        default=(),
        help='DirectoryReader only: Exclude patterns.',
    )
    args, unknown = parser.parse_known_args()
    if args.infile.endswith('.msgpack'):
        bench(reader_msgpack, args)
    elif args.infile.endswith('.zip'):
        raise NotImplementedError('ZIP benchmark not implemented yet')
    else:
        bench(reader_directory, args)


def entry():
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()


if __name__ == '__main__':
    entry()
