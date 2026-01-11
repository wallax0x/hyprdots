PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS produto;
DROP TABLE IF EXISTS usuario;
DROP TABLE IF EXISTS categoria;

-- Tabela de categorias
CREATE TABLE categoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    ativo INTEGER,         -- 0 ou 1 (SQLite não tem tipo boolean)
    imagem BLOB,
    img VARCHAR
);

-- Tabela de usuários
CREATE TABLE usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(50) NOT NULL,
    senha TEXT NOT NULL,
    ativo INTEGER          -- 0 ou 1
);

-- Tabela de produtos
CREATE TABLE produto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(50) NOT NULL,
    preco REAL NOT NULL,
    ativo INTEGER,
    imagem BLOB,
    img VARCHAR,
    id_categoria INTEGER,
    FOREIGN KEY (id_categoria) REFERENCES categoria(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);
