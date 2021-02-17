"""Cat msgpack files.
"""
import os
import sys
import os.path as pt
import reprlib

from ..reader import MsgpackReader


def cat(infile, maxstring):
    r = reprlib.Repr()
    r.maxstring = maxstring
    r.maxdict = 2**32-1
    reader = MsgpackReader(infile)
    for sample in reader:
        print(r.repr(sample))


def main():
    from ..tools.argparse import make_parser_simple
    from ..tools.argparse import argument_infile

    parser = make_parser_simple(__doc__)
    argument_infile(parser, help='File to cat.')
    parser.add_argument(
        '-s', '--maxstring',
        default=40,
        type=int,
        help='max length of strings',
    )
    args, unknown = parser.parse_known_args()
    infile = pt.abspath(args.infile)
    cat(infile, args.maxstring)


def entry():
    try:
        try:
            main()
        except KeyboardInterrupt:
            pass
        finally:
            print()
    except BrokenPipeError:
        # Python flushes standard streams on exit; redirect remaining output
        # to devnull to avoid another BrokenPipeError at shutdown
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())


if __name__ == '__main__':
    entry()
