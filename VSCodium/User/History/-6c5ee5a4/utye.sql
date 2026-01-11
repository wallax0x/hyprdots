DROP TABLE IF EXISTS produto;
DROP TABLE IF EXISTS categoria;


CREATE TABLE categoria(
   id integer primary key autoincrement,
   nome varchar(100) not null,
   descricao text,
   ativo boolean,
   imagem blob,
   img varchar
);

CREATE TABLE produto(
   id integer primary key autoincrement,
   nome varchar(50) not null,
   preco float not null,
   ativo boolean,
   imagem blob,
   img varchar,
   id_categoria int
   foreign key ('id_categoria') references categoria('id')

);

CREATE TABLE usuario (
    id integer, primary key autoincrement,
    nome varchar(50) not null,
    senha varchar not null,
    ativo boolean,
)