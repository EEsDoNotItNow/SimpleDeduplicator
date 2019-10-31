
from pathlib import Path
from PIL import Image as PILImage
import hashlib
import imagehash
import re
from . import Logs
from . import DB

class Image:

    def __init__(self, path):
        self.path = Path(path).expanduser().resolve()
        self.ahash = None
        self.dhash = None
        self.phash = None
        self.whash = None
        self.md5 = None
        self.size = None
        self.height = None
        self.width = None
        self.removed = False
        self.parsed = False
        self.loaded = False


    def pull_from_db(self):
        """Attempt to pull data from the DB.
        """
        db = DB()
        data = db.get_image(self.path)
        if data is None:
            return
        self.ahash = imagehash.hex_to_hash(data['ahash'])
        self.dhash = imagehash.hex_to_hash(data['dhash'])
        self.phash = imagehash.hex_to_hash(data['phash'])
        self.whash = imagehash.hex_to_hash(data['whash'])
        self.md5 = data['md5']
        self.size = data['size']
        self.width = data['width']
        self.height = data['height']
        self.loaded = True


    def upsert_to_db(self):
        DB().upsert_image(self)


    def update_from_drive(self):
        logger = Logs()
        try:
            i = PILImage.open(self.path)
        except OSError:
            logger.error("Not an image...")
            return
        except:
            logger.exception("What happened?")
            exit()
        self.size = self.path.stat().st_size
        try:        
            self.ahash = imagehash.average_hash(i)
            self.phash = imagehash.phash(i)
            self.dhash = imagehash.dhash(i)
            self.whash = imagehash.whash(i)
            self.md5 = hashlib.md5(i.tobytes()).hexdigest()
        except:
            logger.exception("What happened?")
            exit()
        self.parsed = True

    @property
    def real_suffix(self):
        # return self.path.suffix.split('?')[0]
        f = list(filter(None, re.split("[?&]+", self.path.suffix)))
        try:
            return f[0]
        except IndexError:
            return self.path.suffix