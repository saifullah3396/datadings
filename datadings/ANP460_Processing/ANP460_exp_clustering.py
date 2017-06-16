from ANP460_Processing import *

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sklearn.datasets as data
import hdbscan


sns.set_context('poster')
sns.set_style('white')
sns.set_color_codes()
plot_kwds = {'alpha' : 0.5, 's' : 80, 'linewidths':0}


# Experimental hdbscan clustering method.

def draw_hdbscan(image_name, fixation_points):
    dim = calculate_dimensions(image_name)
    img = get_image(image_name)
    #fix_normalized = StandardScaler().fit_transform(fixation_points)
    fix_normalized = fixation_points
    clusterer = hdbscan.HDBSCAN(min_cluster_size=5, gen_min_span_tree=True)
    clusterer.fit(fix_normalized)
    hdbscan.HDBSCAN(algorithm='best', alpha=1.0, approx_min_span_tree=True,
                    gen_min_span_tree=True, leaf_size=40,  # memory=Memory(cachedir=None),
                    metric='euclidean', min_cluster_size=5, min_samples=None, p=None)

    palette = sns.color_palette("hls", 12)
    cluster_colors = [sns.desaturate(palette[col], sat)
                      if col >= 0 else (0.5, 0.5, 0.5) for col, sat in
                      zip(clusterer.labels_, clusterer.probabilities_)]

    plt.imshow(img, zorder=0, extent=[0, dim[0], 0, dim[1]])
    plt.scatter(fix_normalized.T[0], fix_normalized.T[1], c=cluster_colors, **plot_kwds)
    #plt.matshow(img, zorder=1, alpha=0.8, cmap=trans_black,
    #            extent=[0, dim[0], 0, dim[1]])
    plt.show()

def show_maps(first_n_fixations = 6):
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
        draw_hdbscan(image_name, fixation_points)

# Convex hulls of clusters, gaussian maps from clusters . Use to create "denser" saliency
# maps.

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

def draw_gaussian_from_cluster(image_name, fixation_points):
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

# For comparing normal gaussian maps and gaussian maps from clusters, and convex hull
# vs. 20% most salient boolean maps.

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
        draw_convex_hull(image_name, fixation_points, percentage_salient)
        draw_gaussian_from_cluster(image_name, fixation_points, percentage_salient)



if __name__ == '__main__':
    create_maps()
