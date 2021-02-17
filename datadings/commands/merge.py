"""Merge two or more dataset files.

Available strategies:

- concat: Concat input files in the order they are given.
- random: Choose input file to read next sample from randomly, with
  probability depending on the relative size of datasets.
"""
import sys
import os.path as pt
import random

from ..reader import MsgpackReader
from ..reader import Shuffler
from ..writer import RawWriter


def merge_concat(infiles, outfile, shuffle):
    with RawWriter(outfile) as writer:
        for infile in infiles:
            reader = MsgpackReader(infile)
            if shuffle:
                reader = Shuffler(reader)
            with reader:
                for key, raw in reader.rawiter(yield_key=True):
                    writer.write(key, raw)


def cumsum(it):
    total = 0
    for x in it:
        total += x
        yield total


def setup_ranges(lens):
    total = sum(lens)
    ranges = [f / total for f in lens]
    return list(cumsum(ranges))


def select_set(ranges):
    rand = random.uniform(0, 1)
    for i, border in enumerate(ranges):
        if rand < border:
            return i
    return len(ranges) - 1


def merge_random(infiles, outfile, shuffle=False):
    readers = [MsgpackReader(f) for f in infiles]
    if shuffle:
        readers = [Shuffler(r) for r in readers]
    try:
        ranges = setup_ranges([len(r) for r in readers])
    except ZeroDivisionError:
        raise ValueError('zero samples found')
    iters = [r.rawiter(yield_key=True) for r in readers]
    print(len(iters), len(ranges))
    with RawWriter(outfile) as writer:
        while iters:
            i = select_set(ranges)
            try:
                writer.write(*next(iters[i]))
            except StopIteration:
                readers.pop(i)
                iters.pop(i)
                ranges = setup_ranges([len(r) for r in readers])


def main():
    from ..tools.argparse import make_parser_simple
    from ..tools.argparse import argument_infile
    from ..tools.argparse import argument_outfile_positional

    parser = make_parser_simple(__doc__)
    argument_infile(parser, nargs='+', help='Files to merge.')
    argument_outfile_positional(parser)
    parser.add_argument(
        '-s', '--strategy',
        default='random',
        choices=('concat', 'random'),
        help='Merging strategy to use.',
    )
    parser.add_argument(
        '--shuffle',
        action='store_true',
        help='Shuffle each dataset before merging.',
    )
    args, unknown = parser.parse_known_args()
    infiles = [pt.abspath(f) for f in args.infile + args.infiles]
    outfile = pt.abspath(args.outfile)
    if outfile in infiles:
        parser.print_usage()
        print('Cannot write to input files.')
        sys.exit(1)
    if args.strategy == 'random':
        merge_random(infiles, outfile, args.shuffle)
    elif args.strategy == 'concat':
        merge_concat(infiles, outfile, args.shuffle)


def entry():
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()


if __name__ == '__main__':
    entry()
