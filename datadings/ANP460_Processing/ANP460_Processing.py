from __future__ import division
import scipy.misc
from scipy.ndimage.filters import gaussian_filter
from scipy.ndimage.morphology import binary_erosion, binary_dilation
import os
import numpy as np
from datadings.sets.ANP460 import ANP460Reader
from ANP460_Preprocessing import *
import os.path as pt

'''
Create fixation (saliency) maps from 'wrangled_data.zip'. (This needs to be extended 
to handle .msgpack files.)

For every image a boolean and a saliency map is created. Dependent from the image type 
('test' or 'control') and the participants answer ('yes' or 'no') the fixation points 
of the participants are grouped together. 
Participants that saw a test image and answered with 'yes' were considered and 
grouped together. From these fixation points a saliency map was created. For 
control images the opposite is done. Participants that answered with 'no' were 
recognized.. 
'''


def salicon_gaze(fixation_points, image_name):
    dim = calculate_dimensions(image_name)
    grid = np.zeros((960, 1440))
    cx = np.round(fixation_points[:,0]).astype(int)
    cy = np.round(fixation_points[:, 1]).astype(int)
    grid[cy, cx] = 1
    grid = np.flipud(grid)
    return grid[(960-dim[1]):960, 0:dim[0]]


def fixation_map(grid, sigma=38):
    sal_map = gaussian_filter(grid, sigma=sigma, truncate=4, mode='constant')
    sal_map -= np.min(sal_map)
    sal_map /= np.max(sal_map)
    return sal_map


def erosion_dilation(convex_map):
    convex_map = binary_erosion(convex_map, structure=np.ones((20,20)))
    convex_map = binary_dilation(convex_map, structure=np.ones((40,40)))
    convex_map = binary_erosion(convex_map, structure=np.ones((20, 20)))
    return convex_map


def saliency_map(fixation_points, image_name):
    salicon_gaze(fixation_points, image_name)


def draw_saliency_map(outdir_bool, outdir_sal, image_name, fixation_points,
                      percentage_salient):
    grid = salicon_gaze(fixation_points, image_name)
    saliency_map = fixation_map(grid)
    path = pt.join(outdir_sal, image_name)
    scipy.misc.imsave(path, saliency_map)
    # Create boolean map saliency map
    threshold = np.percentile(saliency_map, percentage_salient)
    boolean_map = (saliency_map > threshold)
    boolean_map = erosion_dilation(boolean_map).astype(int)
    # pos = unique_anp.index(anp_list[file_name][0]) + 1
    path = pt.join(outdir_bool, image_name[0:3] + '.png')
    scipy.misc.imsave(path, boolean_map)
    # cv2.imwrite(path, boolean_map)


def correct(type):
    if type == 'test':
        return 'Y'
    else:
        return 'N'


def build_dirs(outdir):
    outdir_bool = pt.join(outdir, 'boolean')
    outdir_sal = pt.join(outdir, 'saliency')
    if not pt.exists(outdir_sal):
        os.makedirs(outdir_sal)
    if not pt.exists(outdir_bool):
        os.makedirs(outdir_bool)
    return outdir_bool, outdir_sal


def build_maps(indir, outdir, percentage_salient=80):
    msgpath = pt.join(indir, 'ANP460.msgpack')
    outdir_bool, outdir_sal = build_dirs(outdir)
    i=1
    with ANP460Reader(msgpath) as reader:
        for sample in reader:
            print i
            fixation_points = []
            image_name = sample.filename.split(os.sep)[1]
            for points in sample.groundtruth:
                if points.answer == correct(sample.type):
                    raw_data = np.array(points.locations[:-1])
                    fixations = get_fixation_points(raw_data, image_name)
                    fixation_points.append(fixations)
            if len(fixation_points) > 0:
                fixation_points = np.concatenate(fixation_points, axis=0)
                draw_saliency_map(outdir_sal, outdir_bool, image_name, fixation_points,
                                  percentage_salient)
            else:
                print 'keine fixierungpunkte vorhanden'
            i += 1
    pass


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
        help='directory that contains ANP460 archives'
    )
    parser.add_argument(
        '-o', '--outdir',
        metavar='OUTPATH',
        help='output directory; defaults to indir'
    )
    args = parser.parse_args()
    outdir = args.outdir or args.indir
    build_maps(args.indir, outdir)

if __name__ == '__main__':
    main()

