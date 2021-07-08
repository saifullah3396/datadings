"""Create dataset files.
The following datasets are supported:

{datasets}

The help text and documentation page for each dataset contains more
information about requirements and possible options. Run

``python -m datadings.commands.write [dataset] -h``

or

``datadings-write [dataset] -h``

to view them.
"""
import os
import os.path as pt
import sys
import importlib
from collections import OrderedDict

from natsort import natsorted


def find_writers():
    from .. import sets
    return [
        mod.partition('_')[0]
        for mod in os.listdir(pt.dirname(sets.__file__))
        if mod.endswith('_write.py')
    ]


def writer_link(w):
    return f':py:mod:`{w} <datadings.sets.{w}_write>`'


def format_writers(writers):
    order = OrderedDict()
    first_char = ''
    for w in writers:
        if w.upper()[0] != first_char:
            first_char = w.upper()[0]
            order[first_char] = []
        order[first_char].append(w)
    link = os.getenv('DOCSBUILD')
    return '\n'.join(
        '%s:\n    %s' % (char, ', '.join(map(writer_link, ws) if link else ws))
        for char, ws in order.items()
    )


def main():
    from ..tools.argparse import make_parser_simple

    writers = natsorted(find_writers())

    parser = make_parser_simple(
        __doc__.format(datasets=format_writers(writers)),
        add_help=False,
    )
    parser.add_argument(
        'dataset',
        nargs='?',
        choices=writers,
        metavar='dataset',
        help='Dataset to write.'
    )
    parser.add_argument(
        '-h', '--help',
        action='store_true',
        help='show this help message and exit'
    )
    args, unknown = parser.parse_known_args()

    if not args.dataset:
        if args.help:
            parser.print_help()
            sys.exit(0)
        else:
            parser.print_usage()
            sys.exit(1)

    sys.argv.pop(0)
    writer = importlib.import_module(
        '.%s_write' % args.dataset,
        'datadings.sets'
    )
    writer.main()


def entry():
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()


if __name__ == '__main__':
    entry()
