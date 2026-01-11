import sqlite3

print('gg')
def init_db():
    conn = sqlite3.connect("database.db")
    with open("schemas.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("BANCO DE DADOS INICIADO COM SUCESSO")
    
init_db()