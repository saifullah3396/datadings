from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import


class SALICONExperiment(dict):
    def __init__(self, locations, map, timestamps, fixations):
        super(SALICONExperiment, self).__init__(
            locations=locations, map=map, timestamps=timestamps,
            fixations=fixations,
        )
