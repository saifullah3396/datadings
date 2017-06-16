from __future__ import division
import cv2
import yaml
import scipy.misc
from scipy.ndimage.filters import gaussian_filter
from scipy.ndimage.morphology import binary_erosion, binary_dilation
from scipy.spatial import ConvexHull
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from PIL import Image, ImageDraw

from ANP460_Preprocessing import *
from os.path import isfile, join
from os import listdir
'''
Create fixation (saliency) maps from 'wrangled_data.zip'. (This needs to be extended 
to handle .msgpack files.)

For every image a boolean and a saliency map is created. Dependent from the image type 
('test' or 'control') and the participants answer ('yes' or 'no') the fixation points 
of the participants are grouped together. 
Participants that saw a test image and answered with 'yes' were considered and 
grouped together. From these fixation points a saliency map was created. For 
control images the opposite happened. Participants that answered with 'no' were 
recognized.. 

'''

indir = '/Users/magnus/master/DFKI/data/fixation_data'
outdir = '/Users/magnus/master/DFKI/data/saliency_maps'
outdir_bool = '/Users/magnus/master/DFKI/data/boolean_map'
outdir_convex = '/Users/magnus/master/DFKI/data/convex_map'
outdir_gaussian_cluster = '/Users/magnus/master/DFKI/data/gaussian_cluster'

with open('/Users/magnus/Downloads/ANP400/image_anp_list.json') as json_data:
    anp_list = yaml.safe_load(json_data)
    anp_list['455.jpg'][0] = 'rough_road'

if not os.path.exists(outdir):
    os.makedirs(outdir)
if not os.path.exists(outdir_bool):
    os.makedirs(outdir_bool)
if not os.path.exists(outdir_convex):
    os.makedirs(outdir_convex)
if not os.path.exists(outdir_gaussian_cluster):
    os.makedirs(outdir_gaussian_cluster)

'''
Take clustered points. Do a gaussian convolution. Then threshold.
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

def test_or_control(image_name):
    '''
    Todo: include difference control / opposite. 
    '''
    if anp_list[image_name][1] == 'test':
        yon = 'test'
    else:
        yon = 'control'
    return yon

def draw_saliency_map(image_name, fixation_points, percentage_salient):
    grid = salicon_gaze(fixation_points, image_name)
    saliency_map = fixation_map(grid)
    path = os.path.join(outdir, image_name)
    scipy.misc.imsave(path, saliency_map)
    # Create boolean map saliency map
    threshold = np.percentile(saliency_map, percentage_salient)
    boolean_map = (saliency_map > threshold)
    boolean_map = erosion_dilation(boolean_map).astype(int)
    # pos = unique_anp.index(anp_list[file_name][0]) + 1
    path = os.path.join(outdir_bool, image_name[0:3] + '.png')
    scipy.misc.imsave(path, boolean_map)
    # cv2.imwrite(path, boolean_map)

def create_maps(first_n_fixations = 6, percentage_salient = 80):
    for image_name in image_names:
        fixation_points = []
        for participant in participants:
            fixpath = os.path.join(indir, participant[0:3], image_name[0:3] + '.npy')
            answerpath = os.path.join(indir, participant[0:3], 'answers.npy')

            if test_or_control(image_name) == 'test':
                if np.load(answerpath)[int(image_name[0:3])] == 'Y':
                    fixation_points.append(np.load(fixpath)[0:first_n_fixations])
            else:
                if np.load(answerpath)[int(image_name[0:3])] == 'N':
                    fixation_points.append(np.load(fixpath)[0:first_n_fixations])
        fixation_points = np.concatenate(fixation_points, axis=0)
        draw_saliency_map(image_name, fixation_points, percentage_salient)

def main():
    create_maps()

if __name__ == '__main__':
    main()

