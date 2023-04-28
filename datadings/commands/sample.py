"""Extract samples from a dataset.
"""
import sys
import os.path as pt

from ..reader import MsgpackReader
from ..reader import Shuffler
from ..tools.argparse import make_parser_simple
from ..tools.argparse import argument_infile
from ..tools.argparse import argument_outfile_positional
from ..writer import RawWriter


def sample(infile, outfile, number, strategy):
    reader = MsgpackReader(infile)
    if number > len(reader):
        print(f'number = {number} greater than {len(reader)} = len(dataset)')
    if strategy == 'random':
        reader = Shuffler(reader)
    with RawWriter(outfile) as writer:
        with reader:
            for i, (key, raw) in enumerate(reader.iter(yield_key=True, raw=True)):
                if i >= number:
                    break
                writer.write(key, raw)


def main():
    parser = make_parser_simple(__doc__)
    argument_infile(parser)
    argument_outfile_positional(parser)
    parser.add_argument(
        'number',
        type=int,
        help='Number of samples to extract.',
    )
    parser.add_argument(
        '-s', '--strategy',
        default='random',
        choices=('sequential', 'random'),
        help='Sampling strategy to use.',
    )
    args = parser.parse_args()
    infile = pt.abspath(args.infile)
    outfile = pt.abspath(args.outfile)
    if outfile == infile:
        parser.print_usage()
        print('Cannot write to input files.')
        sys.exit(1)
    sample(infile, outfile, args.number, args.strategy)


def entry():
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()


if __name__ == '__main__':
    entry()
