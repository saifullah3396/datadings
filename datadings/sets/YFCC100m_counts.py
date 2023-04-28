import warnings

from .tools import load_json


warnings.warn(
    "the YFCC100m dataset is deprecated, "
    "please migrate to https://gitlab.com/jfolz/yfcc100m",
    DeprecationWarning,
    stacklevel=2
)


FILE_COUNTS = load_json('YFCC100m_counts.json.xz')
FILES_TOTAL = sum([n for _, n in FILE_COUNTS])
