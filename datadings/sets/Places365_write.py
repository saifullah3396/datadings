"""Create Places365 data set files.
You can choose between any combination of

- high or low resolution images and
- standard or challenge (extended) training data set

This tool will look for the following files in the input directory
depending on the chosen version and download them if necessary:

- standard (large)

    - train_large_places365standard.tar (105 GB)
    - val_large.tar (2.1 GB)
    - test_large.tar (19 GB)
- standard (small)

    - train_256_places365standard.tar (24 GB)
    - val_256.tar (501 MB)
    - test_256.tar (4.4 GB)
- challenge (large)

    - train_large_places365challenge.tar (476 GB)
    - val_large.tar (2.1 GB)
    - test_large.tar (19 GB)
- challenge (small)

    - train_256_places365challenge.tar (108 GB)
    - val_256.tar (501 MB)
    - test_256.tar (4.4 GB)

See also:
    http://places2.csail.mit.edu/index.html

Important:
    For performance reasons shuffling is not available. It is recommended
    to use the datadings-shuffle command to create a shuffled copy.
"""
import os
import os.path as pt
import tarfile
import io

from ..tools import download_files_if_not_found
from ..tools import verify_files
from ..tools import yield_threaded
from ..writer import FileWriter
from . import ImageClassificationData
from . import ImageData
from .Places365 import CLASS_TO_ID
from ..tools import document_keys


__doc__ += document_keys(ImageClassificationData)


READ_SIZE = 4 * 1024 * 1024


BASE_URL = "http://data.csail.mit.edu/places/places365/"


def file_spec(path, md5, total=None):
    spec = {"url": BASE_URL + path, "path": path, "md5": md5}
    if total is not None:
        spec["total"] = total
    return spec


FILES_META = {
    "meta": file_spec("filelist_places365-standard.tar",
                      "35a0585fee1fa656440f3ab298f8479c"),
}


FILES_LARGE_VAL_TEST = {
    "validation": file_spec("val_large.tar",
                            "9b71c4993ad89d2d8bcbdc4aef38042f", 36500),
    "testing": file_spec("test_large.tar",
                         "41a4b6b724b1d2cd862fb3871ed59913", 328500),
    **FILES_META
}


FILES_256_VAL_TEST = {
    "validation": file_spec("val_256.tar",
                            "e27b17d8d44f4af9a78502beb927f808", 36500),
    "testing": file_spec("test_256.tar",
                         "f532f6ad7b582262a2ec8009075e186b", 328500),
    **FILES_META
}


FILES_LARGE_STANDARD = {
    "training": file_spec("train_large_places365standard.tar",
                          "67e186b496a84c929568076ed01a8aa1", 1803460),
    **FILES_LARGE_VAL_TEST
}


FILES_LARGE_CHALLENGE = {
    "training": file_spec("train_large_places365challenge.tar",
                          "605f18e68e510c82b958664ea134545f", 8000000),
    **FILES_LARGE_VAL_TEST
}


FILES_256_STANDARD = {
    "training": file_spec("train_256_places365standard.tar",
                          "53ca1c756c3d1e7809517cc47c5561c5", 1803460),
    **FILES_256_VAL_TEST
}


FILES_256_CHALLENGE = {
    "training": file_spec("train_256_places365challenge.tar",
                          "741915038a5e3471ec7332404dfb64ef", 8000000),
    **FILES_256_VAL_TEST
}


# (large/256, standard/challenge)
FILES = {
    (False, False): FILES_LARGE_STANDARD,
    (False, True): FILES_LARGE_CHALLENGE,
    (True, False): FILES_256_STANDARD,
    (True, True): FILES_256_CHALLENGE,
}


def get_files(challenge, low_res):
    return FILES[(low_res, challenge)]


def _write_set(generator, data_cls, out_path, total, overwrite):
    try:
        with FileWriter(out_path, total=total, overwrite=overwrite) as writer:
            for member, data, data_args in generator:
                writer.write(data_cls(
                    member.name,
                    data,
                    *data_args,
                ))
    except FileExistsError:
        pass


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
    for line in io.TextIOWrapper(fd, encoding="utf-8").readlines():
        try:
            image_fn, class_id = line.split()
            classes[image_fn] = int(class_id),  # put tuples for later
        except ValueError:
            break  # unlabeled data
    for member in data_tar:
        if not member.isfile() or not member.name.endswith(".jpg"):
            continue
        data = data_tar.extractfile(member).read()
        # either label in tuple or empty tuple
        label = classes.get(pt.basename(member.name), ())
        yield member, data, label


def _write_training_set(indir, outdir, args):
    files = get_files(args.challenge, args.low_res)["training"]
    tar_path = pt.join(indir, files["path"])
    out_path = pt.join(outdir, "training.msgpack")
    with tarfile.open(tar_path, "r", bufsize=READ_SIZE) as tar:
        gen = yield_threaded(_yield_from_training_folder_structure(tar))
        _write_set(gen, ImageClassificationData, out_path, files["total"],
                   args.no_confirm)


def _write_validation_set(indir, outdir, meta_tar, args):
    files = get_files(args.challenge, args.low_res)["validation"]
    tar_path = pt.join(indir, files["path"])
    out_path = pt.join(outdir, "validation.msgpack")
    with tarfile.open(tar_path, "r", bufsize=READ_SIZE) as data_tar:
        gen = yield_threaded(_yield_from_meta_tar_files_list(
            data_tar, meta_tar, "places365_val.txt"
        ))
        _write_set(gen, ImageClassificationData, out_path, files["total"],
                   args.no_confirm)


def _write_testing_set(indir, outdir, meta_tar, args):
    files = get_files(args.challenge, args.low_res)["testing"]
    tar_path = pt.join(indir, files["path"])
    out_path = pt.join(outdir, "testing.msgpack")
    with tarfile.open(tar_path, "r", bufsize=READ_SIZE) as data_tar:
        gen = yield_threaded(_yield_from_meta_tar_files_list(
            data_tar, meta_tar, "places365_test.txt"
        ))
        _write_set(gen, ImageData, out_path, files["total"],
                   args.no_confirm)


def write_sets(indir, outdir, args):
    files = get_files(args.challenge, args.low_res)
    download_files_if_not_found(files, indir)
    if not args.skip_verification:
        verify_files(files, indir)
    meta_tar_path = pt.join(indir, files["meta"]["path"])
    _write_training_set(indir, outdir, args)
    with tarfile.open(meta_tar_path, "r", bufsize=READ_SIZE) as meta_tar:
        _write_validation_set(indir, outdir, meta_tar, args)
        _write_testing_set(indir, outdir, meta_tar, args)


def main():
    from ..tools.argparse import make_parser

    parser = make_parser(__doc__, shuffle=False)
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
    write_sets(args.indir, outdir, args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
