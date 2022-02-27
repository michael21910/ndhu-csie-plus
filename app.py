from flask import Flask, render_template

app = Flask(__name__, template_folder = 'templates')

@app.route("/")
def index():
    return render_template("index.html", question_list = ["hello world 1", "hello world 2"])

if __name__ == '__main__':
    app.run(debug = False, port = 1234)