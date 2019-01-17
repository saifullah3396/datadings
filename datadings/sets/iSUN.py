from __future__ import unicode_literals

from . import make_typefun


iSUNData = make_typefun(
    'iSUNData',
    'image', 'experiments', 'key', 'scenecategory',
)
iSUNExperiment = make_typefun(
    'iSUNExperiment',
    'locations', 'map', 'timestamps', 'fixations',
)
