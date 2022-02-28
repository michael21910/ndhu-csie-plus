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

username = "user000"

@app.route("/")
def index():
    question_list = db.get_index_contents(connection)
    # a test to see if the jinja if statement works
    username = "User001"
    return render_template("index.html", question_list = question_list, username = username)

@app.route("/ask")
def ask():
    username = "User101"
    return render_template("ask.html", username = username)

@app.route("/post", methods = ["POST"])
def post_question():
    #question_list = db.get_index_contents(connection)
    #return render_template("index.html", question_list = question_list, username = "success")
    #print("\n\nreceived\n\n")
    question_dict = request.get_json()
    question_dict["asker"] = ("" if (question_dict["anonymous"]) else username)
    err = db.insert_question(connection, question_dict)
    
    #print("\n\n")
    #print(question_dict)
    #print("\n\n")
    
    return jsonify({ "error_code" : "success" } if (err == 1) else { "error_code" : "failure" })

@app.route("/question/<question_id>", methods = ["GET", "POST"])
def redirect_question(question_id):
    print(question_id)
    question_contents = db.get_question_contents(connection, question_id)
    print(question_contents)
    if (question_contents == None):
        render_template("404.html")
    else:
        return render_template("question.html", username = "hello", question_contents = question_contents)

@app.route("/post_reply", methods = ["GET", "POST"])
def post_reply():
    
    username = "User101"
    reply_contents = request.get_json()
    reply_contents["replier"] = username
    err = db.insert_reply(connection, reply_contents)
    print(reply_contents)
    return jsonify({ "error_code" : "success" } if (err == 1) else { "error_code" : "failure" })
        
if __name__ == "__main__":
    app.run(debug = False, port = 1234)