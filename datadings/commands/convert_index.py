"""Convert the legacy index of dataset a to the new style.
"""
from pathlib import Path

from ..tools import path_append
from ..tools import hash_md5hex
from ..index import legacy_load_index
from ..index import write_keys
from ..index import write_key_hashes
from ..index import write_filter
from ..index import write_offsets


def convert_index(path, outdir):
    path = Path(path)
    # remove .index suffix, write functions implicitly add correct suffix
    if path.suffix == '.index':
        path = path.with_suffix('')
    keys, positions = legacy_load_index(path)
    outpath = (outdir or path.parent) / path.name
    paths = [
        write_keys(keys, outpath),
        write_key_hashes(keys, outpath),
        write_filter(keys, outpath),
        write_offsets(positions, outpath),
    ]
    new_suffixes = set(path.suffix for path in paths)
    with path_append(outpath, '.md5').open('r', encoding='utf-8') as f:
        md5_lines = [
            line for line in f
            if Path(line.strip('\n')).suffix not in new_suffixes
        ]
    with path_append(outpath, '.md5').open('w', encoding='utf-8') as f:
        for line in md5_lines:
            f.write(line)
        for path in paths:
            f.write(f'{hash_md5hex(path)}  {path.name}\n')


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
