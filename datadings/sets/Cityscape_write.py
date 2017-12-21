"""Create CityScape data set files.

This tool will look for the following files in the input directory
and download them if necessary:
    - CityScape.zip from: https://www.cityscapes-dataset.com/

"""
from __future__ import print_function, division

import os.path as pt
import numpy as np

from ..writer import FileWriter
from ..tools import FrequencyPrinter
from . import SegmentationDisparityData
import os
import cv2
import io


def write_image(writer, indata, dsm, outdata, filename):
    item = SegmentationDisparityData(
        indata,
        dsm,
        outdata,
        filename,
        None,
        None,
    )
    writer.write(item)


def write_sets(indir, outdir, shuffle=True):
    for split in ('test', 'val', 'train'):
        outpath = pt.join(outdir, 'cityscape_%s.msgpack' % split)
        with FileWriter(outpath) as writer:
            gt_city_dirs = pt.join(indir, 'gtFine', split)
            img_city_dirs = pt.join(indir, 'leftImg8bit', split)
            dsm_city_dirs = pt.join(indir, 'disparity', split)

            idx = 0
            printer = FrequencyPrinter()
            for city_name in os.listdir(gt_city_dirs):
                gt_city_folder = os.path.join(gt_city_dirs, city_name)
                img_city_folder = os.path.join(img_city_dirs, city_name)
                dsm_city_folder = os.path.join(dsm_city_dirs, city_name)

                for img_name in os.listdir(gt_city_folder):
                    if img_name.endswith("_labelIds.png"):
                        gt_path = os.path.join(gt_city_folder, img_name)
                        with io.FileIO(gt_path, "rb") as f:
                            gt_data = f.read()

                        image_id = img_name.split("_")[1]
                        frame_id = img_name.split("_")[2]

                        img_name = "%s_%s_%s_leftImg8bit.png" \
                                   %(city_name, image_id, frame_id)
                        img_path = os.path.join(img_city_folder, img_name)
                        with io.FileIO(img_path, "rb") as f:
                            img_data = f.read()

                        dsm_name = "%s_%s_%s_disparity.png" \
                                   % (city_name, image_id, frame_id)
                        dsm_path = os.path.join(dsm_city_folder, dsm_name)
                        with io.FileIO(dsm_path, "rb") as f:
                            dsm_data = f.read()

                        write_image(writer, img_data, dsm_data, gt_data, gt_path)
                        printer.update()
                        printer.print_total_updates()
                    idx += 1
                    #if idx == 10:
                    #    break
                #break


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
