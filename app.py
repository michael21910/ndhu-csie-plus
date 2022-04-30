from flask import Flask, render_template, session, request, redirect, url_for
from flask_session import Session
from databaseUtils import databaseUtils
import comsci as cs
import os
from bert_utils import SentenceCleanser, translate

app = Flask(__name__, template_folder = "templates")

# connecting to database
db = databaseUtils(
    os.environ.get('CLEARDB_DATABASE_HOST'),
    os.environ.get('CLEARDB_DATABASE_USER'),
    os.environ.get('CLEARDB_DATABASE_PASSWORD'),
    os.environ.get('CLEARDB_DATABASE_DB')
)

connection = db.connect(
    os.environ.get('CLEARDB_DATABASE_HOST'),
    os.environ.get('CLEARDB_DATABASE_USER'),
    os.environ.get('CLEARDB_DATABASE_PASSWORD'),
    os.environ.get('CLEARDB_DATABASE_DB')
)

app.secret_key = "super secret key"
app.config["SESSION_TYPE"] = "filesystem"

__session = Session(app)

# global variable
tags_list = ["General", "Freshman", "Sophomore", "Junior", "Multimedia", "Network"]

def get_tag_tuple(request_values):
    tags_tuple = tuple(  (tag in request_values) * "checked" for tag in tags_list  )
    return tags_tuple

"""
    Error Code:
        (1) -1 => internal error (MySQL)
        (2)  1 => success
        (3)  2 => login warning 
        (4)  3 => blank field warning
        (5)  4 => not related to CSIE
        (6)  5 => tag not selected
        (7)  6 => sensitive words detected
        (8)  7 => translation error
"""

sentence_cleanser = SentenceCleanser()

# SGET stands for "session get"
def SGET(value, default):
    return default if (value == None) else value

@app.route("/", methods = ["GET", "POST"])
def index():
    # fetch all questions
    question_list = SGET(session.get("search_result"), db.get_index_contents(connection))
    session["search_result"] = None

    # fetch search bar contents
    search_bar_default_value = SGET(session.get("search_bar_default_value"), "")
    session["search_bar_default_value"] = None

    # fetch number of questions according to the search bar
    search_count_message = SGET(session.get("search_count_message"), "")
    session["search_count_message"] = None
    
    # after user login
    if request.method == "POST":
        # fetch user username and password
        username = request.values["username"]
        password = request.values["password"]
        
        # if the user exists (the user input is correct)
        if db.login_user_check(connection, username, password) == "True":
            # stores the username in session
            session["username"] = username
            # get the last page before logging in
            previous_page = SGET(session.get("previous_page"), "/")
            # set previous_page to None
            session["previous_page"] = None
            # redirect to the last page before logging in
            return redirect(previous_page)

        # if the user does not exist (the user input is incorrect)
        elif db.login_user_check(connection, username, password) == "DNE":
            # set login warning message
            session["login_default_message"] = "Username or password is incorrect."
            return redirect(url_for("login"))
        
        # if there is an internal error (MySQL)
        elif db.login_user_check(connection, username, password) == "False":
            return redirect(url_for("FOF"))
    
    # general case
    else:
        return render_template("index.html", 
            question_list = SGET(question_list, []), 
            username = SGET(session.get("username"), ""),
            search_bar_default_value = search_bar_default_value,
            search_count_message = search_count_message
        )
    
@app.route("/logout")
def log_out():
    # when the user logs out, clear the username in the session
    session["username"] = None
    return redirect(url_for("index"))

@app.route("/ask_question")
def ask_question():
    # fetch all the informations from the ask question page
    title_default_value          = SGET(session.get("title_default_value"),                        "")
    content_default_value        = SGET(session.get("content_default_value"),                      "")
    anonymous_checked            = SGET(session.get("anonymous_checked"),                          "")
    default_message              = SGET(session.get("default_message"),                            "")
    ask_question_default_message = SGET(session.get("ask_question_default_message"),               "")
    tags_tuple                   = SGET(session.get("tags_tuple"), tuple([ 0 ] * tags_list.__len__()))
    
    # set all the session variables to None
    session["title_default_value"]          = None
    session["content_default_value"]        = None
    session["anonymous_checked"]            = None
    session["default_message"]              = None
    session["ask_question_default_message"] = None
    session["tags_tuple"]                   = None
    
    return render_template("ask.html", 
        username = SGET(session.get("username"), ""),
        title_default_value   = title_default_value, 
        content_default_value = content_default_value,
        anonymous_checked     = anonymous_checked,
        message               = default_message,
        tagMessage            = ask_question_default_message,
        tags_tuple            = tags_tuple
    )

