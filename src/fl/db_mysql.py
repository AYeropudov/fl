import pymysql
from fl import settings

class MySqlHelper:
    def connect(self):
        return pymysql.connect(host=settings.DB_MYSQL_HOST,
                               user=settings.DB_MYSQL_USER,
                               passwd=settings.DB_MYSQL_PWD,
                               db=settings.DB_MYSQL)

    def get_all_entry(self):
        connection = self.connect()
        try:
            sql = "SELECT value, count FROM words"
            with connection.cursor() as cursor:
                cursor.execute(sql)
            return cursor.fetchall()
        finally:
            connection.close()

    def add_entry(self, data):
        connection = self.connect()
        try:
            sql = "INSERT INTO words(value, count) VALUES {} on duplicate key update count= count +(count)".format(data)
            with connection.cursor() as cursor:
                cursor.execute(sql)
                connection.commit()

                pass
        finally:
            connection.close()

    def add_many_entries(self, data):
        connection = self.connect()
        try:
            sql = "INSERT INTO words(value, count) VALUES (%s, %s) on duplicate key update count= count +(count)"
            with connection.cursor() as cursor:
                cursor.executemany(sql, data)
                connection.commit()
        finally:
            connection.close()
