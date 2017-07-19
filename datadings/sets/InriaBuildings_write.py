"""Create InriaBuilding data set files.

The data set is described here:
    https://project.inria.fr/aerialimagelabeling/contest/

This tool will look for the following files in the input directory
and download them if necessary:
    - https://project.inria.fr/aerialimagelabeling/contest/

"""
from __future__ import print_function, division

import numpy as np
import os.path as pt
import os

from datadings.writer import FileWriter
from datadings.tools import FrequencyPrinter
from datadings.sets import SegmentationData
from datadings.sets.InriaBuildings import CLASSES
from datadings.sets.InriaBuildings import CROP_SIZE
from datadings.tools import pack_array
from datadings.tools import split_array
from datadings.tools import tiff_to_nd_array


def write(writer, img, labels, filename=""):
    item = SegmentationData(
        pack_array(img),
        pack_array(labels),
        filename,
        CLASSES,
        [1] * len(CLASSES),
    )
    writer.write(item)


def images_and_labels_iter(img_dir, label_dir, locations, ids):
    for location in locations:
        for id in ids:
            filename = "%s%s.tif" % (location, id)
            img_path = pt.join(img_dir, filename)

            img = tiff_to_nd_array(img_path)
            train_img = img.astype(np.uint8)

            labels = None
            if label_dir is not None:
                label_path = pt.join(label_dir, filename)

                labels = tiff_to_nd_array(label_path, type=np.int64)
                labels = labels[0]
                labels[labels == 255] = 1  # set correct class label

            yield filename, train_img, labels


def write_sets(indir, outdir, crop_size=(CROP_SIZE, CROP_SIZE)):
    dataset_dir = pt.join(indir, 'AerialImageDataset')
    train_dir = pt.join(dataset_dir, 'train')
    test_dir = pt.join(dataset_dir, 'test')
    train_img_dir = pt.join(train_dir, 'images')
    test_img_dir = pt.join(test_dir, 'images')
    train_gt_dir = pt.join(train_dir, 'gt')

    train_locations = ["vienna", "kitsap", "tyrol-w", "chicago", "austin"]
    test_locations = ["bellingham", "bloomington", "innsbruck",
                      "sfo", "tyrol-e"]
    printer = FrequencyPrinter()


    # Training-Split -> give whole image
    train_file = pt.join(outdir, 'InriaBuildings_train.msgpack')
    with FileWriter(train_file) as writer:
        for fn, train_img, labels in images_and_labels_iter(train_img_dir,
                                                            train_gt_dir,
                                                            train_locations,
                                                            range(6, 37)):
            write(writer, train_img, labels, fn)
            printer.update()
    printer.print_total_updates()


    # Put first 5 images into the validation set, as in the paper
    # https://hal.inria.fr/hal-01468452/document
    # Validation-Split -> give splitted images
    val_file = pt.join(outdir, 'InriaBuildings_val.msgpack')
    with FileWriter(val_file) as writer:
        for fn, train_img, labels in images_and_labels_iter(train_img_dir,
                                                            train_gt_dir,
                                                            train_locations,
                                                            range(6)):
            train_labels = np.expand_dims(labels, axis=0)
            for idx, (sub_img, sub_label) in \
                    enumerate(zip(  split_array(train_img, *crop_size),
                                    split_array(train_labels, *crop_size))):

                sub_img = np.array(sub_img).astype(np.uint8)
                sub_label = np.array(sub_label[0]).astype(np.int64)
                write(writer, sub_img, sub_label, "%s_%s"%(fn, idx))
                printer.update()
    printer.print_total_updates()


    # Test-Split -> give splitted images without labels
    val_file = pt.join(outdir, 'InriaBuildings_test.msgpack')
    with FileWriter(val_file) as writer:
        for fn, train_img, labels in images_and_labels_iter(test_img_dir,
                                                            None,
                                                            test_locations,
                                                            range(37)):
            for idx, sub_img in enumerate(split_array(train_img, *crop_size)):
                sub_img = np.array(sub_img).astype(np.uint8)
                sub_label = np.array([])
                write(writer, sub_img, sub_label, "%s_%s"%(fn, idx))
                printer.update()
    printer.print_total_updates()



def main():
    import argparse
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'indir',
        metavar='INPATH',
        default='.',
        help='directory that contains In InriaBuilding files'
    )
    parser.add_argument(
        '-o', '--outdir',
        metavar='OUTPATH',
        help='output directory; defaults to indir'
    )
    args = parser.parse_args()
    outdir = args.outdir or args.indir
    print(args.indir)
    write_sets(args.indir, outdir)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()



