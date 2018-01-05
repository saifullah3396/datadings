class ImageClassificationData(dict):
    def __init__(self, image, label, key):
        super(ImageClassificationData, self).__init__(
            image=image, label=label, key=key
        )


class ImageSegmentationData(dict):
    def __init__(self, image, label_image, key, classes, class_weights):
        super(ImageSegmentationData, self).__init__(
            image=image, label_image=label_image, key=key,
            classes=classes, class_weights=class_weights
        )


class MaskedImageSegmentationData(dict):
    def __init__(self, image, label_image, mask, key, classes, class_weights):
        super(MaskedImageSegmentationData, self).__init__(
            image=image, label_image=label_image, mask=mask, key=key,
            classes=classes, class_weights=class_weights
        )


class SegmentationDisparityData(dict):
    def __init__(self, image, disparity_map, label_image, key, classes, class_weights):
        super(SegmentationDisparityData, self).__init__(
            image=image, disparity_map=disparity_map, label_image=label_image, key=key,
            classes=classes, class_weights=class_weights
        )


class SaliencyData(dict):
    def __init__(self, image, experiments, key):
        super(SaliencyData, self).__init__(
            image=image, experiments=experiments, key=key
        )


class SaliencyExperiment(dict):
    def __init__(self, locations, map):
        super(SaliencyExperiment, self).__init__(
            locations=locations, map=map,
        )


class UnsupervisedImageData(dict):
    def __init__(self, image, key):
        super(UnsupervisedImageData, self).__init__(image=image, key=key)
