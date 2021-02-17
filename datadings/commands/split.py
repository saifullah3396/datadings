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
from ..writer import RawWriter


def split_dataset(infile, outfiles, splits, overwrite):
    reader = MsgpackReader(infile)
    if max(splits) >= len(reader):
        print('max split = %d >= %d = len(dataset)' % (max(splits), len(reader)))
        sys.exit(1)
    splits = list(splits) + [len(reader)]
    i = 1
    with reader:
        for outfile, split in zip(outfiles, splits):
            try:
                with RawWriter(outfile, overwrite=overwrite) as writer:
                    for i, (key, raw) in enumerate(reader.rawiter(yield_key=True), i):
                        writer.write(key, raw)
                        if i >= split:
                            break
            # user declined overwriting outfile
            except FileExistsError:
                pass
            # seek to split position in case user declined overwriting
            reader.seek(split)


def main():
    from ..tools.argparse import make_parser_simple
    from ..tools.argparse import argument_infile
    from ..tools.argparse import argument_outfiles
    from ..tools.argparse import argument_no_confirm

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
    args, unknown = parser.parse_known_args()

    infile = pt.abspath(args.infile)
    splits = args.split
    if sorted(splits) != splits:
        parser.print_usage()
        print('Splits positions must be in ascending order.')
        sys.exit(1)
    if min(splits) < 1:
        parser.print_usage()
        print('Split positions must be >= 1.')
        sys.exit(1)

    outfiles = args.outfiles
    if outfiles is None:
        root, ext = pt.splitext(infile)
        outfiles = ['%s-%d%s' % (root, i, ext) for i in range(len(splits)+1)]
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
