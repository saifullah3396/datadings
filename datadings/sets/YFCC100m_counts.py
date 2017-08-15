import os.path as pt
import gzip
import json


ROOT_DIR = pt.abspath(pt.dirname(__file__))


with gzip.open(pt.join(ROOT_DIR, 'YFCC100m_counts.json.gz'), 'rt') as f:
    FILE_COUNTS = json.load(f)
FILES_TOTAL = sum([n for _, n in FILE_COUNTS])
