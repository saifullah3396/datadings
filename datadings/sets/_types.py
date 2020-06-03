# AUTO-GENERATED FILE! DO NOT EDIT!


def ANP460Data(
        image,
        experiments,
        key,
        anp,
        type
):
    return {
        'image': image,
        'experiments': experiments,
        'key': key,
        'anp': anp,
        'type': type
    }


def ANP460Experiment(
        locations,
        map,
        answer,
        duration
):
    return {
        'locations': locations,
        'map': map,
        'answer': answer,
        'duration': duration
    }


def CIFAR100Data(
        image,
        label,
        coarse_label,
        key
):
    return {
        'image': image,
        'label': label,
        'coarse_label': coarse_label,
        'key': key
    }


def ImageClassificationData(
        image,
        label,
        key
):
    return {
        'image': image,
        'label': label,
        'key': key
    }


def ImageData(
        image,
        key
):
    return {
        'image': image,
        'key': key
    }


def ImageSegmentationData(
        image,
        target_image,
        key,
        classes,
        class_weights
):
    return {
        'image': image,
        'target_image': target_image,
        'key': key,
        'classes': classes,
        'class_weights': class_weights
    }


def MaskedImageSegmentationData(
        image,
        label_image,
        mask,
        key,
        classes,
        class_weights
):
    return {
        'image': image,
        'label_image': label_image,
        'mask': mask,
        'key': key,
        'classes': classes,
        'class_weights': class_weights
    }


def Places2017Data(
        image,
        tasks,
        key,
        classes
):
    return {
        'image': image,
        'tasks': tasks,
        'key': key,
        'classes': classes
    }


def Places2017Task(
        label_image,
        class_weights
):
    return {
        'label_image': label_image,
        'class_weights': class_weights
    }


def SaliencyData(
        image,
        experiments,
        key
):
    return {
        'image': image,
        'experiments': experiments,
        'key': key
    }


def SaliencyExperiment(
        locations,
        map
):
    return {
        'locations': locations,
        'map': map
    }


def SegmentationDisparityData(
        key,
        image,
        label_image,
        disparity_image
):
    return {
        'key': key,
        'image': image,
        'label_image': label_image,
        'disparity_image': disparity_image
    }


def iSUNData(
        image,
        experiments,
        key,
        scenecategory
):
    return {
        'image': image,
        'experiments': experiments,
        'key': key,
        'scenecategory': scenecategory
    }


def iSUNExperiment(
        locations,
        map,
        timestamps,
        fixations
):
    return {
        'locations': locations,
        'map': map,
        'timestamps': timestamps,
        'fixations': fixations
    }
