import pymysql.cursors
import copy
import string
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

def format_string(target_string):
    return target_string.replace("'", "\\'")

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
                result.reverse()
                return databaseUtils.format_question_lists(result)
        except Exception as e:
            print(e)

    def insert_question(self, connection, question_dict):
        try:
            with connection.cursor() as cursor:
                sql = "INSERT INTO questions (asker, question, content, replies, likes) VALUE ('{}', '{}', '{}', 0, 0);".format(
                    format_string(question_dict["asker"]), format_string(question_dict["question"]), format_string(question_dict["content"])
                )
                cursor.execute(sql)

                sql = "SELECT LAST_INSERT_ID();"
                cursor.execute(sql)
                qid = cursor.fetchall()[0]["LAST_INSERT_ID()"]

                if (self.construct_question_table(connection, qid) == -1):
                    return -1, None

                connection.ping()
                connection.commit()
                return 1, qid
        except Exception as e:
            print(e)
            return -1, None

    def construct_question_table(self, connection, question_id):
        try:
            with connection.cursor() as cursor:
                sql = "CREATE TABLE question_{} (id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY, replier VARCHAR(20), time TIMESTAMP, content VARCHAR(200));".format(
                    question_id
                )
                cursor.execute(sql)

                sql = "CREATE TABLE question_{}_upvoter (id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY, upvoter VARCHAR(20));".format(
                    question_id
                )
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
                replies = databaseUtils.format_reply_lists(cursor.fetchall())

                sql = "SELECT * FROM questions WHERE (id = {});".format(question_id)
                cursor.execute(sql)

                question = databaseUtils.format_question_lists(cursor.fetchall())[0]

                return { "question" : question, "replies" : replies }
        except Exception as e:
            print(e)

    def insert_reply(self, connection, reply_dict):
        try:
            with connection.cursor() as cursor:
                sql = "INSERT INTO question_{} (replier, content) VALUE ('{}', '{}');".format(
                    reply_dict["question_id"], format_string(reply_dict["replier"]), format_string(reply_dict["reply_content"])
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

    def upvote_question(self, connection, question_id, username):
        try:
            with connection.cursor() as cursor:

                sql = "SELECT * FROM question_{}_upvoter WHERE (upvoter = '{}');".format(
                    question_id, format_string(username)
                )
                cursor.execute(sql)

                if (len(cursor.fetchall()) == 0):
                    sql = "UPDATE questions SET likes = likes + 1 WHERE (id = {});".format(question_id)
                    cursor.execute(sql)
                    sql = "INSERT INTO question_{}_upvoter (upvoter) VALUE ('{}');".format(question_id, format_string(username))
                else:
                    sql = "UPDATE questions SET likes = likes - 1 WHERE (id = {});".format(question_id)
                    cursor.execute(sql)
                    sql = "DELETE FROM question_{}_upvoter WHERE (upvoter = '{}');".format(question_id, format_string(username))
                cursor.execute(sql)

                connection.ping()
                connection.commit()
                return 1
        except Exception as e:
            print(e)
            return -1

    def format_question_lists(question_list):
        modified_question_list = []
        for qid, question in enumerate(question_list):
            dictionary = {}
            for key, val in question.items():
                if key == "replies":
                    dictionary[key] = "{} {}".format(val, ("replies" if (val != 1) else "reply"))
                elif key == "time":
                    dictionary[key] = val.strftime("%Y/%m/%d")
                elif ((key == "asker") and (val == "")):
                    dictionary[key] = "Anonymous"
                elif (key != "id"):
                    dictionary[key] = val
            modified_question_list.append({ "question_id" : question_list[qid]["id"], "question_data" : dictionary })
        return modified_question_list

    def format_reply_lists(reply_list):
        modified_reply_list = copy.deepcopy(reply_list)
        for idx, reply in enumerate(reply_list):
            del modified_reply_list[idx]["id"]
            modified_reply_list[idx]["time"] = reply["time"].strftime("%Y/%m/%d")
        return modified_reply_list

    def login_user_check(self, connection, username, password):
        try:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM `users` WHERE `username` = %s AND `password` = %s"
                cursor.execute(sql, (username, password))
                result = cursor.fetchone()
                if result is not None:
                    return "True"
                else:
                    return "DNE"
        except Exception as e:
            print(e)
            return "False"

    def check_username_exists(self, connection, username):
        try:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM `users` WHERE `username` = %s"
                cursor.execute(sql, (username, ))
                result = cursor.fetchone()
                if result is not None:
                    return "True"
                else:
                    return "DNE"
        except Exception as e:
            print(e)
            return "False"

    def add_user(self, connection, username, email, password):
        try:
            with connection.cursor() as cursor:
                token = ''.join(random.sample(string.ascii_letters + string.digits, 10))
                sql = "INSERT INTO `users` (`username`, `email`, `password`, `token`) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (username, email, password, token))
                connection.commit()
                databaseUtils.send_email(email, token)
                return "True"
        except Exception as e:
            print(e)
            return "False"

    def send_email(email, token):
        content = MIMEMultipart()
        content["subject"] = "Welcome to NDHU CSIEplus"
        content["from"] = "ndhucsieplus@gmail.com"
        content["to"] = email
        content.attach(MIMEText("""
Hello,
Welcome to NDHU CSIEplus!
Your token is: """ + token + """,
This token is needed to change the password, please keep it safe.
            """))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            try:
                server.ehlo()
                server.login("ndhucsieplus@gmail.com", "xhheytxfagcimsqa")
                server.send_message(content)
                print("email send to: ", str(email))
            except Exception as e:
                print(e)

    def change_password_user_check(self, connection, username, token):
        try:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM `users` WHERE `username` = %s AND `token` = %s"
                cursor.execute(sql, (username, token))
                result = cursor.fetchone()
                print(result)
                if result is not None:
                    print("change_password_user_check TRUE")
                    return "True"
                else:
                    print("change_password_user_check DNE")
                    return "DNE"
        except Exception as e:
            print(e)
            return "False"

    def update_password(self, connection, username, password):
        try:
            with connection.cursor() as cursor:
                sql = "UPDATE `users` SET password = %s WHERE username = %s"
                cursor.execute(sql, (password, username))
                connection.commit()
                return "True"
        except Exception as e:
            print(e)
            return "False"
