from . import DB, Logs, ImageCollection, Image
import time
from pathlib import Path

class Importer:

    def __init__(self, source_dir):
        self.source_dir = Path(source_dir).expanduser().resolve()
        self.log = Logs()


    def run(self):
        self.log.info("Begin run")
        db = DB()
        ic = ImageCollection(self.source_dir)

        total_images = len([x for x in ic])
        count = 0
        total_bytes = 0
        for i in ic:
            count += 1
            t2 = time.time()
            img = Image(i)

            img.pull_from_db()
            if img.loaded:
                total_bytes += img.size
                continue

            img.update_from_drive()
            if not img.parsed:
                continue

            img.upsert_to_db()
            self.log.info(f"On image {count:,}/{total_images:,} ({count/total_images:.3%})")
            self.log.info(f"Found new image {img.path}")

        self.log.info("Finished run")
