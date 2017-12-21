from collections import namedtuple

from ..reader import MsgpackReader as ISUNReader


class iSUNData(dict):
    def __init__(self, image, experiments, key, scenecategory):
        super(iSUNData, self).__init__(
            image=image, experiments=experiments, key=key,
            scenecategory=scenecategory,
        )


class iSUNExperiment(dict):
    def __init__(self, locations, map, timestamps, fixations):
        super(iSUNExperiment, self).__init__(
            locations=locations, map=map,
            timestamps=timestamps, fixations=fixations,
        )
