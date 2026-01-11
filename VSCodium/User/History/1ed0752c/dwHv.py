from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/admin")
def dashboard():
        return render_template("admin/dashboard.html") 
s
app.run(debug=True)