import sqlite3

def init_db():
    try:
        print("[DEBUG] Tentando conectar ao banco de dados...")
        conn = sqlite3.connect("database.db")
        print("[DEBUG] Conexão estabelecida com sucesso.")

        print("[DEBUG] Tentando abrir o arquivo 'squemas.sql'...")
        with open("squemas.sql", "r", encoding="utf-8") as f:
            script = f.read()
            print("[DEBUG] Script SQL lido com sucesso. Tamanho:", len(script), "caracteres.")

        print("[DEBUG] Executando script SQL no banco...")
        conn.executescript(script)
        print("[DEBUG] Script executado com sucesso.")

        conn.commit()
        print("[DEBUG] Alterações confirmadas (commit realizado).")

    except Exception as e:
        print("[ERRO] Ocorreu um problema durante a inicialização do banco:", e)

    finally:
        if 'conn' in locals():
            conn.close()
            print("[DEBUG] Conexão fechada.")

    print("BANCO DE DADOS INICIADO COM SUCESSO")
