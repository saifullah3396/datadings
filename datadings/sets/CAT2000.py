from datadings.sets import convert_saliency as convert_cat2000
from datadings.sets import SaliencyData, SaliencyExperiment
from datadings.reader import MsgpackReader

def convert_saliency(item):
    return SaliencyData(
            item[0],
            [SaliencyExperiment(*experiment[:2] if len(experiment) < 4 # locations
                                else [experiment[3], experiment[1]]) for experiment in item[1]], # fixations
            item[2],
    )


class CAT2000Reader(MsgpackReader):
    _convert = staticmethod(convert_saliency)
