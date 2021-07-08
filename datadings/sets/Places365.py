from .tools import load_json

CLASSES = load_json("Places365_classes.json.gz")
CLASS_TO_ID = {c: i for i, c in enumerate(CLASSES)}
ID_TO_CLASS = {i: c for i, c in enumerate(CLASSES)}
