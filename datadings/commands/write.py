"""Create dataset files.
The following datasets are supported:

{datasets}

The help text for each dataset contains more information about requirements
and possible options.
"""
import os
import os.path as pt
import sys
import importlib
from collections import OrderedDict


def find_writers():
    import datadings
    return [
        mod.partition('_')[0]
        for mod in os.listdir(pt.join(pt.dirname(datadings.__file__), 'sets'))
        if mod.endswith('_write.py')
    ]


def format_writers(writers):
    order = OrderedDict()
    first_char = ''
    for w in writers:
        if w.lower()[0] != first_char:
            first_char = w.lower()[0]
            order[first_char] = []
        order[first_char].append(w)
    return '\n'.join('%s:\n    %s' % (char.upper(), ', '.join(ws))
                     for char, ws in order.items())


def main():
    from datadings.argparse import make_parser

    writers = sorted(find_writers())

    parser = make_parser(__doc__.format(datasets=format_writers(writers)))
    parser.add_argument(
        'dataset',
        choices=writers,
        metavar='dataset',
        help='Dataset to write.'
    )
    args, unknown = parser.parse_known_args()

    sys.argv.pop(0)
    writer = importlib.import_module('datadings.sets.' + args.dataset + '_write')
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
