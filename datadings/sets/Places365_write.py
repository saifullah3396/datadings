"""Create Places365 data set files. You can choose between any combination of
 - high or low resolution images and
 - standard or challenge (extended) training data set

The data set is described here:
    http://places2.csail.mit.edu/index.html
"""
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

import os
import os.path as pt
import random
import tarfile

from ..tools import download_if_not_found
from ..writer import FileWriter
from .Places365 import CLASS_TO_ID
from . import (
    ImageClassificationData,
    ImageData,
)


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
    if split == "training":
        fmt_str = "train_{size}_places365{train_select}.tar"
    elif split == "validation":
        fmt_str = "val_{size}.tar"
    elif split == "testing":
        fmt_str = "test_{size}.tar"
    else:
        assert False
    return fmt_str.format(**fmt_kwargs)


def _download_and_extract(split, indir, challenge, low_res):
    tar_fn = _images_tar_fn(split, challenge=challenge, low_res=low_res)
    tar_path = pt.join(indir, tar_fn)
    download_if_not_found(BASE_URL + tar_fn, tar_path)
    return tar_path


def _write_set(data_tar, generator, data_cls, out_path, shuffle):
    if shuffle:
        generator = list(generator)
        random.shuffle(generator)
    with FileWriter(out_path) as writer:
        for member_, data_args in generator:
            bytes_ = data_tar.extractfile(member_).read()
            writer.write(data_cls(
                bytes_,
                *data_args,
                member_.name
            ))


def _yield_from_training_folder_structure(data_tar):
    for member in data_tar:
        if not member.isfile() or not member.name.endswith(".jpg"):
            continue
        label = "/".join(member.name.split(os.sep)[2:-1])
        yield member, (CLASS_TO_ID[label],)


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
        if classes is not None:
            yield member, (classes[pt.basename(member.name)],)
        else:
            yield member, tuple()


def _write_training_set(indir, outdir, challenge, low_res, shuffle):
    tar_path = _download_and_extract("training", indir, challenge, low_res)
    out_path = pt.join(outdir, "%s.msgpack" % "training")
    with tarfile.open(tar_path, "r") as tar:
        gen = _yield_from_training_folder_structure(tar)
        _write_set(tar, gen, ImageClassificationData, out_path, shuffle)


def _write_validation_set(indir, outdir, meta_tar, challenge, low_res, shuffle):
    tar_path = _download_and_extract("validation", indir, challenge, low_res)
    out_path = pt.join(outdir, "%s.msgpack" % "validation")
    with tarfile.open(tar_path, "r") as data_tar:
        gen = _yield_from_meta_tar_files_list(data_tar, meta_tar,
                                              "places365_val.txt")
        _write_set(data_tar, gen, ImageClassificationData, out_path, shuffle)


def _write_testing_set(indir, outdir, meta_tar, challenge, low_res, shuffle):
    tar_path = _download_and_extract("testing", indir, challenge, low_res)
    out_path = pt.join(outdir, "%s.msgpack" % "testing")
    with tarfile.open(tar_path, "r") as data_tar:
        gen = _yield_from_meta_tar_files_list(data_tar, meta_tar,
                                              "places365_test.txt")
        _write_set(data_tar, gen, ImageData, out_path, shuffle)


def write_sets(indir, outdir, challenge, low_res, shuffle=True):
    meta_tar_fn = _meta_tar_fn(challenge)
    meta_tar_path = pt.join(indir, meta_tar_fn)
    download_if_not_found(BASE_URL + meta_tar_fn, meta_tar_path)
    _write_training_set(indir, outdir, challenge, low_res, shuffle)
    with tarfile.open(meta_tar_path, "r") as meta_tar:
        _write_validation_set(indir, outdir, meta_tar, challenge, low_res,
                              shuffle)
        _write_testing_set(indir, outdir, meta_tar, challenge, low_res, shuffle)


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
