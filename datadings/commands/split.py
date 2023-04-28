"""Splits one dataset into several smaller ones.

For example two split positions A and B produce three output files:

    [.....file1.....|A|.....file2.....|B|.....file3.....]

File 1 contains samples 0 to A-1.
File 2 contains samples A to B-1.
File 3 contains samples B to end of input.
"""
import sys
import os.path as pt

from ..reader import MsgpackReader
from ..tools.argparse import make_parser_simple
from ..tools.argparse import argument_infile
from ..tools.argparse import argument_outfiles
from ..tools.argparse import argument_no_confirm
from ..writer import RawWriter


def split_dataset(infile, outfiles, splits, overwrite):
    reader = MsgpackReader(infile)
    if max(splits) >= len(reader):
        print(f'max split = {max(splits)} >= {len(reader)} = len(dataset)')
        sys.exit(1)
    splits = list(splits) + [len(reader)]
    with reader:
        for outfile, start, stop in zip(outfiles, splits, splits[1:]):
            try:
                with RawWriter(outfile, overwrite=overwrite) as writer:
                    for key, raw in reader.iter(start=start, stop=stop, yield_key=True, raw=True):
                        writer.write(key, raw)
            # user declined overwriting outfile
            except FileExistsError:
                print(f'{outfile} exists, skipping')


def main():
    parser = make_parser_simple(__doc__)
    argument_infile(parser, help='File to split.')
    argument_outfiles(parser)
    parser.add_argument(
        'split',
        type=int,
        nargs='+',
        help='Index where infile is split.',
    )
    argument_no_confirm(parser)
    args = parser.parse_args()

    infile = pt.abspath(args.infile)
    splits = args.split
    if sorted(splits) != splits:
        parser.print_usage()
        print('Split positions must be in ascending order.')
        sys.exit(1)
    if min(splits) < 1:
        parser.print_usage()
        print('Split positions must be >= 1.')
        sys.exit(1)

    outfiles = args.outfiles
    if outfiles is None:
        root, ext = pt.splitext(infile)
        outfiles = [f'{root}-{i}{ext}' % (root, i, ext) for i in range(len(splits)+1)]
    outfiles = [pt.abspath(f) for f in outfiles]

    if infile in outfiles:
        parser.print_usage()
        print('Cannot overwrite input files.')
        sys.exit(1)

    split_dataset(infile, outfiles, splits, args.no_confirm)


def entry():
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()


if __name__ == '__main__':
    entry()
