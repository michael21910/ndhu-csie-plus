from flask import Flask, render_template, jsonify, session, request, redirect, url_for
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

app.secret_key = "super secret key"
app.config["SESSION_TYPE"] = "filesystem"

def SGET(value, default):
    return default if (value == None) else value

@app.route("/", methods = ["GET", "POST"])
def index():
    
    question_list = db.get_index_contents(connection)
    
    if request.method == "POST":
        print(request.values)
        
        username = request.values["username"]
        password = request.values["password"]
        
        if db.login_user_check(connection, username, password) == "True":
            print("username:", username)
            session["username"] = username
            
            previous_page = SGET(session.get("previous_page"), "index")
            
            session["previous_page"] = None
            
            return redirect(previous_page)

        elif db.login_user_check(connection, username, password) == "DNE":
            return render_template("login.html", 
                message = "Username or password is incorrect.")
        
        elif db.login_user_check(connection, username, password) == "False":
            return redirect(url_for("FOF"))
        
    else:
        return render_template("index.html", 
            question_list = SGET(question_list, []), 
            username = SGET(session.get("username"), "")
        )
    
@app.route("/logout")
def log_out():
    session["username"] = None
    return redirect(url_for("index"))

@app.route("/ask_question")
def ask_question():
    title_default_value   = SGET(session.get("title_default_value"),   "")
    content_default_value = SGET(session.get("content_default_value"), "")
    anonymous_checked     = SGET(session.get("anonymous_checked"),     "")
    default_message       = SGET(session.get("default_message"),       "")
    
    session["title_default_value"]   = None
    session["content_default_value"] = None
    session["anonymous_checked"]     = None
    session["default_message"]       = None
    
    return render_template("ask.html", 
        username = SGET(session.get("username"), ""),
        title_default_value   = title_default_value, 
        content_default_value = content_default_value,
        anonymous_checked     = anonymous_checked,
        message               = default_message
    )

@app.route("/post_question", methods = [ "GET", "POST" ])
def post_question():
    
    question_dict = {
        "question"  : request.values["question-title"],
        "content"   : request.values["question-content"],
        "asker"     : SGET(session.get("username"), "")
    }
    
    print(question_dict)
    if (question_dict["question"] == ""):
        err = 3
    elif (session.get("username") == None):
        err = 2
    else:
        print(request.values)
        print(question_dict["question"] == "")
        if ("anonymous" in list(request.values.keys())):
            question_dict["asker"] = ""
        err = db.insert_question(connection, question_dict)
    print(err)
    if (err == 1):
        print("success")
        return redirect(url_for("index"))
    elif (err == -1):
        print("fail")
        return redirect(url_for("FOF"))
    elif (err == 2):
        print("login")
        session["previous_page"]         = url_for("ask_question")
        session["title_default_value"]   = question_dict["question"]
        session["content_default_value"] = question_dict["content"]
        session["anonymous_checked"]     = ("checked" if (question_dict["asker"] == "") else None) 
        return redirect(url_for("login"))
    elif (err == 3):
        print("empty")
        session["title_default_value"]   = question_dict["question"]
        session["content_default_value"] = question_dict["content"]
        session["anonymous_checked"]     = ("checked" if (question_dict["asker"] == "") else None) 
        session["default_message"]       = "Question title must not be blank!"
        return redirect(url_for("ask_question"))

@app.route("/question", methods = ["GET"])
def redirect_question():
    question_id = int(request.args.get("qid"))
    question_contents = db.get_question_contents(connection, question_id)
    
    username = SGET(session.get("username"), "")
    reply_default_value = SGET(session.get("reply_default_value"), "")
    session["reply_default_value"] = None
    
    session["previous_page"] = "/question?qid={}".format(question_id)
    
    if (question_contents == None):
        return redirect(url_for("FOF"))
    else:
        return render_template("question.html", 
            username = username, 
            question_contents = question_contents,
            reply_default_value = reply_default_value
        )

@app.route("/post_reply", methods = [ "GET", "POST" ])
def post_reply():
    
    username = SGET(session.get("username"), "")
    
    reply_contents = {
        "reply_content" : request.values["reply_entry_box"],
        "replier"       : username
    }
    
    previous_page = SGET(session.get("previous_page"), "/")
    
    reply_contents["question_id"] = int(previous_page[14:])
    
    #session["previous_page"] = None
    print(previous_page)
    if (reply_contents["reply_content"] == ""):
        return redirect(previous_page)
    elif (username == ""):
        session["reply_default_value"] = reply_contents["reply_content"]
        return redirect(url_for("login"))
    else:
        err = db.insert_reply(connection, reply_contents)
        print(err)
        return redirect(previous_page)

@app.route("/upvote_question", methods = ["POST"])
def upvote_question():
    
    username = SGET(session.get("username"), "")
    previous_page = SGET(session.get("previous_page"), "/")
    
    if (username == ""):
        err = 2
    else:
        question_id = int(previous_page[14:])
        err = db.upvote_question(connection, question_id, username)
        print(err)
    return jsonify({ "error_code" : previous_page } if (err == 1) else { "error_code" : url_for("FOF") } if (err == -1) else { "error_code" : "login" })

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