@app.route("/search", methods = [ "GET", "POST" ])
def search_question():
    # get the search bar contents
    search_string = request.values["search_bar"]

    # fetch question list in the search result
    question_list = databaseUtils.filter_contents(db.get_index_contents(connection), search_string)

    if (question_list == -1):
        session["search_result"] = session["search_count_message"] = None
    else:
        session["search_result"] = question_list
        session["search_count_message"] = "Found {} results".format(len(question_list))
    session["search_bar_default_value"] = search_string
    return redirect(url_for("index"))

@app.route("/leaderboard", methods = [ "GET", "POST" ])
def leaderboard():
    # fetch username
    username = SGET(session.get("username"), "")
    # fetch leaderboard
    user_contents = db.get_leaderboard(connection)
    
    # sort user_contents by their points in descending order
    if (user_contents != None):
        user_contents.sort()
        user_contents.reverse()
    else:
        user_contents = ""
    
    return render_template("leaderboard.html", username = username, user_contents = user_contents)

@app.route("/post_question", methods = [ "GET", "POST" ])
def post_question():
    # fetch the question, content, and asker's username
    question_dict = {
        "question"  : request.values["question-title"],
        "content"   : request.values["question-content"],
        "asker"     : SGET(session.get("username"), ""),
        "tags_tuple" : get_tag_tuple(request.values)
    }
    
    # store the username for points subtraction
    asker_username = question_dict["asker"]

    # if the question title is empty, set err to 3
    if (question_dict["question"] == ""): 
        err = 3
    # if the user hasn't logged in, set err to 2
    elif (session.get("username") == None): 
        err = 2
    # if the question title is not empty and the user has logged in, set err to 1 or -1 according to the MySql connection result
    else:
        # determine the content or the title is realted to CSIE
        user_question_merged = question_dict['question'] + " " + question_dict['content']
        print("\n\nMERGED: {}\n\n".format(user_question_merged))        
        user_question_translated, translate_success = translate(user_question_merged) 
        user_question_cleansed   = sentence_cleanser.cleanse(user_question_translated)        
        print("\n\nCLEANSED: {}\n\n".format(user_question_cleansed))        
        if not (translate_success):            
            print("\n\nCOULD NOT TRANSLATE SENTENCE\n\n")            
            err = 7        
        elif (user_question_cleansed[1]):            
            print("\n\nDETECTED SENSITIVE WORDS\n\n")            
            err = 6            
        else:            
            user_question_formatted = user_question_cleansed[0]
            print("\n\nFORMATTED: {}\n\n".format(user_question_formatted))
            err = 4            
            if (user_question_formatted.__len__()):                
                user_question_rejoined = " ".join(user_question_formatted)                
                print("\n\nREJOINED: {}\n\n".format(user_question_rejoined))                
                user_question_vectorized = cs.preprocess_vectorize_without_translate(user_question_rejoined)                
                print("\n\nVECTORIZED SHAPE: {}\n\n".format(user_question_vectorized.shape))
                relation_score = float(cs.get_relation_score(user_question_vectorized)) * 100                
                print("\n\nPREDICTED SCORE: {:.4f}%\n\n".format(relation_score))                
                if (relation_score >= 50):
                    request_set = set(request.values.keys())
                    tags_count  = sum(  (tag in request_set)  for tag in tags_list  )
                    target_tag  = (  list(  set(tags_list).intersection(request_set)  ) or [ None ]  )[-1]                    
                    print("\n\nTARGET TAG: {}\n\n".format(target_tag))                    
                    if (tags_count != 1):
                        err = 5                        
                    else:
                        if ("anonymous" in request_set):
                            question_dict["asker"] = ""
                        err, qid = db.insert_question(connection, question_dict, target_tag, asker_username)

    # if err is 1, redirect to the question page that the user just posted
    if (err == 1):
        print("\n\nSUCCESS\n\n")
        redirect_to = "/question?qid={}".format(qid)
    # else, do the following
    else:
        # fetch question, content and asker's username
        session["title_default_value"]   = question_dict["question"]
        session["content_default_value"] = question_dict["content"]
        session["anonymous_checked"]     = ("checked" if (question_dict["asker"] == "") else None) 
        session["tags_tuple"] = question_dict["tags_tuple"]
        # if something went wrong about the MySQL connection
        if (err == -1):
            print("\n\nMYSQL ERROR\n\n")
            session["default_message"] = "Your request cannot be processed right now, please try again later!"
            redirect_to = url_for("ask_question")
        # if the user hasn't logged in
        elif (err == 2):
            print("\n\nUSER NOT LOGGED IN\n\n")
            session["previous_page"] = url_for("ask_question")
            session["login_default_message"] = "You must login before posting!"
            redirect_to = url_for("login")
        # if the question title is empty
        elif (err == 3):
            print("\n\nEMPTY FIELD DETECTED\n\n")
            session["default_message"] = "Question title must not be blank!"
            redirect_to = url_for("ask_question")
        elif (err == 4):
            print("\n\nUNRELATED TO CSIE\n\n")
            session["default_message"] = "Your post is not related to CSIE! Please contact us if you think this is a mistake."
            redirect_to = url_for("ask_question")
        elif (err == 5):
            print("\n\nINVALID TAG SELECTION\n\n")
            session["ask_question_default_message"] = "You can only choose 1 tag."
            redirect_to = url_for("ask_question")
        elif (err == 6):
            print("\n\nSENSITIVE WORDS DETECTED\n\n")
            session["default_message"] = "Woah! There appear to be sensitive words in your question. Please check your wording."
            redirect_to = url_for("ask_question")
        elif (err == 7):
            print("\n\nTRANSLATION ERROR\n\n")
            session["default_message"] = "The website is under maintenance. Please post in English or try again later!"
            redirect_to = url_for("ask_question")
        else:
            redirect_to = url_for("FOF")
        
    return redirect(redirect_to)

