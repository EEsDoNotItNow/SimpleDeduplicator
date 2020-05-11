
from pathlib import Path
import re
import time
import os
from . import DB, Logs, ImageCollection

class NameFix:

    def __init__(self, source_dir):
        self.source_dir = Path(source_dir).expanduser().resolve()
        self.log = Logs()

    def run(self):

        ic = ImageCollection(self.source_dir)
        total = 0
        for i in ic:
            if len(i.name.split('?')) > 1:
                self.log.info("Detected malformed filename, correcting")
                f = list(filter(None, re.split("[?&]+", i.name)))
                file_name = Path(f[0])

                # Check to see if we need to modify our file_name
                while Path(i.parent,file_name).is_file():
                    file_name = file_name.stem + "_copy" + file_name.suffix
                file_name = Path(i.parent,file_name)
                self.log.info(f"New filename is {file_name} (from {i})")
                os.rename(i, file_name)
                total += 1
        self.log.info(f"Renamed {total} files")

