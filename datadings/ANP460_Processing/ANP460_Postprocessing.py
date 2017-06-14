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
Create fixation (saliency) maps, boolean maps from fixations maps and use DBSCAN 
clustering to create boolean maps.
For every image one "ground truth" was created.
For each image the participant was asked if the ANP is visible? 
Dependent if the image was a test or control/opposite image the  
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

def draw_convex_hull(image_name, fixation_points):
    dim = calculate_dimensions(image_name)
    fix_normalized = StandardScaler().fit_transform(fixation_points)
    db = DBSCAN(eps=0.27, min_samples=5).fit(fix_normalized)
    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True
    labels = db.labels_
    unique_labels = set(labels)
    convex_map = np.array(Image.new('L', (dim[0], dim[1]), 0))
    for k in unique_labels:
        if k == -1:
            continue
        class_member_mask = (labels == k)
        # would you like to include non core samples?
        xy = fixation_points[class_member_mask & core_samples_mask]
        if len(np.unique(xy[:, 0]))<3:
            continue
        hull = ConvexHull(xy)
        img = Image.new('L', (dim[0], dim[1]), 0)
        pts = [(x[0], x[1]) for x in xy[hull.vertices,:]]
        ImageDraw.Draw(img).polygon(pts, outline=1, fill=20)
        convex_map += np.array(img)
    convex_map[convex_map >= 1] = 255
    convex_map = np.flipud(convex_map)
    path = os.path.join(outdir_convex, image_name[0:3] + '.png')
    cv2.imwrite(path, convex_map)

def draw_gaussian_boolean_map_from_cluster(image_name, fixation_points):
    dim = calculate_dimensions(image_name)
    fix_normalized = StandardScaler().fit_transform(fixation_points)
    db = DBSCAN(eps=0.27, min_samples=5).fit(fix_normalized)
    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True
    labels = db.labels_
    class_member_mask = (labels != -1)
    # would you like to include non core samples?
    cluster_points = fixation_points[class_member_mask & core_samples_mask]
    if len(np.unique(cluster_points[:, 0])) < 3:
        pass
    grid = salicon_gaze(cluster_points, image_name)
    saliency_map = fixation_map(grid)
    path = os.path.join(outdir_gaussian_cluster, image_name[0:3] + '.png')
    scipy.misc.imsave(path, saliency_map)

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
        #draw_convex_hull(image_name, fixation_points)
        #draw_gaussian_boolean_map_from_cluster(image_name, fixation_points)

def get_image(image_name):
    path = os.path.join(im_root, image_name)
    img = sci.imread(path)
    dim = calculate_dimensions(image_name)
    dim = (int(dim[0]), int(dim[1]), 3)
    img = sci.imresize(img, dim)
    return img

def view_convex_bool_map():
    boolean_path =[join(outdir_bool, f) for f in listdir(outdir_bool)
                   if f.endswith('.png')]
    convex_path = [join(outdir_convex, f) for f in listdir(outdir_convex)
                   if f.endswith('.png')]
    for i, image_name in enumerate(image_names):
        dim = calculate_dimensions(image_name)
        img = get_image(image_name)
        f, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
        ax1.imshow(img, zorder=0, extent=[0, dim[0], 0, dim[1]])
        ax2.imshow(img, zorder=0, extent=[0, dim[0], 0, dim[1]])
        boolean_map = np.asarray(Image.open(boolean_path[i]))
        convex_map = np.asarray(Image.open(convex_path[i]))
        ax1.matshow(boolean_map, zorder=1, alpha=0.8, cmap=trans_black,
                                                extent=[0, dim[0], 0, dim[1]])
        ax2.matshow(convex_map, zorder=1, alpha=0.8, cmap=trans_black,
                                                      extent=[0, dim[0], 0, dim[1]])
        plt.show()
    pass

def view_gaussians():
    boolean_path =[join(outdir_gaussian_cluster, f) for f in listdir(outdir_gaussian_cluster)
                   if f.endswith('.png')]
    convex_path = [join(outdir, f) for f in listdir(outdir)
                   if f.endswith('.jpg')]
    for i, image_name in enumerate(image_names):
        dim = calculate_dimensions(image_name)
        img = get_image(image_name)
        f, (ax1, ax2) = plt.subplots(1, 2, figsize=(15,6), sharey=True)
        ax1.imshow(img, zorder=0, extent=[0, dim[0], 0, dim[1]])
        ax2.imshow(img, zorder=0, extent=[0, dim[0], 0, dim[1]])
        boolean_map = np.asarray(Image.open(boolean_path[i]))
        convex_map = np.asarray(Image.open(convex_path[i]))
        ax1.matshow(boolean_map, zorder=1, alpha=1, cmap=trans_black,
                                                extent=[0, dim[0], 0, dim[1]])
        ax2.matshow(convex_map, zorder=1, alpha=1, cmap=trans_black,
                                                      extent=[0, dim[0], 0, dim[1]])
        plt.show()
    pass

def main():
    #create_maps()
    view_convex_bool_map()
    #view_gaussians()

if __name__ == '__main__':
    main()

