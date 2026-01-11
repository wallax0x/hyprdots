from flask import Flask, render_template, url_for, redirect, request
import sqlite3
import base64
from flask_bcrypt import Bcrypt
app = Flask(__name__)
bcrypt = Bcrypt(app)

def conexao():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    return render_template('index.html')

@app.route("/admin")
def dashboard():
    conn = conexao()
    
    # Busca a contagem de produtos
    total_produtos = conn.execute('SELECT COUNT(id) FROM produto').fetchone()[0]
    
    # Busca a contagem de categorias
    total_categorias = conn.execute('SELECT COUNT(id) FROM categoria').fetchone()[0]
    
    conn.close()
    
    # Envia as variáveis para o template
    return render_template('admin/dashboard.html',
                            total_produtos=total_produtos,
                            total_categorias=total_categorias)
@app.route("/listarcategoria")
def listarCategoria():
    conn = conexao()
    categoria = conn.execute('select * from categoria')
    return render_template('admin/listar_categoria.html',
                           categorias = categoria )


@app.route("/cadastrarcategoria", methods=['GET','POST'])
def cadastrarCategoria():
    if request.method == 'POST':
        nome_categoria = request.form.get('nome_categoria')
        descricao = request.form.get('descricao')
        ativo = request.form.get('ativo')
        imagem = request.files.get('imagem')              
        imagem_base64 = base64.b64encode(imagem.read()).decode('utf-8')
        if nome_categoria:
            conn = conexao()
            conn.execute('INSERT INTO categoria (nome, descricao, ativo, imagem ) VALUES (?, ?, ?, ?)',
                (nome_categoria, descricao, ativo, imagem_base64))            
            conn.commit()
            conn.close()
            return redirect(url_for('listarCategoria'))        
    return render_template('admin/cadastrar_categoria.html')
    
    
@app.route("/editarcategoria/<int:id>", methods=['GET','POST'])
def editarCategoria(id):
    conn = conexao()
    categoria = conn.execute('select * from categoria where id=?', (id,)).fetchone()
    if request.method == 'POST':
        nome_categoria = request.form.get('nome_categoria')
        descricao = request.form.get('descricao')
        ativo = request.form.get('ativo')
        imagem = request.files.get('imagem')              
        imagem_base64 = base64.b64encode(imagem.read()).decode('utf-8')
        if nome_categoria:
            conn = conexao()
            if imagem:
                conn.execute('UPDATE categoria SET nome=?, descricao=?, ativo=?, imagem=? WHERE id=?',   
                (nome_categoria, descricao, ativo, imagem_base64, id,))           
            else:
                conn.execute('UPDATE categoria SET nome=?, descricao=?, ativo=? WHERE id=?',   
                (nome_categoria, descricao, ativo, id,)) 

            conn.commit()
            conn.close()
            return redirect(url_for('listarCategoria'))

    return render_template('admin/editar_categoria.html',
                            categoria=categoria )

