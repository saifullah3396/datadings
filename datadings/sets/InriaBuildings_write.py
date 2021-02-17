"""Create InriaBuildings data set files.

This tool will look for the unpacked "AerialImageDataset"
directory in the input directory.

See also:
    https://project.inria.fr/aerialimagelabeling/contest/

Note:
    Registration is required to download this dataset. Please visit the
    website and follow the instructions to download and decompress it.

Important:
    Samples are NOT SHUFFLED! It is recommended to use the datadings-shuffle
    command to create a shuffled copy.
"""
import os.path as pt
import io

import numpy as np
from simplejpeg import encode_jpeg
from PIL import Image

from ..writer import FileWriter
from . import ImageData
from . import ImageSegmentationData
from .InriaBuildings import CROP_SIZE
from ..tools import split_array
from ..tools import tiff_to_nd_array
from ..tools import document_keys


__doc__ += document_keys(ImageSegmentationData)


def array2imagedata(array):
    if array.dtype == np.bool:
        bio = io.BytesIO()
        img = Image.fromarray(array, '1')
        img.save(bio, 'PNG', optimize=True)
        return bio.getvalue()
    else:
        array = np.ascontiguousarray(array.transpose((1, 2, 0)))
        return encode_jpeg(array, quality=95)


def write(writer, img, labels, filename=""):
    if labels is not None:
        writer.write(ImageSegmentationData(
            filename,
            array2imagedata(img),
            array2imagedata(labels),
        ))
    else:
        writer.write(ImageData(
            filename,
            array2imagedata(img),
        ))


def images_and_labels_iter(img_dir, label_dir, locations, ids):
    for location in locations:
        for id in ids:
            filename = "%s%s.tif" % (location, id)
            img_path = pt.join(img_dir, filename)
            train_img = tiff_to_nd_array(img_path, type=np.uint8)

            labels = None
            if label_dir is not None:
                label_path = pt.join(label_dir, filename)
                labels = tiff_to_nd_array(label_path, type=np.uint8)
                labels = labels[0] == 255
            yield filename, train_img, labels


def write_sets(indir, outdir, args, crop_size=(CROP_SIZE, CROP_SIZE)):
    dataset_dir = pt.join(indir, 'AerialImageDataset')
    train_dir = pt.join(dataset_dir, 'train')
    test_dir = pt.join(dataset_dir, 'test')
    train_img_dir = pt.join(train_dir, 'images')
    test_img_dir = pt.join(test_dir, 'images')
    train_gt_dir = pt.join(train_dir, 'gt')

    train_locations = ["vienna", "kitsap", "tyrol-w", "chicago", "austin"]
    test_locations = ["bellingham", "bloomington", "innsbruck",
                      "sfo", "tyrol-e"]

    # Training-Split -> give whole image
    ids = range(6, 37)
    total = len(train_locations) * len(ids)
    train_file = pt.join(outdir, 'train.msgpack')
    try:
        with FileWriter(train_file, total=total, overwrite=args.no_confirm) as writer:
            for fn, img, labels in images_and_labels_iter(
                    train_img_dir, train_gt_dir, train_locations, ids
            ):
                write(writer, img, labels, fn)
    except FileExistsError:
        pass

    # Put first 5 images into the validation set, as in the paper
    # https://hal.inria.fr/hal-01468452/document
    # Validation-Split -> give splitted images
    test_file = pt.join(outdir, 'val.msgpack')
    ids = range(1, 6)
    crop_h, crop_w = crop_size
    crops = (5000 // crop_h) * (5000 // crop_w)
    total = len(train_locations) * len(ids) * crops
    try:
        with FileWriter(test_file, total=total, overwrite=args.no_confirm) as writer:
            for fn, img, labels in images_and_labels_iter(
                    train_img_dir, train_gt_dir, train_locations, ids
            ):
                labels = np.expand_dims(labels, axis=0)
                gen = enumerate(zip(
                    split_array(img, *crop_size),
                    split_array(labels, *crop_size)
                ))
                for idx, (sub_img, sub_label) in gen:
                    _, w, h = sub_img.shape
                    if w < crop_w or h < crop_h:  # reject small patches
                        continue
                    write(writer, sub_img, sub_label[0], "%s_%s" % (fn, idx))
    except FileExistsError:
        pass

    # Test-Split -> give splitted images without labels
    test_file = pt.join(outdir, 'test.msgpack')
    ids = range(1, 37)
    crops = (5000 // crop_h) * (5000 // crop_w)
    total = len(test_locations) * len(ids) * crops
    try:
        with FileWriter(test_file, total=total, overwrite=args.no_confirm) as writer:
            for fn, img, labels in images_and_labels_iter(
                    test_img_dir, None, test_locations, ids
            ):
                gen = enumerate(split_array(img, *crop_size))
                for idx, sub_img in gen:
                    _, w, h = sub_img.shape
                    if w < crop_w or h < crop_h:  # reject small patches
                        continue
                    write(writer, sub_img, None, "%s_%s" % (fn, idx))
    except FileExistsError:
        pass


def main():
    from ..tools.argparse import make_parser

    parser = make_parser(__doc__, skip_verification=False, shuffle=False)
    args = parser.parse_args()
    outdir = args.outdir or args.indir
    write_sets(args.indir, outdir, args)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
