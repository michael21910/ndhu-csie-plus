from flask import Flask, render_template, request, redirect, url_for
from databaseUtils import databaseUtils

app = Flask(__name__, template_folder = "templates")

db = databaseUtils(
    "127.0.0.1",
    "root",
    "root",
    "csieplus"
)

connection = db.connect(
    "127.0.0.1",
    "root",
    "root",
    "csieplus"
)

@app.route("/", methods = ["GET", "POST"])
def index():
    global question_list
    global username
    global password
    question_list = db.get_index_contents(connection)
    if request.method == "POST":
        username = request.values["username"]
        password = request.values["password"]
        if db.login_user_check(connection, username, password) == "True":
            print("usename:", username)
            return render_template("index.html", question_list = question_list, username = username)
        elif db.login_user_check(connection, username, password) == "DNE":
            return render_template("login.html", message = "Username or password is incorrect.")
        elif db.login_user_check(connection, username, password) == "False":
            return redirect(url_for("FOF"))
    else:
        return render_template("index.html", question_list = question_list, username = "")

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
    app.run(debug = True, port = 5000)