from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user # <--- ADICIONE ISSO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_garanhuns' # Necessário para sessões
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///garanhuns.db' # Banco de dados local
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- USA O flask_login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Nome da função da rota de login
# ---------------------------

db = SQLAlchemy(app)

# --- MODELOS (O Banco de Dados) --- CLASSE USUARIO

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    cpf = db.Column(db.String(14), nullable=True)     # Novo
    whatsapp = db.Column(db.String(20), nullable=True) # Agora para todos

    # Dados específicos do profissional
    profissao = db.Column(db.String(50), nullable=True)
    bairro = db.Column(db.String(50), nullable=True)
    descricao = db.Column(db.Text, nullable=True)


# FUNCAO CARREGAMENTO PARA CLASSE USUARIO
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# --- ROTAS (As páginas do site) ---

# --- ROTAS ATUALIZADAS ---

@app.route('/')
def index():
    # Pega o que a pessoa digitou na busca
    termo = request.args.get('q', '') # Ex: "Pedreiro"
    filtro_bairro = request.args.get('bairro', '') # Ex: "Magano"
    
    # Começa pegando todos os profissionais
    query = Usuario.query.filter_by(tipo='profissional')
    
    # Se a pessoa digitou algo, filtra
    if termo:
        # Busca tanto no nome quanto na profissão (usando like/ilike logic)
        query = query.filter(
            (Usuario.profissao.contains(termo)) | 
            (Usuario.nome.contains(termo)) |
            (Usuario.descricao.contains(termo))
        )
    
    # Se escolheu um bairro específico
    if filtro_bairro and filtro_bairro != 'Todos':
        query = query.filter_by(bairro=filtro_bairro)
        
    profissionais = query.all()
    
    # Lista de bairros para o filtro (para não ter que escrever manual no HTML)
    bairros_garanhuns = ['Heliópolis', 'Magano', 'Boa Vista', 'Cohab 1', 'Cohab 2', 'Centro', 'Brasília', 'Aloísio Pinto']
    
    return render_template('index.html', 
                         profissionais=profissionais, 
                         bairros=bairros_garanhuns,
                         termo_atual=termo)

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        try:
            # Pega os dados comuns a todos
            nome = request.form.get('nome')
            email = request.form.get('email')
            senha = request.form.get('senha')
            cpf = request.form.get('cpf')          # Pega o CPF
            whatsapp = request.form.get('whatsapp') # Pega o Zap
            tipo = request.form.get('tipo')
            
            # Verifica email duplicado
            if Usuario.query.filter_by(email=email).first():
                flash('Email já cadastrado!', 'danger')
                return redirect(url_for('cadastro'))
            
            # Cria o usuário
            novo_usuario = Usuario(
                nome=nome, email=email, senha=senha, tipo=tipo, 
                cpf=cpf, whatsapp=whatsapp
            )
            
            # Se for profissional, pega os dados extras
            if tipo == 'profissional':
                novo_usuario.profissao = request.form.get('profissao')
                novo_usuario.bairro = request.form.get('bairro')
                novo_usuario.descricao = request.form.get('descricao')
                
            db.session.add(novo_usuario)
            db.session.commit()
            
            flash('Conta criada! Faça login.', 'success')
            return redirect(url_for('login')) # Manda pro login
            
        except Exception as e:
            flash(f'Erro: {str(e)}', 'danger')
            
    return render_template('cadastro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        # Verifica se usuário existe e a senha bate
        if usuario and usuario.senha == senha:
            login_user(usuario)
            return redirect(url_for('index'))
        else:
            flash('Login inválido. Verifique email e senha.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/perfil')
@login_required
def perfil():
    return render_template('perfil.html', nome_usuario=current_user.nome)

# Cria o banco de dados na primeira execução
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)