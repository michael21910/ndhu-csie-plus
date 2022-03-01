from flask import Flask, render_template, jsonify, request, redirect, url_for
from databaseUtils import databaseUtils

app = Flask(__name__, template_folder = "templates")

db = databaseUtils(
    "127.0.0.1",
    "root",
    "",
    "csieplus"
)

connection = db.connect(
    "127.0.0.1",
    "root",
    "",
    "csieplus"
)

username  = ""

@app.route("/", methods = ["GET", "POST"])
def index():
    global question_list
    global username
    global password
    question_list = db.get_index_contents(connection)
    if request.method == "POST":
        _username = request.values["username"]
        _password = request.values["password"]
        if db.login_user_check(connection, _username, _password) == "True":
            print("username:", _username)
            #return render_template("index.html", question_list = question_list, username = username)
            username  = _username
            return render_template("index.html", question_list = ([] if (question_list == None) else question_list), username = username)

        elif db.login_user_check(connection, _username, _password) == "DNE":
            return render_template("login.html", message = "Username or password is incorrect.")
        elif db.login_user_check(connection, _username, _password) == "False":
            return redirect(url_for("FOF"))
    else:
        #return render_template("index.html", question_list = question_list, username = "")
        return render_template("index.html", question_list = ([] if (question_list == None) else question_list), username = username)

@app.route("/logout")
def log_out():
    global username
    username = ""
    return redirect(url_for("index"))

@app.route("/ask_question")
def ask_question():
    return render_template("ask.html", username = username)

@app.route("/post_question", methods = ["POST"])
def post_question():

    if (username == ""):
        err = 2
    else:
        question_dict = request.get_json()
        question_dict["asker"] = ("" if (question_dict["anonymous"]) else username)
        err = db.insert_question(connection, question_dict)

    return jsonify({ "error_code" : "success" } if (err == 1) else { "error_code" : "failure" } if (err == -1) else { "error_code" : "please login first" })

@app.route("/question", methods = ["GET"])
def redirect_question():
    question_id = int(request.args.get("qid"))
    question_contents = db.get_question_contents(connection, question_id)
    if (question_contents == None):
        return redirect(url_for("FOF"))
    else:
        return render_template("question.html", username = username, question_contents = question_contents)

@app.route("/post_reply", methods = ["POST"])
def post_reply():
    if (username == ""):
        err = 2
    else:
        reply_contents = request.get_json()
        reply_contents["replier"] = username
        err = db.insert_reply(connection, reply_contents)
    return jsonify({ "error_code" : "success" } if (err == 1) else { "error_code" : "failure" } if (err == -1) else { "error_code" : "please login first" })

@app.route("/upvote_question", methods = ["POST"])
def upvote_question():
    if (username == ""):
        err = 2
    else:
        contents = request.get_json()
        err = db.upvote_question(connection, contents["question_id"], username)
    return jsonify({ "error_code" : "success" } if (err == 1) else { "error_code" : "failure" } if (err == -1) else { "error_code" : "please login first" })

@app.route("/login")
def login():
    return render_template("login.html", message = "")

@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.values["username"]
        email = request.values["email"]
        password = request.values["password"]
        repeatPassword = request.values["repeat-password"]
        if username == "" or email == "" or password == "" or repeatPassword == "":
            return render_template("register.html", message = "Please fill in all fields.")
        else:
            if db.check_username_exists(connection, username) == "True":
                render_template("register.html", message = "Username already exists.")
            elif db.check_username_exists(connection, username) == "DNE":
                if password == repeatPassword:
                    db.add_user(connection, username, email, password)
                    return render_template("login.html", message = "You have successfully registered.")
                else:
                    return render_template("register.html", message = "Password is not the same.")
            elif db.check_username_exists(connection, username) == "False":
                return redirect(url_for("FOF"))
    return render_template("register.html", message = "")

@app.route("/forgotpassword", methods = ["GET", "POST"])
def forgotpassword():
    if request.method == "POST":
        print("POSTTTTT")
        username = request.values["username"]
        token = request.values["token"]
        newPassword = request.values["new-password"]
        repeatNewPassword = request.values["repeat-new-password"]
        print(username, token, newPassword, repeatNewPassword)
        if username == "" or token == "" or newPassword == "" or repeatNewPassword == "":
            return render_template("forgotpassword.html", message = "Please fill in all fields.")
        else:
            if db.change_password_user_check(connection, username, token) == "True":
                if newPassword == repeatNewPassword:
                    db.update_password(connection, username, newPassword)
                    return render_template("login.html", message = "You have successfully changed your password.")
                else:
                    return render_template("forgotpassword.html", message = "Password is not the same.")
            elif db.change_password_user_check(connection, username, token) == "DNE":
                return render_template("forgotpassword.html", message = "Username or token is incorrect.")
            elif db.change_password_user_check(connection, username, token) == "False":
                return redirect(url_for("FOF"))
    return render_template("forgotpassword.html", message = "")

@app.route("/404")
def FOF():
    return render_template("404.html")

if __name__ == "__main__":
    app.run(debug = False, port = 1234)
