import pymysql.cursors
import copy

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
                result = databaseUtils.format_question_list(result)
                return result
        except Exception as e:
            print(e)
            return 'False'
    
    def format_question_list(question_list):
        modified_question_list = copy.deepcopy(question_list)
        for qid, question in enumerate(question_list):
            del modified_question_list[qid]["id"]
            for key, val in question.items():
                if (key == "replies"):
                    modified_question_list[qid][key] = \
                        "{} {}".format(val, ("replies" if (val > 1) else "reply"))
                elif (key == "time"):
                    modified_question_list[qid][key] = \
                        val.strftime("%Y/%m/%d")
                elif (key == "id"):
                    modified_question_list[qid][key] = \
                        "question-{}".format(val)
        return modified_question_list