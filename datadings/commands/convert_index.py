"""Convert the legacy index of dataset a to the new style.
"""
from pathlib import Path

from ..index import legacy_load_index
from ..index import write_keys
from ..index import write_key_hashes
from ..index import write_bloom_filter
from ..index import write_offsets


def convert_index(path, outdir):
    path = Path(path)
    # remove .index suffix, write functions implicitly add correct suffix
    if path.suffix == '.index':
        path = path.with_suffix('')
    keys, positions = legacy_load_index(path)
    outpath = (outdir or path.parent) / path.name
    write_keys(keys, outpath)
    write_key_hashes(keys, outpath)
    write_bloom_filter(keys, outpath)
    write_offsets(positions, outpath)


def main():
    from ..tools.argparse import make_parser_simple
    from ..tools.argparse import argument_infile
    from ..tools.argparse import argument_outdir

    parser = make_parser_simple(__doc__)
    argument_infile(parser)
    argument_outdir(parser)
    args, unknown = parser.parse_known_args()
    convert_index(args.infile, args.outdir)


def entry():
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()


if __name__ == '__main__':
    entry()
