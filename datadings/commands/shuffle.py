"""Shuffle an existing dataset file.
"""
import sys
import os.path as pt

from ..reader import MsgpackReader
from ..reader import Shuffler
from ..writer import RawWriter


def shuffle(infile, outfile):
    r = MsgpackReader(infile)
    shuffler = Shuffler(r)
    with RawWriter(outfile, total=len(r)) as writer:
        for key, raw in shuffler.iter(yield_key=True, raw=True):
            writer.write(key, raw)


def main():
    from ..tools.argparse import make_parser_simple
    from ..tools.argparse import argument_infile
    from ..tools.argparse import argument_outfile_positional

    parser = make_parser_simple(__doc__)
    argument_infile(parser)
    argument_outfile_positional(parser)
    args, unknown = parser.parse_known_args()
    infile = pt.abspath(args.infile)
    outfile = pt.abspath(args.outfile)
    if infile == outfile:
        parser.print_usage()
        print('Input and output file must be different.')
        sys.exit(1)
    shuffle(infile, outfile)


def entry():
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()


if __name__ == '__main__':
    entry()
