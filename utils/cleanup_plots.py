import os
import glob

def cleanup_images():
    """Удаляет старые изображения перед новым запуском."""
    patterns = [
        "output/districts/plots/*.png",
        "output/districts/diagrams/*.png",
        "output/regions/plots/*.png",
        "output/regions/diagrams/*.png",
        "output/all_regions/plots/*.png",
        "output/all_regions/diagrams/*.png"
    ]
    for pattern in patterns:
        for file in glob.glob(pattern):
            try:
                os.remove(file)
            except OSError:
                pass
