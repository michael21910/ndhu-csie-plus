import pymysql.cursors
import copy, time

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
                charset = "utf8",
                cursorclass = pymysql.cursors.DictCursor
            )
            return connection
        except Exception as e:
            print(e)
            return False

    def get_index_contents(self, connection):
        try:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM questions;"
                cursor.execute(sql)
                result = cursor.fetchall()
                """
                result = tuple(tuple(row.values()) for row in result)
                """
                result = databaseUtils.format_question_list2(result)
                return result
        except Exception as e:
            print(e)
            return "False"
    
    def insert_question(self, connection, question_dict):
        try:
            with connection.cursor() as cursor:
                sql = "INSERT INTO questions (asker, question, content, replies, likes) VALUE ('{}', '{}', '{}', 0, 0);".format(
                    question_dict["asker"], question_dict["question"], question_dict["content"]
                )
                #print(sql)
                #time.sleep(5)
                cursor.execute(sql)
                sql = "SELECT LAST_INSERT_ID();"
                cursor.execute(sql)
                qid = cursor.fetchall()
                #print(qid, type(qid))
                _qid = qid[0]["LAST_INSERT_ID()"]
                #print(_qid)
                if (self.construct_question_table(connection, _qid) == -1):
                    return -1
                connection.ping()
                connection.commit()
                return 1
        except Exception as e:
            #print("insert fail")   
            print(e)     
            return -1
    
    def construct_question_table(self, connection, question_id):
        try:
            with connection.cursor() as cursor:
                sql = "CREATE TABLE question_{} (id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY, replier VARCHAR(20), time TIMESTAMP, content VARCHAR(200));".format(
                    question_id    
                )
                #print(sql)
                #print("\n\n")
                cursor.execute(sql)
                connection.ping()
                connection.commit()
                return 1
        except Exception as e:
            print(e)
            return -1
    
    def get_question_contents(self, connection, question_id):
        try:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM question_{};".format(question_id)
                cursor.execute(sql)
                replies = databaseUtils.format_question_list(cursor.fetchall(), remove_content = False)
                sql = "SELECT * FROM questions WHERE (id = {});".format(question_id)
                cursor.execute(sql)
                question = databaseUtils.format_question_list(cursor.fetchall(), remove_content = False, remove_id = False)[0]
                result = {"question" : question, "replies" : replies}
                return result
        except Exception as e:
            print(e)
    
    def insert_reply(self, connection, reply_dict):
        try:
            with connection.cursor() as cursor:
                sql = "INSERT INTO question_{} (replier, content) VALUE ('{}', '{}');".format(
                    reply_dict["question_id"], reply_dict["replier"], reply_dict["reply_content"]    
                )
                cursor.execute(sql)
                sql = "UPDATE questions SET replies = replies + 1 WHERE (id = {});".format(
                    reply_dict["question_id"]    
                )
                cursor.execute(sql)
                connection.ping()
                connection.commit()
                return 1
        except Exception as e:
            print(e)
            return -1
    
    def format_question_list2(question_list):
        modified_question_list = []
        for qid, question in enumerate(question_list):
            _dictionary = {}
            for key, val in question.items():
                if key == "replies":
                    _dictionary[key] = "{} {}".format(val, ("replies" if (val != 1) else "reply"))
                elif key == "time":
                    _dictionary[key] = val.strftime("%Y/%m/%d")
                elif ((key == "asker") and (val == "")):
                    _dictionary[key] = "Anonymous"
                elif (key != "id"):
                    _dictionary[key] = val
            dictionary = { "question_id" : question_list[qid]["id"], "question_data" : _dictionary }
            modified_question_list.append(dictionary)
        #print(modified_question_list)
        return modified_question_list
    
    def format_question_list(question_list, remove_content = True, remove_id = True):
        modified_question_list = copy.deepcopy(question_list)
        for qid, question in enumerate(question_list):
            if (remove_id):
                del modified_question_list[qid]["id"]
            if (remove_content):
                del modified_question_list[qid]["content"]
            for key, val in question.items():
                if key == "replies":
                    modified_question_list[qid][key] = \
                        "{} {}".format(val, ("replies" if (val != 1) else "reply"))
                elif key == "time":
                    modified_question_list[qid][key] = \
                        val.strftime("%Y/%m/%d")
                elif ((key == "asker") and (val == "")):
                    modified_question_list[qid][key] = \
                        "Anonymous"
        #print(modified_question_list)
        return modified_question_list