"""Create CityScape data set files.

This tool will look for the following files in the input directory
and download them if necessary:
    - CityScape.zip from: https://www.cityscapes-dataset.com/

"""
from __future__ import print_function, division

import os.path as pt
import numpy as np

from datadings.writer import FileWriter
from datadings.tools import FrequencyPrinter
from datadings.sets import SegmentationDisparityData
from datadings.sets.Cityscape import COUNTS
import os
import cv2


def write_image(writer, indata, dsm, outdata, filename):
    item = SegmentationDisparityData(
        indata,
        dsm,
        outdata,
        filename,
        COUNTS,
        COUNTS,
    )
    writer.write(item)


def write_sets(indir, outdir, shuffle=True):
    for split in ('test', 'val', 'train'):
        outpath = pt.join(outdir, 'cityscape_%s.msgpack' % split)
        with FileWriter(outpath) as writer:
            gt_city_dirs = pt.join(indir, 'gtFine', split)
            img_city_dirs = pt.join(indir, 'leftImg8bit', split)
            dsm_city_dirs = pt.join(indir, 'dsm', split)

            printer = FrequencyPrinter()
            for city_name in os.listdir(gt_city_dirs):
                gt_city_folder = os.path.join(gt_city_dirs, city_name)
                img_city_folder = os.path.join(img_city_dirs, city_name)
                dsm_city_folder = os.path.join(dsm_city_dirs, city_name)

                for img_name in os.listdir(gt_city_folder):
                    if img_name.endswith("_labelIds.png"):
                        gt_path = os.path.join(gt_city_folder, img_name)
                        image_id = img_name.split("_")[1]
                        frame_id = img_name.split("_")[2]

                        img_name = "%s_%s_%s_leftImg8bit.png" \
                                   %(city_name, image_id, frame_id)
                        img = os.path.join(img_city_folder, img_name)
                        #dsm = os.path.join(dsm_city_folder,
                        #                   img.replace("gtFine", "todofixme"))

                        gt = cv2.imread(gt_path)
                        gt = cv2.resize(gt, (256, 512), interpolation=0) #FIXME

                        img = cv2.imread(img)
                        img = cv2.resize(img, (256, 512), interpolation=1) #FIXME

                        write_image(writer, img, img, gt, gt_path)
                        printer.update()
                        printer.print_total_updates()



def median_frequency_weights(counts):
    total = sum(counts)
    freq = [n/total for n in counts]
    # cannot serialize numpy scalars,
    # weights must be Python numbers!
    median_freq = float(np.median(freq))
    return [median_freq/f for f in freq]


def class_counts(gen):
    counts = np.float64([])
    printer = FrequencyPrinter()
    for segmap in gen:
        printer.update()
        cs = np.bincount(segmap.flatten()).astype(np.float64) / segmap.size
        if len(cs) <= len(counts):
            counts[:len(cs)] += cs
        else:
            cs[:len(counts)] += counts
            counts = cs
    counts = {c: counts[c] for c in np.nonzero(counts)[0]}
    return counts


def print_values(prefix, values):
    print('%s = [' % prefix)
    for v in values:
        print('    {},'.format(v))
    print(']')


def gt_imgs(indir):
    gt_city_dirs = pt.join(indir, 'gtFine', "train")
    for city_name in os.listdir(gt_city_dirs):
        gt_city_folder = os.path.join(gt_city_dirs, city_name)
        for img in os.listdir(gt_city_folder):
            if img.endswith("_labelIds.png"):
                gt_path = os.path.join(gt_city_folder, img)
                yield np.array(cv2.imread(gt_path)).astype(np.uint8)


def sorted_values(d):
    return [d[k] for k in sorted(d)]


def calculate_weights(indir):
    gen = gt_imgs(indir)
    counts = class_counts(gen)
    weights = median_frequency_weights(counts)
    print_values('INDEXES', sorted(counts))
    print_values('COUNTS', sorted_values(counts))
    print_values('WEIGHTS', sorted_values(weights))


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
        help='directory that contains MIT1003 archives'
    )
    parser.add_argument(
        '-o', '--outdir',
        metavar='OUTPATH',
        help='output directory; defaults to indir'
    )
    parser.add_argument(
        '--calculate-weights',
        action='store_true',
        help='calculate median-frequency class weights'
    )
    args = parser.parse_args()
    outdir = args.outdir or args.indir
    if args.calculate_weights:
        calculate_weights(args.indir)
    else:
        write_sets(args.indir, outdir)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print()
