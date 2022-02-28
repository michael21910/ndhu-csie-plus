import pymysql.cursors
import copy
import string
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

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
            return "False"
    
    def format_question_list(question_list):
        modified_question_list = copy.deepcopy(question_list)
        for qid, question in enumerate(question_list):
            del modified_question_list[qid]["id"]
            for key, val in question.items():
                if key == "replies":
                    modified_question_list[qid][key] = \
                        "{} {}".format(val, ("replies" if (val != 1) else "reply"))
                elif key == "time":
                    modified_question_list[qid][key] = \
                        val.strftime("%Y/%m/%d")
                elif key == "id":
                    modified_question_list[qid][key] = \
                        "question-{}".format(val)
        return modified_question_list

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
