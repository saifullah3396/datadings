# AUTO-GENERATED FILE! DO NOT EDIT!


def ADE20kData(
        key,
        image,
        label,
        label_image,
        parts_images
):
    return {
        'key': key,
        'image': image,
        'label': label,
        'label_image': label_image,
        'parts_images': parts_images
    }


def ANP460Data(
        key,
        image,
        experiments,
        anp,
        type
):
    return {
        'key': key,
        'image': image,
        'experiments': experiments,
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


def ImageClassificationData(
        key,
        image,
        label
):
    return {
        'key': key,
        'image': image,
        'label': label
    }


def ImageCoarseClassificationData(
        key,
        image,
        label,
        coarse_label
):
    return {
        'key': key,
        'image': image,
        'label': label,
        'coarse_label': coarse_label
    }


def ImageData(
        key,
        image
):
    return {
        'key': key,
        'image': image
    }


def ImageDisparitySegmentationData(
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


def ImageInstanceSegmentationData(
        key,
        image,
        label_image,
        instance_image
):
    return {
        'key': key,
        'image': image,
        'label_image': label_image,
        'instance_image': instance_image
    }


def ImageSegmentationData(
        key,
        image,
        label_image
):
    return {
        'key': key,
        'image': image,
        'label_image': label_image
    }


def MaskedImageSegmentationData(
        key,
        image,
        label_image,
        mask
):
    return {
        'key': key,
        'image': image,
        'label_image': label_image,
        'mask': mask
    }


def Places2017Data(
        key,
        image,
        label,
        label_image,
        instance_image,
        boundary
):
    return {
        'key': key,
        'image': image,
        'label': label,
        'label_image': label_image,
        'instance_image': instance_image,
        'boundary': boundary
    }


def SaliencyData(
        key,
        image,
        experiments
):
    return {
        'key': key,
        'image': image,
        'experiments': experiments
    }


def SaliencyExperiment(
        locations,
        map
):
    return {
        'locations': locations,
        'map': map
    }


def SaliencyTimeseriesExperiment(
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
