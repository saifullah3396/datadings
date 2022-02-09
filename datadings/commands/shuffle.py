"""Shuffle an existing dataset file.
"""
import sys
import os.path as pt
import random

from ..reader import MsgpackReader
from ..reader import Shuffler
from ..reader import QuasiShuffler
from ..writer import RawWriter


def shuffle(infile, outfile, args):
    r = MsgpackReader(infile)
    n = len(r)
    if args.true_shuffle:
        shuffler = Shuffler(r)
    else:
        shuffler = QuasiShuffler(
            r,
            buf_size=args.buf_size,
            chunk_size=args.chunk_size,
            seed=random.randrange(2**32)
        )
    with RawWriter(outfile, total=n, overwrite=args.no_confirm) as writer:
        for key, raw in shuffler.iter(yield_key=True, raw=True):
            writer.write(key, raw)


def main():
    from ..tools.argparse import make_parser_simple
    from ..tools.argparse import argument_infile
    from ..tools.argparse import argument_no_confirm
    from ..tools.argparse import argument_outfile_positional

    parser = make_parser_simple(__doc__)
    argument_infile(parser)
    argument_outfile_positional(parser)
    argument_no_confirm(parser)
    parser.add_argument(
        '--true-shuffle',
        action='store_true',
        help='Use slower but more random shuffling algorithm'
    )
    parser.add_argument(
        '--buf-size',
        type=float,
        help='size of the shuffling buffer for fast shuffling; '
             'values less than 1 are interpreted as fractions of '
             'the dataset length; bigger values improve '
             'randomness, but use more memory'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        help='size of chunks read by the fast shuffling algorithm; '
             'bigger values improve performance, but reduce randomness'
    )
    args, unknown = parser.parse_known_args()
    infile = pt.abspath(args.infile)
    outfile = pt.abspath(args.outfile)
    if infile == outfile:
        parser.print_usage()
        print('Input and output file must be different.')
        sys.exit(1)
    shuffle(infile, outfile, args)


def entry():
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()


if __name__ == '__main__':
    entry()
