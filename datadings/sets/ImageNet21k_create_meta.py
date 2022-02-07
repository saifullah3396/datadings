"""
This module is used to convert/create required metadata for the
ImageNet21k dataset (winter release) to be included with datadings.

This tool will look for the following files in the input directory:

- imagenet21k_miil_tree.pth
- winter21_whole.tar.gz

Important:
    PyTorch is required to load imagenet21k_miil_tree.pth.
    The more lightweight CPU-only version is sufficient.

See also:
    http://image-net.org/download
    https://github.com/Alibaba-MIIL/ImageNet21K

Note:
    Registration is required to download winter21_whole.tar.gz.
    Please visit the website to download it.
    If you experience issues downloading you may consider using
    bittorrent:
    https://academictorrents.com/details/8ec0d8df0fbb507594557bce993920442f4f6477
"""
import os
import gzip
import json
import lzma
import pickle
import tarfile
from pathlib import Path
from collections import OrderedDict

import requests
import tqdm

from ..tools.argparse import make_parser
from ..tools import prepare_indir
from ..tools import query_user
from .ImageNet21k_write import FILES
from .ImageNet21k_synsets import NUM_VALID_SYNSETS


try:
    import torch
except ImportError:
    import warnings
    warnings.warn("PyTorch is required to run this tool.")
    # a dummy replacement for the torch module that raises when used
    class torch:
        @staticmethod
        def load(*_, **__):
            raise RuntimeError("PyTorch is required to run this tool.")


NUM_TOTAL_SYNSETS = 19167


def convert_semantic_tree(infile):
    with infile.open('rb') as f:
        tree = torch.load(f)
    # convert numpy scalars to python ints
    tree['class_tree_list'] = [[int(v) for v in l] for l in tree['class_tree_list']]
    # don't need redundant class list and child to parent mapping
    tree.pop('class_list')
    tree.pop('child_2_parent')
    return tree


def extract_synset_counts(infile):
    train = 0
    val = 0
    valid = 0
    with tqdm.tqdm(total=NUM_TOTAL_SYNSETS) as printer:
        # open the dataset file in streaming mode (r|gz)
        # non-streaming mode is basically impossible because of gzip compression
        with tarfile.open(infile, mode='r|gz') as tar:
            # count the number of files in each synset-tar
            for synset in tar:
                if synset.isfile():
                    name = Path(synset.name).stem
                    printer.set_description(name)
                    printer.update()
                    # use streaming mode (r|), since the parent file is not seekable
                    synset_tar = tarfile.open(fileobj=tar.extractfile(synset), mode='r|')
                    n = len(synset_tar.getmembers())
                    # only synsets with more than 500 samples are valid
                    # the first 50 are used for the validation set
                    # the rest are for training
                    if n > 500:
                        valid += 1
                        train += n - 50
                        val += 50
    assert valid == NUM_VALID_SYNSETS, \
        f'expected {NUM_VALID_SYNSETS} valid synsets, but found {valid}'
    return {'train': train, 'val': val}


def main():
    parser = make_parser(__doc__, shuffle=False)
    args = parser.parse_args()
    indir = Path(args.indir)
    outdir = Path(args.outdir or args.indir)

    files = prepare_indir(FILES, args)

    outfile = outdir / 'ImageNet21k_synsets.json.xz'
    if outfile.exists() and not args.no_confirm:
        answer = query_user(f'{outfile.name} exists, overwrite?')
        if answer == 'no':
            raise FileExistsError(outfile)
        elif answer == 'abort':
            raise KeyboardInterrupt(outfile)

    out = convert_semantic_tree(Path(files['tree']['path']))
    out.update(extract_synset_counts(Path(files['data']['path'])))

    with lzma.open(outfile, 'wt', preset=lzma.PRESET_EXTREME, encoding='utf-8') as fp:
        json.dump(out, fp, separators=(',', ':'))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
