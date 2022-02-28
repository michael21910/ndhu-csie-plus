from flask import Flask, render_template, jsonify, request
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

username = "freak"

@app.route("/")
def index():
    question_list = db.get_index_contents(connection)
    # a test to see if the jinja if statement works
    return render_template("index.html", question_list = ([] if (question_list == None) else question_list), username = username)

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
        render_template("404.html")
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
    
if __name__ == "__main__":
    app.run(debug = False, port = 1234)