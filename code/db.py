
import sqlite3
from . import Logs

class DB:
    __shared_state = {'init':False}
  
    def __init__(self):
        self.__dict__ = self.__shared_state
        if not self.init:
            self.log = Logs()
            self.conn = sqlite3.connect("duplicates.db")
            self.conn.row_factory = self.dict_factory
            # self.cur = conn.cursor() # We really should just make cursors on the fly
            self.init = True
            self.log.info("Init the DB")


    def upsert_image(self, image_dict):
        pass


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
        logger.info("Check to see if images exists.")
        if not table_exists(cur, "images"):
            logger.info("Create images table")
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
            conn.commit()
        else:
            logger.info("images exists, continue")

        logger.info("Check to see if skips exists.")
        if not table_exists(cur, "skips"):
            logger.info("Create skips table")
            cmd = """
                CREATE TABLE skips
                (
                    file_name1 TEXT,
                    file_name2 TEXT,
                    UNIQUE(file_name1, file_name2)
                )
            """
            cur.execute(cmd)
            conn.commit()
        else:
            logger.info("images exists, continue")