@app.route("/question", methods = ["GET"])
def redirect_question():
    # fetch the question is and contents
    question_id = int(request.args.get("qid"))
    question_contents = db.get_question_contents(connection, question_id)
    
    # fetch the username, and the replies of the question
    username = SGET(session.get("username"), "")
    reply_default_value = SGET(session.get("reply_default_value"), "")
    session["reply_default_value"] = None
    
    # set the previous page and the question page
    session["previous_page"] = "/question?qid={}".format(question_id)
    session["question_id"]   = question_id
    
    if (question_contents == None):
        return redirect(url_for("FOF"))
    else:
        return render_template("question.html", 
            username = username, 
            question_contents = question_contents,
            reply_default_value = reply_default_value,
            tag = tags_list[ question_contents["question"]["question_data"]["tag"] - 1 ]
        )

@app.route("/post_reply", methods = [ "GET", "POST" ])
def post_reply():
    # fetch the username, reply contents, question id and previous page
    username = SGET(session.get("username"), "")
    reply_contents = {
        "reply_content" : request.values["reply_entry_box"],
        "replier"       : username
    }
    previous_page = SGET(session.get("previous_page"), "/")
    reply_contents["question_id"] = SGET(session.get("question_id"), 1)
    
    # if the user typed nothing and clicked post, set err to 3
    if (reply_contents["reply_content"] == ""):
        err = 3
    # if the user hasn't logged in, set err to 2
    elif (username == ""):
        err = 2
    # if the user has logged in and typed something, set err to 1 or -1 according to the MySql connection result
    else:
        err = db.insert_reply(connection, reply_contents)
    
    # if something went wrong about the MySQL connection
    if (err == -1):
        print("\n\nMYSQL ERROR\n\n")
        redirect_to = previous_page
    # if the user posts his/her answers successfly
    elif (err == 1):
        print("\n\nSUCCESS\n\n")
        redirect_to = previous_page
    # if the user hasn't logged in
    elif (err == 2):
        print("\n\nUSER NOT LOGGED IN\n\n")
        session["reply_default_value"] = reply_contents["reply_content"]
        redirect_to = url_for("login")
    # if the user typed nothing
    elif (err == 3):
        print("\n\nBLANK FIELD DETECTED\n\n")
        redirect_to = previous_page
    else:
        redirect_to = url_for("FOF")

    return redirect(redirect_to)
    
@app.route("/upvote_question", methods = [ "GET", "POST" ])
def upvote_question():
    # fetch the username and the previous page
    username = SGET(session.get("username"), "")
    previous_page = SGET(session.get("previous_page"), "/")

    # if the user hasn't logged in, set err to 2
    if (username == ""):
        err = 2
    # if the user has logged in, set err to 1 or -1 according to the MySql connection result
    else:
        question_id = SGET(session.get("question_id"), 1)
        err = db.upvote_question(connection, question_id, username)
    
    # if something went wrong about the MySQL connection
    if (err == -1):
        print("\n\nMYSQL ERROR\n\n")
        redirect_to = previous_page
    # if the user has logged in and upvoted the question successfully
    elif (err == 1):
        print("\n\nSUCCESS\n\n")
        redirect_to = previous_page
    # if the user hasn't logged in
    elif (err == 2):
        print("\n\nUSER NOT LOGGED IN\n\n")
        redirect_to = url_for("login")
    else:
        redirect_to = url_for("FOF")
    
    return redirect(redirect_to)
    

