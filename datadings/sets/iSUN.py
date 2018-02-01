from __future__ import unicode_literals

from . import make_typefun


make_typefun(
    b'iSUNData',
    'image', 'experiments', 'key', 'scenecategory',
)
make_typefun(
    b'iSUNExperiment',
    'locations', 'map', 'timestamps', 'fixations',
)
