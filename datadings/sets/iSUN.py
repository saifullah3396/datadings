from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

from . import make_typefun


iSUNData = make_typefun(
    'iSUNData',
    'image', 'experiments', 'key', 'scenecategory',
)
iSUNExperiment = make_typefun(
    'iSUNExperiment',
    'locations', 'map', 'timestamps', 'fixations',
)
