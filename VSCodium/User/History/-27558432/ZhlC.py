from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_garanhuns' # Necessário para sessões
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///garanhuns.db' # Banco de dados local
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MODELOS (O Banco de Dados) ---

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False) # 'cliente' ou 'profissional'
    
    # Dados específicos do profissional
    profissao = db.Column(db.String(50), nullable=True) # Ex: Encanador
    bairro = db.Column(db.String(50), nullable=True) # Ex: Magano, Boa Vista
    whatsapp = db.Column(db.String(20), nullable=True)
    descricao = db.Column(db.Text, nullable=True)

# --- ROTAS (As páginas do site) ---

@app.route('/')
def index():
    # Na home, mostramos os últimos profissionais cadastrados
    profissionais = Usuario.query.filter_by(tipo='profissional').all()
    return render_template('index.html', profissionais=profissionais)

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        # Pega dados do formulário
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        tipo = request.form['tipo']
        
        # Cria novo usuário
        novo_usuario = Usuario(nome=nome, email=email, senha=senha, tipo=tipo)
        
        # Se for profissional, adiciona os dados extras
        if tipo == 'profissional':
            novo_usuario.profissao = request.form['profissao']
            novo_usuario.bairro = request.form['bairro']
            novo_usuario.whatsapp = request.form['whatsapp']
            novo_usuario.descricao = request.form['descricao']
            
        db.session.add(novo_usuario)
        db.session.commit()
        return redirect(url_for('index'))
        
    return render_template('cadastro.html')

# Cria o banco de dados na primeira execução
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)