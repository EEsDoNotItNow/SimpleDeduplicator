from pathlib import Path
from .image import Image

class ImageCollection:
    image_exts = [
        # '.gif',
        # '.gifv',
        '.jpeg',
        '.jpg',
        '.jpgi',
        '.png',
        '.xx',
        ]

    def __init__(self, base_dir):
        self.base_dir = Path(base_dir).expanduser()


    def __iter__(self):
        for p in self.base_dir.glob("**/*"):
            if not p.is_file():
                continue
            i = Image(p)
            if i.real_suffix.lower() not in self.image_exts:
                continue
            yield p
        