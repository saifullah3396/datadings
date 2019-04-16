# AUTO-GENERATED FILE! DO NOT EDIT!
from __future__ import unicode_literals


def ANP460Data(image, experiments, key, anp, type): return {u'image': image, u'experiments': experiments, u'key': key, u'anp': anp, u'type': type}


def ANP460Experiment(locations, map, answer, duration): return {u'locations': locations, u'map': map, u'answer': answer, u'duration': duration}


def CIFAR100Data(image, label, coarse_label, key): return {u'image': image, u'label': label, u'coarse_label': coarse_label, u'key': key}


def ImageClassificationData(image, label, key): return {u'image': image, u'label': label, u'key': key}


def ImageSegmentationData(image, target_image, key, classes, class_weights): return {u'image': image, u'target_image': target_image, u'key': key, u'classes': classes, u'class_weights': class_weights}


def MaskedImageSegmentationData(image, label_image, mask, key, classes, class_weights): return {u'image': image, u'label_image': label_image, u'mask': mask, u'key': key, u'classes': classes, u'class_weights': class_weights}


def Places2017Data(image, tasks, key, classes): return {u'image': image, u'tasks': tasks, u'key': key, u'classes': classes}


def Places2017Task(label_image, class_weights): return {u'label_image': label_image, u'class_weights': class_weights}


def SaliencyData(image, experiments, key): return {u'image': image, u'experiments': experiments, u'key': key}


def SaliencyExperiment(locations, map): return {u'locations': locations, u'map': map}


def SegmentationDisparityData(image, disparity_map, label_image, key, classes, class_weights): return {u'image': image, u'disparity_map': disparity_map, u'label_image': label_image, u'key': key, u'classes': classes, u'class_weights': class_weights}


def UnsupervisedImageData(image, key): return {u'image': image, u'key': key}


def iSUNData(image, experiments, key, scenecategory): return {u'image': image, u'experiments': experiments, u'key': key, u'scenecategory': scenecategory}


def iSUNExperiment(locations, map, timestamps, fixations): return {u'locations': locations, u'map': map, u'timestamps': timestamps, u'fixations': fixations}
