import pymysql.cursors

class databaseUtils:
    def __init__(self, host, username, password, database):
        self.host = host
        self.username = username
        self.password = password
        self.database = database
    
    def connect(self, host, username, password, database):
        try:
            connection = pymysql.connect(
                host = host,
                user = username,
                password = password,
                db = database,
                charset = 'utf8',
                cursorclass = pymysql.cursors.DictCursor
            )
            return connection
        except Exception as e:
            print(e)
            return False