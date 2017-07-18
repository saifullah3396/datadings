"""Create Vaihingen data set files.

The data set is described here:
    xxx

This tool will look for the following files in the input directory
and download them if necessary:
    - Vaihingen Dataset

"""
from __future__ import print_function, division

import numpy as np
import os.path as pt

from datadings.writer import FileWriter
from datadings.tools import FrequencyPrinter
from datadings.sets import MaskedSegmentationData
from datadings.sets.Vaihingen import CLASSES
from datadings.sets.Vaihingen import CROP_SIZE
from datadings.sets.Vaihingen import COLOR_TO_CLASS_MAP
from datadings.tools import pack_array
from datadings.tools import split_array


def write(writer, img, labels, mask, filename=""):
    item = MaskedSegmentationData(
        pack_array(img),
        pack_array(labels),
        pack_array(mask),
        filename,
        CLASSES,
        [1] * len(CLASSES),
    )
    writer.write(item)


def map_color_values_to_class_indices(img):
    arr_2d = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)
    for c, i in COLOR_TO_CLASS_MAP.items():
        m = np.all(img == np.array(c).reshape(1, 1, 3), axis=2)
        arr_2d[m] = i
    return arr_2d


def tiff_to_nd_array(file_path, type=np.int8):
    from osgeo import gdal
    dataset = gdal.Open(file_path, gdal.GA_ReadOnly)
    return np.array([dataset.GetRasterBand(idx+1).ReadAsArray()
                        for idx in range(dataset.RasterCount)]).astype(type)



def write_sets(indir, outdir, crop_size=(CROP_SIZE, CROP_SIZE)):
    # FIXME: add download_if_not_found, not easily accessable?
    dataset_dir = pt.join(indir, 'ISPRS_semantic_labeling_Vaihingen')
    img_dir = pt.join(dataset_dir, 'top')
    dsm_dir = pt.join(dataset_dir, 'dsm')
    label_dir = pt.join(dataset_dir, 'gts_for_participants')

    printer = FrequencyPrinter()

    # Training-Split -> give whole image
    train_file = pt.join(outdir, 'Vaihingen_train.msgpack')
    with FileWriter(train_file) as writer:
        for id in [1, 3, 5, 7, 13, 17, 21, 23, 26, 32, 37]:
            img_path = pt.join(img_dir, "top_mosaic_09cm_area%s.tif" %(id))
            label_path = pt.join(label_dir, "top_mosaic_09cm_area%s.tif" % (id))
            dsm_path = pt.join(dsm_dir, "dsm_09cm_matching_area%s.tif" % (id))

            img = tiff_to_nd_array(img_path)
            train_img = img.astype(np.uint8)

            labels = tiff_to_nd_array(label_path, type=np.uint8)
            labels = labels.transpose(1, 2, 0)
            train_labels = map_color_values_to_class_indices(labels)\
                .astype(np.int64)

            dsm = tiff_to_nd_array(dsm_path, type=np.int32)
            train_dsm = dsm[0]

            write(writer, train_img, train_labels, train_dsm, "train_%s"%(id))
            printer.update()


    # Validation-Split -> give splitted images
    val_file = pt.join(outdir, 'Vaihingen_val.msgpack')
    with FileWriter(val_file) as writer:
        for id in [11, 15, 28, 30, 34]:
            img_path = pt.join(img_dir, "top_mosaic_09cm_area%s.tif" %(id))
            label_path = pt.join(label_dir, "top_mosaic_09cm_area%s.tif" % (id))
            dsm_path = pt.join(dsm_dir, "dsm_09cm_matching_area%s.tif" % (id))

            img = tiff_to_nd_array(img_path)
            train_img = img #transpose after splitting!

            labels = tiff_to_nd_array(label_path, type=np.uint8)
            labels = labels.transpose(1, 2, 0)
            train_labels = map_color_values_to_class_indices(labels)

            dsm = tiff_to_nd_array(dsm_path, type=np.int32)
            train_dsm = dsm[0]

            train_labels = np.expand_dims(train_labels, axis=0)
            train_dsm = np.expand_dims(train_dsm, axis=0)

            for idx, (sub_img, sub_label, sub_dsm) in \
                    enumerate(zip(  split_array(train_img, *crop_size),
                                    split_array(train_labels, *crop_size),
                                    split_array(train_dsm, *crop_size))):
                sub_img = np.array(sub_img).astype(np.uint8)
                sub_label = np.array(sub_label[0]).astype(np.int64)
                sub_dsm = np.array(sub_dsm[0])
                write(writer, sub_img, sub_label, sub_dsm, "val_%s_%s"%(id, idx))
                printer.update()



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



