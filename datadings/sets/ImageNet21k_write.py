"""Create ImageNet21k winter release data set files.

This tool will look for the following files in the input directory:

- winter21_whole.tar.gz

See also:
    http://image-net.org/download
    https://github.com/Alibaba-MIIL/ImageNet21K

Note:
    Registration is required to download this dataset.
    Please visit the website to download it.
    If you experience issues downloading you may consider using bittorrent:
    https://academictorrents.com/details/8ec0d8df0fbb507594557bce993920442f4f6477

Important:
    For performance reasons samples are read in same order as they are stored
    in the source tar files. It is recommended to use the datadings-shuffle
    command to create a shuffled copy.
"""
import os
import gzip
import json
import lzma
import pickle
import tarfile
import itertools as it
from pathlib import Path
from collections import OrderedDict
from multiprocessing.dummy import Pool as ThreadPool

from ..tools import document_keys
from ..tools import yield_process
from ..writer import FileWriter
from . import ImageNet21kData
from .ILSVRC2012_write import verify_image
from .ImageNet21k_synsets import SYNSETS
from .ImageNet21k_synsets import SYNSET_TREE_LIST
from .ImageNet21k_synsets import NUM_TRAIN_SAMPLES
from .ImageNet21k_synsets import NUM_VAL_SAMPLES
from .ImageNet21k_synsets import VAL_SAMPLES_PER_SYNSET


__doc__ += document_keys(ImageNet21kData)


FILES = {
    'tree': {
        'url': "https://miil-public-eu.oss-eu-central-1.aliyuncs.com/model-zoo/" \
                + "ImageNet_21K_P/resources/winter21/imagenet21k_miil_tree.pth",
        'path': 'imagenet21k_miil_tree.pth',
        'md5': 'ed3a7de5b90ace4999a99fca2a129d74',
    },
    'data': {
        'url': None,
        'path': 'winter21_whole.tar.gz',
        'md5': 'ab313ce03179fd803a401b02c651c0a2',
    }
}


def yield_samples(infile):
    # open the dataset file in streaming mode (r|gz)
    with tarfile.open(infile, mode='r|gz') as tar:
        for synset in tar:
            name = Path(synset.name).stem
            if synset.isfile() and name in SYNSETS:
                label = SYNSETS[name]
                label_tree = SYNSET_TREE_LIST[label]
                # use streaming mode (r|), since the parent file is not seekable
                synset_tar = tarfile.open(fileobj=tar.extractfile(synset), mode='r|')
                # sort images by name, as would be done by ls/glob
                # this ensures the first 50 images used for the validation set
                # are the same as in the Alibaba preprocessing script:
                # https://github.com/Alibaba-MIIL/ImageNet21K/blob/653ad536fde814e4cc7d0e19a48c8389e4ac2107/dataset_preprocessing/processing_script.sh#L51
                images = iter(sorted(
                    (info.name, synset_tar.extractfile(info).read())
                    for info in synset_tar
                ))
                val_images = it.islice(images, VAL_SAMPLES_PER_SYNSET)
                for name, data in val_images:
                    yield 'val', name, data, label, label_tree
                for name, data in images:
                    yield 'train', name, data, label, label_tree


def write_sets(files, outdir, args):
    gen = yield_process(yield_samples(files['data']['path']))

    def __verify_inner(item):
        split, key, data, label, label_tree = item
        data = verify_image(data, args.compress, colorsubsampling=args.subsampling)
        return split, ImageNet21kData(key, data, label, label_tree)

    trainfile = outdir / 'train.msgpack'
    valfile = outdir / 'val.msgpack'

    pool = ThreadPool(args.threads)
    train_writer = FileWriter(
        trainfile,
        total=NUM_TRAIN_SAMPLES,
        overwrite=args.no_confirm,
    )
    val_writer = FileWriter(
        valfile,
        total=NUM_VAL_SAMPLES,
        overwrite=args.no_confirm,
    )
    with train_writer, val_writer:
        for split, sample in pool.imap_unordered(__verify_inner, gen):
            if sample['image'] is None:
                print(f"{split} sample {sample['key']} failed verification")
            if split == 'train':
                train_writer.write(sample)
            elif split == 'val':
                val_writer.write(sample)
            else:
                raise ValueError(f'unknown split {split!r}')


def main():
    from ..tools.argparse import make_parser
    from ..tools.argparse import argument_threads
    from ..tools import prepare_indir

    from .ILSVRC2012_write import argument_compress
    from .ILSVRC2012_write import argument_subsampling

    parser = make_parser(__doc__, shuffle=False)
    argument_threads(parser, default=1)
    argument_compress(parser)
    argument_subsampling(parser)
    args = parser.parse_args()
    indir = Path(args.indir)
    outdir = Path(args.outdir or args.indir)

    files = prepare_indir(FILES, args)

    write_sets(files, outdir, args)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
