#!/usr/bin/env python


from PIL import Image
import imagehash
import logging
import pathlib
import sqlite3
import time
import shutil
import hashlib



# Find images not in DB

for p in pathlib.Path('/home/pheonix/Pictures').glob("**/*"):
    if not p.is_file():
        continue

    file_name = str(p)
    data = cur.execute("SELECT * FROM images WHERE file_name=?", (file_name,)).fetchone()
    if data is not None:
        logger.debug(f"File {p} is already in DB, skip")
        continue
    try:
        I = Image.open(p)
    except OSError:
        # logger.debug("Not an image...")
        continue
    except:
        logger.exception("What happened?")
        exit()
    logger.info(str(p))
    # print(I.width, I.height, I.size,p.stat().st_size)
    try:        
        ahash = imagehash.average_hash(I)
        phash = imagehash.phash(I)
        dhash = imagehash.dhash(I)
        whash = imagehash.whash(I)
    except:
        logger.exception("What happened?")
        exit()
    height = I.height
    width = I.width
    size = p.stat().st_size

    md5_current = hashlib.md5(Image.open(p).tobytes()).hexdigest()

    ahash = str(ahash)
    phash = str(phash)
    dhash = str(dhash)
    whash = str(whash)  
    cmd = """
        INSERT INTO images 
        (
            file_name,
            height,
            width,
            size,
            ahash,
            phash,
            dhash,
            whash,
            md5
        ) VALUES (                
            :file_name,
            :height,
            :width,
            :size,
            :ahash,
            :phash,
            :dhash,
            :whash,
            :md5_current
        )
        """
    cur.execute(cmd, locals())
    conn.commit()
    logger.info(f"Saved {p}")

logger.info("Load extention")
conn.enable_load_extension(True)
cur.execute("SELECT load_extension('/home/pheonix/Git/sqlite-hexhammdist/sqlite-hexhammdist.so','hexhammdist_init')")

# Process images to check for duplicates
logger.info("Import completed, now checking for duplicates")
t_last = time.time()

if args.rowid is None:
    args.rowid = cur.execute('SELECT max(rowid) as rowid FROM images').fetchone()['rowid']

logger.info(args.rowid)
t1 = time.time()
for idx, current_image in enumerate(cur.execute("SELECT *,rowid FROM images WHERE removed = 0 AND rowid<=? ORDER BY rowid DESC",(args.rowid,) ).fetchall()):
    
    p_current = pathlib.Path(current_image['file_name'])
    if not p_current.exists():
        mark_removed(p_current)
        logger.warning(f"Removed a non-existent file: {p_current}")
        continue


    cmd = f"""
    SELECT 
    *, 
    hexhammdist(ahash,'{current_image['ahash']}') as d_ahash,
    hexhammdist(phash,'{current_image['phash']}') as d_phash,
    hexhammdist(dhash,'{current_image['dhash']}') as d_dhash,
    hexhammdist(whash,'{current_image['whash']}') as d_whash
    FROM images
    WHERE rowid < {current_image['rowid']}
    AND removed = 0
    AND d_ahash < {args.threshold}
    AND d_phash < {args.threshold}
    AND d_dhash < {args.threshold}
    AND d_whash < {args.threshold}
    """
    logger.info(current_image['rowid'])
    # Check if current_image even exists, continue if not
    for db_image in cur.execute(cmd).fetchall():
        # Check if this image combo has been seen before, skip if so
        if cur.execute("SELECT * FROM skips WHERE file_name1=? AND file_name2=?", (str(p_current),str(db_image['file_name'])) ).fetchone() is not None:
            logger.info(f"Skipping per DB, file was {db_image['file_name']}")
            continue
        if cur.execute("SELECT * FROM skips WHERE file_name2=? AND file_name1=?", (str(p_current),str(db_image['file_name'])) ).fetchone() is not None:
            logger.info(f"Skipping per DB, file was {db_image['file_name']}")
            continue
        # Ask user WTF to do (or run MD5 if needed)
        p_db = pathlib.Path(db_image['file_name'])

        logger.warning("Hashes match, show the images and quit!")
        logger.info("A:")
        logger.info(f"  File Name: {p_current} ")
        logger.info(f"       Size: {p_current.stat().st_size} ")
        logger.info(f"       MD5: {current_image['md5']} ")
        logger.info("B:")
        logger.info(f"  File Name: {p_db} ")
        logger.info(f"       Size: {p_db.stat().st_size} ")
        logger.info(f"       MD5: {db_image['md5']} ")
        logger.info(f"ahash: {db_image['d_ahash']}")
        logger.info(f"phash: {db_image['d_phash']}")
        logger.info(f"dhash: {db_image['d_dhash']}")
        logger.info(f"whash: {db_image['d_whash']}")
        logger.info(f"A to keep {p_current}")
        logger.info(f"B to keep {db_image['file_name']}")
        logger.info("D to display")
        logger.info(f"S to skip")
        logger.info("N/C do do nothing/continue")
        if p_current.stat().st_size < db_image['size']:
            logger.info(f"Suggesting B, as it is larger ({db_image['size']} > {p_current.stat().st_size})")
        elif p_current.stat().st_size > db_image['size']:
            logger.info(f"Suggesting A, as it is larger ({db_image['size']} < {p_current.stat().st_size})")
        while 1:
            if current_image['md5'] == db_image['md5']:
                logger.info("md5 is identical! Keeping A, moving B")
                choice = 'a'
            else:
                choice = input("> ").lower()

            if choice == 'n' or choice =='c':
                logger.info("Do nothing and move on.")
                break

            if choice == "s":
                insert_skip(p_current, p_db)
                break

            if choice == "d":
                I1 = Image.open(p_current)
                I2 = Image.open(db_image['file_name'])
                I1.show()
                I2.show()
                continue

            elif choice == "a":
                file_to_move = pathlib.Path(db_image['file_name'])

            elif choice == "b":
                file_to_move = p_current

            # TODO: This really should be a config value in the script
            file_dest = pathlib.Path("/home/pheonix/Duplicates/",file_to_move.name)
            while pathlib.Path(file_dest).is_file():
                file_dest = pathlib.Path(file_dest.parent, file_dest.stem + "_copy" + file_dest.suffix)
                logger.info(f"Had to rename file to {file_dest}")
            shutil.move(str(file_to_move), str(file_dest))
            mark_removed(file_to_move)
            db_changed = True
            break
t2 = time.time()
logger.info(f"Ran in {t2-t1:.3f} seconds")
