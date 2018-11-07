import MySQLdb


def connect():
    db = MySQLdb.connect("localhost", "root", "83197862@Home", "stock", 3306, charset='utf8')
    return db


def close(db):
    db.close