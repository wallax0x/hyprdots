import sqlite3

def init_db():
    conn = sqlite3.connect("database.db")
    with open("squemas.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("BANCO DE DADOS INICIADO COM SUCESSO")
    