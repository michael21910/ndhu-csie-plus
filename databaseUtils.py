import pymysql.cursors
import copy

def format_string(question_list):
    _q = copy.deepcopy(question_list)
    for i, q in enumerate(question_list):
        for key, val in q.items():
            if (key == "replies"):
                _q[i][key] = "{} {}".format(val, "replies" if (val > 1) else "reply")
            elif (key == "time"):
                _q[i][key] = val.strftime("%Y/%m/%d")
            elif (key == "id"):
                _q[i][key] = "question-{}".format(val)
        del _q[i]["id"]
    return _q

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

    def get_index_contents(self, connection):
        try:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM `questions`"
                cursor.execute(sql)
                result = cursor.fetchall()
                """
                result = tuple(tuple(row.values()) for row in result)
                """
                result = format_string(result)
                return result
        except Exception as e:
            print(e)
            return 'False'
    