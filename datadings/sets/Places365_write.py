"""Create Places365 data set files.
You can choose between any combination of
    - high or low resolution images and
    - standard or challenge (extended) training data set

The data set is described here:
    http://places2.csail.mit.edu/index.html

Important:
    For performance reasons shuffling is not available.
    You can use datadings-shuffle to create a shuffled copy.

This tool will look for the following files in the input directory
depending on the chosen version and download them if necessary:
    - standard (large)
        - train_large_places365standard.tar (105 GB)
        - val_large (2.1 GB)
        - test_large (19 GB)
    - standard (small)
        - train_256_places365standard.tar (24 GB)
        - val_256.tar (501 MB)
        - test_256.tar (4.4 GB)
    - challenge (large)
        - train_large_places365challenge.tar (476 GB)
        - val_large (2.1 GB)
        - test_large (19 GB)
    - challenge (small)
        - train_256_places365challenge.tar (108 GB)
        - val_256.tar (501 MB)
        - test_256.tar (4.4 GB)
"""
import os
import os.path as pt
import tarfile

from ..tools import download_if_not_found
from ..tools import yield_threaded
from ..writer import FileWriter
from . import ImageClassificationData
from . import ImageData
from .Places365 import CLASS_TO_ID


TOTAL = {
    "training": 1803460,
    "challenge": 8000000,
    "validation": 36500,
    "testing": 328500,
}
READ_SIZE = 4 * 1024 * 1024
BASE_URL = "http://data.csail.mit.edu/places/places365/"


def _meta_tar_fn(challenge=False):
    if challenge:
        return "filelist_places365-challenge.tar"
    else:
        return "filelist_places365-standard.tar"


def _images_tar_fn(split, challenge=False, low_res=False):
    fmt_kwargs = {
        "size": "256" if low_res else "large",
        "train_select": "challenge" if challenge else "standard",
    }
    total = TOTAL[split]
    if split == "training":
        fmt_str = "train_{size}_places365{train_select}.tar"
        if challenge:
            total = TOTAL["challenge"]
    elif split == "validation":
        fmt_str = "val_{size}.tar"
    elif split == "testing":
        fmt_str = "test_{size}.tar"
    else:
        assert False
    return fmt_str.format(**fmt_kwargs), total


def _download(split, indir, challenge, low_res):
    tar_fn, total = _images_tar_fn(split, challenge=challenge, low_res=low_res)
    tar_path = pt.join(indir, tar_fn)
    download_if_not_found(BASE_URL + tar_fn, tar_path)
    return tar_path, total


def _write_set(generator, data_cls, out_path, total):
    with FileWriter(out_path, total=total) as writer:
        for member, data, data_args in generator:
            writer.write(data_cls(
                data,
                *data_args,
                member.name
            ))


def _yield_from_training_folder_structure(data_tar):
    for member in data_tar:
        if not member.isfile() or not member.name.endswith(".jpg"):
            continue
        label = "/".join(member.name.split(os.sep)[2:-1])
        data = data_tar.extractfile(member).read()
        yield member, data, (CLASS_TO_ID[label],)


def _yield_from_meta_tar_files_list(data_tar, meta_tar, files_list_fn):
    fd = meta_tar.extractfile(files_list_fn)
    classes = {}
    for line in fd:
        entries = line.decode("utf-8").strip().split()
        if len(entries) == 1:
            classes = None
            break  # unlabeled data
        image_fn, class_id = entries
        classes[image_fn] = int(class_id)
    for member in data_tar:
        if not member.isfile() or not member.name.endswith(".jpg"):
            continue
        data = data_tar.extractfile(member).read()
        if classes is not None:
            yield member, data, (classes[pt.basename(member.name)],)
        else:
            yield member, data, tuple()


def _write_training_set(indir, outdir, challenge, low_res):
    tar_path, total = _download("training", indir, challenge, low_res)
    out_path = pt.join(outdir, "%s.msgpack" % "training")
    with tarfile.open(tar_path, "r", bufsize=READ_SIZE) as tar:
        gen = yield_threaded(_yield_from_training_folder_structure(tar))
        _write_set(gen, ImageClassificationData, out_path, total)


def _write_validation_set(indir, outdir, meta_tar, challenge, low_res):
    tar_path, total = _download("validation", indir, challenge, low_res)
    out_path = pt.join(outdir, "%s.msgpack" % "validation")
    with tarfile.open(tar_path, "r", bufsize=READ_SIZE) as data_tar:
        gen = yield_threaded(_yield_from_meta_tar_files_list(
            data_tar, meta_tar, "places365_val.txt"
        ))
        _write_set(gen, ImageClassificationData, out_path, total)


def _write_testing_set(indir, outdir, meta_tar, challenge, low_res):
    tar_path, total = _download("testing", indir, challenge, low_res)
    out_path = pt.join(outdir, "%s.msgpack" % "testing")
    with tarfile.open(tar_path, "r", bufsize=READ_SIZE) as data_tar:
        gen = yield_threaded(_yield_from_meta_tar_files_list(
            data_tar, meta_tar, "places365_test.txt"
        ))
        _write_set(gen, ImageData, out_path, total)


def write_sets(indir, outdir, challenge, low_res):
    meta_tar_fn = _meta_tar_fn(challenge)
    meta_tar_path = pt.join(indir, meta_tar_fn)
    download_if_not_found(BASE_URL + meta_tar_fn, meta_tar_path)
    _write_training_set(indir, outdir, challenge, low_res)
    with tarfile.open(meta_tar_path, "r", bufsize=READ_SIZE) as meta_tar:
        _write_validation_set(indir, outdir, meta_tar, challenge, low_res)
        _write_testing_set(indir, outdir, meta_tar, challenge, low_res)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "indir",
        metavar="INPATH",
        help="directory that contains ILSRCV 2012 image directories and lists"
    )
    parser.add_argument(
        "-o", "--outdir",
        metavar="OUTPATH",
        help="output directory; defaults to indir"
    )
    parser.add_argument(
        "-l", "--low-res",
        action="store_true",
        help="Download the resized and cropped images (256x256). "
             "Default are images with minimum dimension of 512 and preserved "
             "aspect ratio."
    )
    parser.add_argument(
        "-c", "--challenge",
        action="store_true",
        help="Download the extended challenge training dataset. Validation and "
             "testing are the same."
    )
    args = parser.parse_args()
    outdir = args.outdir or args.indir
    write_sets(args.indir, outdir, args.challenge, args.low_res)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
