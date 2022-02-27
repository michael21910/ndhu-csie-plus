from flask import Flask, render_template
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

@app.route("/")
def index():
    question_list = db.get_index_contents(connection)
    # a test to see if the jinja if statement works
    username = "User001"
    return render_template("index.html", question_list = question_list, username = username)

if __name__ == "__main__":
    app.run(debug = False)