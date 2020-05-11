from . import DB, Logs, ImageCollection, Image, Args
import time
from pathlib import Path
from PIL import Image as PILImage
import shutil


class Deduplicator:


    def __init__(self, source_dir):
        self.source_dir = Path(source_dir).expanduser().resolve()
        self.log = Logs()


    def run(self):
        self.log.info("Begin run")

        args = Args()
        db = DB()

        if args.rowid is None:
            args.rowid = db.get_max_rowid()

        self.log.info(args.rowid)
        t1 = time.time()
        for idx, current_image in enumerate(db.iter_images(args.rowid)):
            
            p_current = Path(current_image['file_name'])
            if not p_current.is_file():
                db.mark_removed(p_current)
                self.log.warning(f"Removed a non-existent file: {p_current}")
                continue
            
            self.log.info(current_image['rowid'])
            # Check if current_image even exists, continue if not
            for db_image in db.iter_images_hammdist(current_image):
                # Check if this image combo has been seen before, skip if so

                p_db = Path(db_image['file_name'])

                if not p_db.is_file():
                    db.mark_removed(db_image['file_name'])
                    continue

                if db.is_skipped(str(p_current), str(db_image['file_name'])):
                    self.log.info(f"Skipping per DB, file was {db_image['file_name']}")
                    continue


                ts_a = p_current.stat().st_mtime
                ts_b = p_db.stat().st_mtime

                a_is_younger = ts_a < ts_b

                # Ask user WTF to do (or run MD5 if needed)

                self.log.warning("Hashes match, show the images and quit!")
                self.log.info("A:")
                self.log.info(f"  File Name: {p_current} ")
                self.log.info(f"       Size: {p_current.stat().st_size} ")
                self.log.info(f"       MD5: {current_image['md5']} ")
                self.log.info("B:")
                self.log.info(f"  File Name: {p_db} ")
                self.log.info(f"       Size: {p_db.stat().st_size} ")
                self.log.info(f"       MD5: {db_image['md5']} ")
                self.log.info(f"ahash: {db_image['d_ahash']}")
                self.log.info(f"phash: {db_image['d_phash']}")
                self.log.info(f"dhash: {db_image['d_dhash']}")
                self.log.info(f"whash: {db_image['d_whash']}")
                self.log.info(f"A to keep {p_current}")
                self.log.info(f"B to keep {db_image['file_name']}")
                self.log.info("D to display")
                self.log.info(f"S to skip")
                self.log.info("N/C do do nothing/continue")
                if p_current.stat().st_size < db_image['size']:
                    self.log.info(f"Suggesting B, as it is larger ({db_image['size']} > {p_current.stat().st_size})")
                elif p_current.stat().st_size > db_image['size']:
                    self.log.info(f"Suggesting A, as it is larger ({db_image['size']} < {p_current.stat().st_size})")
                while 1:
                    if current_image['md5'] == db_image['md5'] and args.md5:
                        self.log.info("md5 is identical! Keeping A, moving B")
                        choice = 'a'
                    elif current_image['md5'] == db_image['md5'] and  not args.md5:
                        self.log.info("md5 is identical!")
                        self.log.info(f"{'A' if a_is_younger else 'B'} is younger, recommend keeping it")
                        choice = input("> ").lower()
                    else:
                        choice = input("> ").lower()

                    if choice == 'n' or choice =='c':
                        self.log.info("Do nothing and move on.")
                        break

                    if choice == "s":
                        db.insert_skip(p_current, p_db)
                        break

                    if choice == "d":
                        I1 = PILImage.open(p_current)
                        I2 = PILImage.open(db_image['file_name'])
                        I1.show()
                        I2.show()
                        continue

                    elif choice == "a":
                        file_to_move = Path(db_image['file_name'])

                    elif choice == "b":
                        file_to_move = p_current

                    # TODO: This really should be a config value in the script
                    file_dest = Path("/home/pheonix/Duplicates/",file_to_move.name)
                    while Path(file_dest).is_file():
                        file_dest = Path(file_dest.parent, file_dest.stem + "_copy" + file_dest.suffix)
                        self.log.info(f"Had to rename file to {file_dest}")
                    shutil.move(str(file_to_move), str(file_dest))
                    db.mark_removed(file_to_move)
                    db_changed = True
                    break
        t2 = time.time()
        self.log.info(f"Ran in {t2-t1:.3f} seconds")        

        self.log.info("Finished run")