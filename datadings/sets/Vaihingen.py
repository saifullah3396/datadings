CROP_SIZE = 384

CLASSES = [
    'Impervious surfaces',
    'Buildings',
    'Low vegetation',
    'Tree',
    'Car',
    'Clutter',
]

COLOR_TO_CLASS_MAP = {
    (255, 255, 255): 0,  # Impervious surfaces (white)
    (0, 0, 255): 1,      # Buildings (dark blue)
    (0, 255, 255): 2,    # Low vegetation (light blue)
    (0, 255, 0): 3,      # Tree (green)
    (255, 255, 0): 4,    # Car (yellow)
    (255, 0, 0): 5,      # Clutter (red)
    (0, 0, 0): 6,        # Unclassified (black)
}
