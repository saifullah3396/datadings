from .tools import load_json


FILE_COUNTS = load_json('YFCC100m_counts.json.xz')
FILES_TOTAL = sum([n for _, n in FILE_COUNTS])
