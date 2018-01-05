from . import datatype


ANP460Data = datatype(
    'ANP460Data',
    'image', 'experiments', 'key', 'anp', 'type',
)
ANP460Experiment = datatype(
    'ANP460Experiment',
    'locations', 'map', 'answer', 'duration',
)
