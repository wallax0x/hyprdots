from flask import Flask, render_template, url_for
import sqlite3


app = Flask(__name__, template_folder="templates")


@app.route("/")
def index():
    return render_template('base.html')


@app.route("/admin")
def dashboard():
    return render_template("admin/dashboard.html")

@app.route("/listarcategoria")
def listaCategoria():
    return render_template('admin/listar_categoria.html')

app.run(debug=True)