# Rota para excluir categoria
@app.route("/excluir_categoria/<int:id>", methods=['GET', 'POST'])
def excluirCategoria(id):
    conn = conexao()
    categoria = conn.execute('SELECT * FROM categoria WHERE id = ?', (id,)).fetchone()
    
    if request.method == 'POST':
        conn.execute('DELETE FROM categoria WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return redirect(url_for('listarCategoria'))    
    conn.close()
    return render_template('admin/excluir_categoria.html', categoria = categoria )


# INÍCIO da Rota de PRODUTO


# Rota para CADASTRAR Produto
@app.route("/cadastrarproduto", methods=['GET','POST'])
def cadastrarProduto():
    conn = conexao()
    
    if request.method == 'POST':
        # Pega os dados do formulário
        nome_produto = request.form.get('nome_produto')
        preco = request.form.get('preco')
        ativo = request.form.get('ativo')
        id_categoria = request.form.get('id_categoria') # Baseado no seu schema.sql
        imagem = request.files.get('imagem')              
        
        imagem_base64 = ""
        if imagem:
            imagem_base64 = base64.b64encode(imagem.read()).decode('utf-8')
        
        if nome_produto and preco and id_categoria:
            # Insere na tabela 'produto'
            conn.execute('INSERT INTO produto (nome, preco, ativo, imagem, id_categoria) VALUES (?, ?, ?, ?, ?)',
                (nome_produto, preco, ativo, imagem_base64, id_categoria))            
            conn.commit()
            conn.close()
            return redirect(url_for('listarProdutos')) # Redireciona para a lista
    
    # Se for GET, busca as categorias para o formulário
    # (Usando 'True' como string, igual ao seu schema de exemplo)
    categorias = conn.execute('SELECT * FROM categoria').fetchall()
    conn.close()
    return render_template('admin/cadastrar_produto.html', categorias=categorias)

#removi WHERE ativo = "True"

# Rota para LISTAR Produtos
@app.route("/listarprodutos")
def listarProdutos():
    conn = conexao()
    # SQL(produto, categoria, id_categoria)
    # Também busca p.imagem para exibir na lista
    sql_query = """
    SELECT p.id, p.nome, p.preco, p.ativo, p.imagem, c.nome AS nome_categoria
    FROM produto p 
    JOIN categoria c ON p.id_categoria = c.id
    """
    
    produtos = conn.execute(sql_query).fetchall()
    conn.close()
    return render_template('admin/listar_produtos.html',
                           produtos = produtos )


# FIM da Rota de PRODUTOS


# Rota para EDITAR Produto
@app.route("/editarproduto/<int:id>", methods=['GET','POST'])
def editarProduto(id):
    conn = conexao()
    
    if request.method == 'POST':
        # Pega os dados do formulário
        nome_produto = request.form.get('nome_produto')
        preco = request.form.get('preco')
        ativo = request.form.get('ativo')
        id_categoria = request.form.get('id_categoria')
        imagem = request.files.get('imagem')              
        
        if nome_produto and preco and id_categoria:
            if imagem and imagem.filename:
                # Se uma nova imagem foi enviada
                imagem_base64 = base64.b64encode(imagem.read()).decode('utf-8')
                conn.execute('UPDATE produto SET nome=?, preco=?, ativo=?, imagem=?, id_categoria=? WHERE id=?',   
                    (nome_produto, preco, ativo, imagem_base64, id_categoria, id))           
            else:
                # Se nenhuma imagem nova foi enviada
                conn.execute('UPDATE produto SET nome=?, preco=?, ativo=?, id_categoria=? WHERE id=?',   
                    (nome_produto, preco, ativo, id_categoria, id)) 

            conn.commit()
            conn.close()
            return redirect(url_for('listarProdutos'))

    # Se for GET:
    # 1. Busca o produto específico

    produto = conn.execute('SELECT * FROM produto WHERE id = ?', (id,)).fetchone()
    # 2. Busca TODAS as categorias para o dropdown

    categorias = conn.execute('SELECT * FROM categoria').fetchall()
    conn.close()
    
    return render_template('admin/editar_produto.html',
                            produto=produto, categorias=categorias )

# Rota para EXCLUIR Produto (com confirmação)
@app.route("/excluir_produto/<int:id>", methods=['GET', 'POST'])
def excluirProduto(id):
    conn = conexao()
    produto = conn.execute('SELECT * FROM produto WHERE id = ?', (id,)).fetchone()
    
    if request.method == 'POST':
        # Se o formulário foi enviado, exclui
        conn.execute('DELETE FROM produto WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return redirect(url_for('listarProdutos'))    
    
    # Se for GET, mostra a página de confirmação.
    conn.close()
    return render_template('admin/excluir_produto.html', produto = produto )

# Rota para DETALHES da Categoria
@app.route("/detalhes_categoria/<int:id>")
def detalhesCategoria(id):
    conn = conexao()
    
    # Busca a categoria específica
    categoria = conn.execute('SELECT * FROM categoria WHERE id = ?', (id,)).fetchone()
    
    # Busca todos os produtos que pertencem a esta categoria
    produtos = conn.execute('SELECT * FROM produto WHERE id_categoria = ?', (id,)).fetchall()
    
    conn.close()
    
    if not categoria:
        return redirect(url_for('listarCategoria'))
        
    return render_template('admin/detalhes_categoria.html',
                            categoria = categoria,
                            produtos = produtos )
# Rota para DETALHES do Produto
@app.route("/detalhesproduto/<int:id>")
def detalhesProduto(id):
    conn = conexao()
    
    # JOIN para pegar o produto E o nome da sua categoria
    sql_query = """
    SELECT p.*, c.nome AS nome_categoria, c.descricao AS descricao_categoria
    FROM produto p
    LEFT JOIN categoria c ON p.id_categoria = c.id
    WHERE p.id = ?
    """
    
    produto = conn.execute(sql_query, (id,)).fetchone()
    conn.close()
    
    # Se o produto não for encontrado, volta para a lista

    if not produto:
        return redirect(url_for('listarProdutos'))
        
    return render_template('admin/detalhes_produto.html',
                            produto = produto )

@app.route("/listarusuario")
def listarUsuario():
    conn = conexao()
    # Seleciona todos os usuários para listar
    # É uma boa prática não selecionar a senha, mas vamos pegar tudo por simplicidade
    usuarios = conn.execute('SELECT * FROM usuario').fetchall()
    conn.close()
    
    # Envia a lista de usuários para o template
    return render_template('admin/listar_usuario.html',
                           usuarios = usuarios )
@app.route("/login")
def login():
    return render_template('admin/login.html')

@app.route("/cadastrarusuario", methods=['GET','POST'])
def cadastrarUsuario():
    if request.method == 'POST':
        nome = request.form.get('nome')
        senha = request.form.get('senha')
        ativo = request.form.get('ativo') 
        
        # Garante que os campos não estão vazios
        if nome and senha and ativo:
            # variável é 'senha_criptografada'
            senha_criptografada = bcrypt.generate_password_hash(senha).decode('utf-8')
            
            conn = conexao()
            # Adicionado o campo 'ativo' no INSERT
            conn.execute('INSERT INTO usuario (nome, senha, ativo) VALUES (?, ?, ?)',
                (nome, senha_criptografada, ativo))            
            conn.commit()
            conn.close()
            # Redireciona para a lista de usuários (precisa ser criada)
            return redirect(url_for('listarUsuario'))
            
    return render_template('admin/cadastrar_usuario.html')
@app.route("/editarusuario/<int:id>", methods=['GET','POST'])
def editarUsuario(id):
    conn = conexao()
    usuario = conn.execute('select * from usuario where id=?', (id,)).fetchone()
    if request.method == 'POST':
        nome = request.form.get('nome')
        senha = request.form.get('senha')
        senha_cript = bcrypt.generate_password_hash(senha).decode('utf-8')
        if nome:
            conn.execute('UPDATE usuario SET nome=?, senha=? WHERE id=?',
            (nome, senha_cript, id,)) 
            
            conn.commit()
            conn.close()
            return redirect(url_for('listarUsuario'))

    return render_template('admin/editar_usuario.html',
                            usuario=usuario )


@app.route("/excluir_usuario/<int:id>", methods=['GET', 'POST'])
def excluirUsuario(id):
    conn = conexao()
    categoria = conn.execute('SELECT * FROM usuario WHERE id = ?', (id,)).fetchone()
    
    if request.method == 'POST':
        conn.execute('DELETE FROM usuario WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return redirect(url_for('listarUsuario'))    
    conn.close()
    return render_template('admin/excluir_usuario.html', usuario = usuario )



app.run(debug=True)