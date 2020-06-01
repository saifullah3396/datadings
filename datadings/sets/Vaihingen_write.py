"""Create Vaihingen data set files.

The data set is described here:
    xxx

This tool will look for the following files in the input directory
and download them if necessary:
    - Vaihingen Dataset

"""
import numpy as np
import os.path as pt

from ..writer import FileWriter
from . import MaskedImageSegmentationData
from .Vaihingen import CLASSES
from .Vaihingen import CROP_SIZE
from .Vaihingen import COLOR_TO_CLASS_MAP
from ..tools import split_array
from ..tools import tiff_to_nd_array


def write(writer, img, labels, mask, filename=""):
    item = MaskedImageSegmentationData(
        img,
        labels,
        mask,
        filename,
        CLASSES,
        [1] * len(CLASSES),
    )
    writer.write(item)


def map_color_values_to_class_indices(img):
    arr_2d = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)
    for c, i in COLOR_TO_CLASS_MAP.items():
        m = np.all(img == np.array(c).reshape((1, 1, 3)), axis=2)
        arr_2d[m] = i
    return arr_2d


def images_label_dsm_iter(indir, image_ids):
    dataset_dir = pt.join(indir, 'ISPRS_semantic_labeling_Vaihingen')
    img_dir = pt.join(dataset_dir, 'top')
    dsm_dir = pt.join(dataset_dir, 'dsm')
    label_dir = pt.join(dataset_dir, 'gts_for_participants')

    for id in image_ids:
        fn = "top_mosaic_09cm_area%s.tif" % (id)
        img_path = pt.join(img_dir, fn)
        label_path = pt.join(label_dir, fn)
        dsm_path = pt.join(dsm_dir, fn.replace("top_", "dsm_"))

        img = tiff_to_nd_array(img_path)
        train_img = img.astype(np.uint8)

        labels = tiff_to_nd_array(label_path, type=np.uint8)
        labels = labels.transpose(1, 2, 0)
        train_labels = map_color_values_to_class_indices(labels) \
            .astype(np.int64)

        dsm = tiff_to_nd_array(dsm_path, type=np.int32)
        train_dsm = dsm[0]
        yield fn, train_img, train_labels, train_dsm


def write_sets(indir, outdir, crop_size=(CROP_SIZE, CROP_SIZE)):
    # Training-Split -> give whole image
    train_file = pt.join(outdir, 'Vaihingen_train.msgpack')
    with FileWriter(train_file) as writer:
        image_ids = [1, 3, 5, 7, 13, 17, 21, 23, 26, 32, 37]
        for fn, train_img, train_labels, train_dsm in \
                                    images_label_dsm_iter(indir, image_ids):

            write(writer, train_img, train_labels, train_dsm, fn)

    # Validation-Split -> give splitted images
    val_file = pt.join(outdir, 'Vaihingen_val.msgpack')
    with FileWriter(val_file) as writer:
        for fn, train_img, train_labels, train_dsm in \
                            images_label_dsm_iter(indir, [11, 15, 28, 30, 34]):

            train_labels = np.expand_dims(train_labels, axis=0)
            train_dsm = np.expand_dims(train_dsm, axis=0)

            for idx, (sub_img, sub_label, sub_dsm) in \
                    enumerate(zip(  split_array(train_img, *crop_size),
                                    split_array(train_labels, *crop_size),
                                    split_array(train_dsm, *crop_size))):
                sub_img = np.array(sub_img).astype(np.uint8)
                sub_label = np.array(sub_label[0]).astype(np.int64)
                sub_dsm = np.array(sub_dsm[0])
                write(writer, sub_img, sub_label, sub_dsm, "%s_%s"%(fn, idx))


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
        help='directory that contains Vaihingen Dataset files'
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
