
import sqlite3
from . import Logs
from .args import Args

class DB:
    __shared_state = {'init':False}
  
    def __init__(self):
        self.__dict__ = self.__shared_state
        if not self.init:
            self.log = Logs()
            self.conn = sqlite3.connect("duplicates.db")
            self.conn.row_factory = self.dict_factory
            # self.cur = conn.cursor() # We really should just make cursors on the fly
            self.conn.enable_load_extension(True)
            self.conn.cursor().execute("SELECT load_extension('code/sqlite-hexhammdist.so', 'hexhammdist_init')")
            self.init = True
            self.log.info("Init the DB")
            self.init_tables()


    def upsert_image(self, image):
        cur = self.conn.cursor()
        cmd = """
        INSERT OR REPLACE INTO images 
        (   file_name,
            height,
            width,
            size,
            ahash,
            phash,
            dhash,
            whash,
            md5
        ) VALUES (?,?,?,?,?,?,?,?,?)
        """
        cur.execute(cmd, 
            (   str(image.path),
                image.height,
                image.width,
                image.size,
                str(image.ahash),
                str(image.phash),
                str(image.dhash),
                str(image.whash),
                str(image.md5)
            )
        )
        self.conn.commit()


    def get_image(self, path):
        cur = self.conn.cursor()
        cmd = """
        SELECT * FROM images WHERE file_name=?
        """
        return cur.execute(cmd, (str(path),) ).fetchone()


    def iter_images(self, max_row_id):
        cur = self.conn.cursor()
        for i in cur.execute("SELECT *,rowid FROM images WHERE removed = 0 AND rowid<=? ORDER BY rowid DESC",(max_row_id,)).fetchall():
            yield i


    def get_max_rowid(self):
        cur = self.conn.cursor()
        return cur.execute('SELECT max(rowid) as rowid FROM images').fetchone()['rowid']


    def iter_images_hammdist(self, current_image):
        cur = self.conn.cursor()
        args = Args()
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
        for i in cur.execute(cmd):
            yield i


    def is_skipped(self, file1, file2):
        cur = self.conn.cursor()
        if cur.execute("SELECT * FROM skips WHERE file_name1=? AND file_name2=?", (file1, file2) ).fetchone() is not None:
            return True
        if cur.execute("SELECT * FROM skips WHERE file_name1=? AND file_name2=?", (file1, file2) ).fetchone() is not None:
            return True
        return False


    @staticmethod
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d


    def table_exists(self, cur, table_name):
        cur = self.conn.cursor()
        cmd = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
        if cur.execute(cmd).fetchone():
            return True
        return False


    def mark_removed(self, file_name):
        cur = self.conn.cursor()
        cur.execute("UPDATE images SET removed=1 WHERE file_name=?",(str(file_name),))
        self.conn.commit()
        logger.info(f"File removed: {str(file_name)}")
        # time.sleep(1)


    def insert_skip(self, file_name1, file_name2):
        cur = self.conn.cursor()
        cur.execute("INSERT OR IGNORE INTO skips (file_name1, file_name2) VALUES (?,?)", 
            (str(file_name1), str(file_name2)))
        cur.execute("INSERT OR IGNORE INTO skips (file_name1, file_name2) VALUES (?,?)", 
            (str(file_name2), str(file_name1)))
        self.conn.commit()


    def insert_md5(self, file_name, md5):
        cur = self.conn.cursor()
        cur.execute("UPDATE images SET md5=? WHERE file_name=?",
            (
                md5,
                file_name
                )
            )
        self.conn.commit()


    def init_tables(self):
        cur = self.conn.cursor()
        self.log.info("Check to see if 'images' exists.")
        if not self.table_exists(cur, "images"):
            self.log.info("Create images table")
            cmd = """
                CREATE TABLE images
                (
                    file_name TEXT UNIQUE,
                    height INT,
                    width INT,
                    size INT,
                    ahash TEXT,
                    phash TEXT,
                    dhash TEXT,
                    whash TEXT,
                    md5 TEXT,
                    removed BOOLEAN DEFAULT 0
                )
            """
            cur.execute(cmd)
            self.conn.commit()
        else:
            self.log.info("'images' exists, continue")

        self.log.info("Check to see if 'skips' exists.")
        if not self.table_exists(cur, "skips"):
            self.log.info("Create skips table")
            cmd = """
                CREATE TABLE skips
                (
                    file_name1 TEXT,
                    file_name2 TEXT,
                    UNIQUE(file_name1, file_name2)
                )
            """
            cur.execute(cmd)
            self.conn.commit()
        else:
            self.log.info("'skips' exists, continue")
