"""Create Vaihingen data set files.

This tool will look for the ISPRS_semantic_labeling_Vaihingen directory in the
input directory.

See also:
    http://www2.isprs.org/commissions/comm3/wg4/2d-sem-label-vaihingen.html

Note:
    Requests to download the dataset can be made by filling out the form on
    the website.

Warning:
    Images, labels, and masks are numpy arrays, not images!

"""
import numpy as np
import os.path as pt

from ..writer import FileWriter
from . import MaskedImageSegmentationData
from .Vaihingen import CROP_SIZE
from .Vaihingen import COLOR_TO_CLASS_MAP
from ..tools import split_array
from ..tools import tiff_to_nd_array
from ..tools import document_keys


__doc__ += document_keys(MaskedImageSegmentationData)


def write(writer, img, labels, mask, filename):
    writer.write(MaskedImageSegmentationData(
        filename,
        img,
        labels,
        mask,
    ))


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
        fn = "top_mosaic_09cm_area%s.tif" % (id,)
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


def write_sets(indir, outdir, args, crop_size=(CROP_SIZE, CROP_SIZE)):
    # Training-Split -> give whole image
    train_file = pt.join(outdir, 'Vaihingen_train.msgpack')
    image_ids = [1, 3, 5, 7, 13, 17, 21, 23, 26, 32, 37]
    try:
        with FileWriter(train_file, overwrite=args.no_confirm) as writer:
            for fn, train_img, train_labels, train_dsm in \
                    images_label_dsm_iter(indir, image_ids):
                write(writer, train_img, train_labels, train_dsm, fn)
    except FileExistsError:
        pass

    # Validation-Split -> give splitted images
    val_file = pt.join(outdir, 'Vaihingen_val.msgpack')
    try:
        with FileWriter(val_file) as writer:
            for fn, train_img, train_labels, train_dsm in \
                    images_label_dsm_iter(indir, [11, 15, 28, 30, 34]):
                train_labels = np.expand_dims(train_labels, axis=0)
                train_dsm = np.expand_dims(train_dsm, axis=0)
                gen = enumerate(zip(
                    split_array(train_img, *crop_size),
                    split_array(train_labels, *crop_size),
                    split_array(train_dsm, *crop_size),
                ))
                for idx, (sub_img, sub_label, sub_dsm) in gen:
                    sub_img = np.array(sub_img).astype(np.uint8)
                    sub_label = np.array(sub_label[0]).astype(np.int64)
                    sub_dsm = np.array(sub_dsm[0])
                    write(writer, sub_img, sub_label, sub_dsm, "%s_%s" % (fn, idx))
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