@app.route("/login")
def login():
    # fetch login message
    login_default_message = SGET(session.get("login_default_message"), "")
    session["login_default_message"] = None
    return render_template("login.html", message = login_default_message)

@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "POST":
        # fetch the username, password, and email
        username = request.values["username"]
        email = request.values["email"] + "@gms.ndhu.edu.tw"
        password = request.values["password"]
        repeatPassword = request.values["repeat-password"]

        # if the user leave at least 1 field blank
        if username == "" or email == "" or password == "" or repeatPassword == "":
            session["register_default_message"] = "Please fill in all fields."
            return redirect(url_for("register"))
        else:
            # if the user already exists
            if db.check_username_exists(connection, username) == "True":
                session["register_default_message"] = "Username already exists."
                return redirect(url_for("register"))
            # if the user doesn't exist
            elif db.check_username_exists(connection, username) == "DNE":
                # if the password and repeat password are the same, insert the user into the database
                if password == repeatPassword:
                    db.add_user(connection, username, email, password)
                    session["login_default_message"] = "You have successfully registered."
                    return redirect(url_for("login"))
                # if the password and repeat password are not the same
                else:
                    session["register_default_message"] = "Passwords are not the same."
                    return redirect(url_for("register"))
            # if MySql error
            elif db.check_username_exists(connection, username) == "False":
                return redirect(url_for("FOF"))
    register_default_message = SGET(session.get("register_default_message"), "")
    session["register_default_message"] = None
    return render_template("register.html", message = register_default_message)

@app.route("/forgotpassword", methods = ["GET", "POST"])
def forgotpassword():
    if request.method == "POST":
        # fetch the username, email and token
        username = request.values["username"]
        token = request.values["token"]
        newPassword = request.values["new-password"]
        repeatNewPassword = request.values["repeat-new-password"]

        # if the user leave at least 1 field blank
        if username == "" or token == "" or newPassword == "" or repeatNewPassword == "":
            session["forgotpassword_default_message"] = "Please fill in all fields."
            return redirect(url_for("forgotpassword"))
        else:
            # if the user input is all correct
            if db.change_password_user_check(connection, username, token) == "True":
                # if the new password and repeat new password are the same
                if newPassword == repeatNewPassword:
                    user_previous_password = db.get_user_info(connection, username)[2]
                    if user_previous_password == newPassword:
                        session["login_default_message"] = "Your new password is the same as your previous password."
                        return redirect(url_for("login"))
                    db.update_password(connection, username, newPassword)
                    session["login_default_message"] = "You have successfully changed your password."
                    return redirect(url_for("login"))
                else:
                    session["forgotpassword_default_message"] = "Passwords are not the same."
                    return redirect(url_for("forgotpassword"))
            elif db.change_password_user_check(connection, username, token) == "DNE":
                session["forgotpassword_default_message"] = "Username or token is incorrect."
                return redirect(url_for("forgotpassword"))
            elif db.change_password_user_check(connection, username, token) == "False":
                return redirect(url_for("FOF"))
    forgotpassword_default_message = SGET(session.get("forgotpassword_default_message"), "")
    session["forgotpassword_default_message"] = None
    return render_template("forgotpassword.html", message = forgotpassword_default_message)

@app.route('/profile')
def profile():
    # get the username and the previous page
    username = SGET(session.get("username"), "")

    # if the user hasn't logged in, redirect to login page
    if username == "":
        session["login_default_message"] = "Please login to view your profile."
        return redirect(url_for("login"))
    else:
        username, email, password, points, posts, answers = db.get_user_info(connection, username)
        return render_template("profile.html",
            username = username,
            email = email,
            password = len(password) * "*",
            points = points, 
            posts = posts,
            answers = answers
        )

@app.route("/404")
def FOF():
    return render_template("404.html")

@app.route("/rules")
def rules():
    username = SGET(session.get("username"), "")
    return render_template("rules.html", username = username)

@app.route("/about")
def about():
    username = SGET(session.get("username"), "")
    return render_template("about.html", username = username)

@app.errorhandler(404)
def error_handler(_):
    return redirect(url_for("FOF"))

if __name__ == "__main__":
    app.run(debug = False)