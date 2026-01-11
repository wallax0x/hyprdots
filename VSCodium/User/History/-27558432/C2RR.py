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

# --- MODELOS (O Banco de Dados) ---

class Usuario(db.Model, UserMixin):
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
            nome = request.form['nome']
            email = request.form['email']
            senha = request.form['senha']
            tipo = request.form['tipo']
            
            # Verifica se email já existe
            if Usuario.query.filter_by(email=email).first():
                flash('Este email já está cadastrado!', 'danger')
                return redirect(url_for('cadastro'))
            
            novo_usuario = Usuario(nome=nome, email=email, senha=senha, tipo=tipo)
            
            if tipo == 'profissional':
                novo_usuario.profissao = request.form['profissao']
                novo_usuario.bairro = request.form['bairro']
                novo_usuario.whatsapp = request.form['whatsapp']
                novo_usuario.descricao = request.form['descricao']
                
            db.session.add(novo_usuario)
            db.session.commit()
            
            flash('Cadastro realizado com sucesso! Faça login ou procure seu perfil.', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'Erro ao cadastrar: {str(e)}', 'danger')
            return redirect(url_for('cadastro'))
            
    return render_template('cadastro.html')

# Cria o banco de dados na primeira execução
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)