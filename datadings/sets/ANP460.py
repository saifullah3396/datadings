from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import

from . import make_typefun


ANP460Data = make_typefun(
    'ANP460Data',
    'image', 'experiments', 'key', 'anp', 'type',
)
ANP460Experiment = make_typefun(
    'ANP460Experiment',
    'locations', 'map', 'answer', 'duration',
)
