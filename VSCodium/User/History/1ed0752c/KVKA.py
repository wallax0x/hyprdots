from flask import Flask, render_template, url_for
import sqlite3


app = Flask(__name__, template_folder="templates")

def conexao():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn



@app.route("/")
def index():
    return render_template('base.html')


@app.route("/admin")
def dashboard():
    return render_template("admin/dashboard.html")

@app.route("admin/listar_categoria")
def listar_categoria():
    conn = conexao()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categoria")
    categorias = cursor.fetchall()
    conn.close()
    return render_template("admin/listar_categoria.html", categorias=categorias)

app.run(debug=True)