from ANP460_Postprocessing import *

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sklearn.datasets as data
import hdbscan


sns.set_context('poster')
sns.set_style('white')
sns.set_color_codes()
plot_kwds = {'alpha' : 0.5, 's' : 80, 'linewidths':0}


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

if __name__ == '__main__':
    show_maps()


'''
moons, _ = data.make_moons(n_samples=50, noise=0.05)
blobs, _ = data.make_blobs(n_samples=50, centers=[(-0.75,2.25), (1.0, 2.0)], cluster_std=0.25)
test_data = np.vstack([moons, blobs])
plt.scatter(test_data.T[0], test_data.T[1], color='b', **plot_kwds)

clusterer = hdbscan.HDBSCAN(min_cluster_size=5, gen_min_span_tree=True)
clusterer.fit(test_data)

hdbscan.HDBSCAN(algorithm='best', alpha=1.0, approx_min_span_tree=True,
    gen_min_span_tree=True, leaf_size=40, #memory=Memory(cachedir=None),
    metric='euclidean', min_cluster_size=5, min_samples=None, p=None)

clusterer.minimum_spanning_tree_.plot(edge_cmap='viridis',
                                      edge_alpha=0.6,
                                      node_size=80,
                                      edge_linewidth=2)

clusterer.single_linkage_tree_.plot(cmap='viridis', colorbar=True)
clusterer.condensed_tree_.plot()

palette = sns.color_palette()
cluster_colors = [sns.desaturate(palette[col], sat)
                  if col >= 0 else (0.5, 0.5, 0.5) for col, sat in
                  zip(clusterer.labels_, clusterer.probabilities_)]
plt.scatter(test_data.T[0], test_data.T[1], c=cluster_colors, **plot_kwds)
'''