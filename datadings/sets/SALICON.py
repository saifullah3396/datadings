from ..reader import MsgpackReader as SALICONReader
from . import SaliencyData as SALICONData


class SALICONExperiment(dict):
    def __init__(self, locations, map, timestamps, fixations):
        super(SALICONExperiment, self).__init__(
            locations=locations, map=map, timestamps=timestamps,
            fixations=fixations,
        )
