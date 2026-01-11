DROP TABLE IF EXISTS produto;
DROP TABLE IF EXISTS categoria;


CREATE TABLE categoria(
   id integer primary key autoincrement,
   nome varchar(100),
   descricao text,
   ativo boolean,
   imagem blob,
   img varchar
);

CREATE TABLE produto(
   id integer primary key autoincrement,
   nome varchar(50),
   preco float,
   ativo boolean,
   imagem blob,
   img varchar,
   id_categoria int
   forengn key ('id_categoria') references categoria('id')

);

