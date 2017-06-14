'''
The sample***.txt files of ANP460 consist of raw eye tracking recordings from the 
Microsoft SMI. For the purpose of datadings we'll preprocess eye tracking data to create 
fixation points.  
'''
from __future__ import division
import pdb
from itertools import compress
import os
import os.path as pt

import csv

import pandas as pd
import numpy as np
from numpy import genfromtxt

import matplotlib.pyplot as plt
from PIL import Image
import scipy.misc as sci
from dispersion import *
import time
from matplotlib.colors import LinearSegmentedColormap

im_root = '/Users/magnus/master/DFKI/data/images_original'
eye_root = '/Users/magnus/master/DFKI/data/eye_tracking_data'

outdir = '/Users/magnus/master/DFKI/data/fixation_data'

participants = os.listdir(eye_root)[1:]
image_names = os.listdir(im_root)

cdict1 = {'red':   ((0.0, 0.0, 0.0),
                   (1.0, 1.0, 1.0)),

         'green': ((0.0, 0.0, 0.0),
                   (1.0, 1.0, 1.0)),

         'blue':  ((0.0, 0.0, 0.0),
                   (1.0, 1.0, 1.0)),

         'alpha': ((0.0, 0.0, 0),
                   (1.0, 1.0, 0.4))
        }

cdict2 = {'red':   ((0.0, 0.0, 0.0),
                   (1.0, 1.0, 0.0)),

         'green': ((0.0, 0.0, 0.0),
                   (1.0, 1.0, 0.0)),

         'blue':  ((0.0, 0.0, 0.0),
                   (1.0, 1.0, 0.0)),

         'alpha': ((0.0, 1.0, 1),
                   (1.0, 0.0, 0.))
        }

trans_white = LinearSegmentedColormap('transWhite', cdict1)
trans_black = LinearSegmentedColormap('transBlack', cdict2)

def load_experiment(participant, image_name):
    sample = 'sample' + str(int(image_name[0:3])+1) + '.txt'
    path = os.path.join(eye_root, participant, sample)
    raw_data = genfromtxt(path, delimiter=',')[:, 0:3]
    # Timestamp starts at 0 seconds.
    raw_data[:, 0] -= raw_data[0, 0]
    # Time unit: seconds.
    raw_data[:, 0] /= 1000000
    return raw_data

def image_size(image_name):
    path = os.path.join(im_root, image_name)
    x = Image.open(path)
    return x.size[0], x.size[1]

def calculate_offset(image_name, target_size=(1440, 960)):
    w, h = image_size(image_name)
    tw, th = target_size
    source_aspect = w / h
    target_aspect = tw / th
    if source_aspect < target_aspect:
        offset = (tw - source_aspect * th) / -2, 0
    elif source_aspect > target_aspect:
        offset = 0, (th - tw / source_aspect) / -2
    else:
        offset = 0, 0
    return offset

def calculate_dimensions(image_name, target_size=(1440, 960)):
    w, h = image_size(image_name)
    tw, th = target_size
    source_aspect = w / h
    target_aspect = tw / th
    if source_aspect <= target_aspect:
        h = th
        w = th * source_aspect
    elif source_aspect > target_aspect:
        h = tw / source_aspect
        w = tw
    new_dim = int(w), int(h)
    return new_dim

def wrangle_raw_data(raw_data, image_name, threshold=[0.3, 6]):
    dim = calculate_dimensions(image_name)
    offset = calculate_offset(image_name)
    # 0: Time, 1: x-coordinate, 2: y-coordinate
    raw_data[:, 1] += offset[0]
    # correct 960 with dim ...
    raw_data[:, 2] = 960 - raw_data[:, 2]
    raw_data[:, 2] += offset[1]
    # time threshold, saves computation time during dispersion algorithm
    raw_data = raw_data[np.logical_and(raw_data[:, 0] >= threshold[0],
                                       raw_data[:, 0] <= threshold[1])]
    raw_data = raw_data[np.logical_and(raw_data[:, 1] > 0,
                                       raw_data[:, 2] > 0)]
    raw_data = raw_data[np.logical_and(raw_data[:, 1] < dim[0],
                                       raw_data[:, 2] < dim[1])]
    return raw_data

def get_fixations_of_experiment(participant, image_name, top=None):
    raw_data = load_experiment(participant, image_name)
    wrangled_data = wrangle_raw_data(raw_data, image_name)
    fixations = dispersion(wrangled_data, r_initial=20, r_drift=30)
    return fixations

def participant_answers(participant):
    path = os.path.join(eye_root, participant, 'answer.txt')
    answers = genfromtxt(path, delimiter=",", dtype="|S5")[:,1]
    if len(answers) != 460:
        'Number of answers does not equal the number of images.'
    return answers

def write_fixation_sets(outdir):
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    for participant in participants:
        path = os.path.join(outdir, participant[0:3])
        if not os.path.exists(path):
            os.makedirs(path)
        answers_path = os.path.join(path, 'answers')
        np.save(answers_path, participant_answers(participant))
        for image_name in image_names:
            fixation_path = os.path.join(path, image_name[0:3]+'.npy')
            fixations = get_fixations_of_experiment(participant, image_name)
            np.save(fixation_path, fixations)

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
    write_fixation_sets(outdir)
    pass



if __name__ == '__main__':
    main()