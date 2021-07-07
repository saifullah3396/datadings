from .tools import load_json

CLASS_TO_ID = load_json("Places356_classes.json.xz")
CLASSES = list(CLASS_TO_ID)
ID_TO_CLASS = {v: k for k, v in CLASS_TO_ID.items()}
