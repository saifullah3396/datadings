from . import datatype


iSUNData = datatype(
    'iSUNData',
    'image', 'experiments', 'key', 'scenecategory',
)
iSUNExperiment = datatype(
    'iSUNExperiment',
    'locations', 'map', 'timestamps', 'fixations',
)
