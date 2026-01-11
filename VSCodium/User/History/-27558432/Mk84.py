import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename # Importante para segurança do nome do arquivo
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_garanhuns'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///garanhuns.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- CONFIGURAÇÃO DE UPLOAD ---
UPLOAD_FOLDER = 'static/uploads' # Onde as fotos vão morar
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} # Só aceita imagem

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER# CRIPTOGRAFA A SENHA
            senha_hash = generate_password_hash(senha) # Cria o hash seguro

            # Cria o usuário USANDO O HASH, não a senha pura
            novo_usuario = Usuario(
                nome=nome, email=email, senha=senha_hash, tipo=tipo, # <--- MUDOU AQUI
                cpf=cpf, whatsapp=whatsapp
            )

# Cria a pasta se ela não existir (para evitar erros)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Por favor, faça login para acessar essa página."
login_manager.login_message_category = "info"

db = SQLAlchemy(app)

# --- MODELO ATUALIZADO ---
class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    cpf = db.Column(db.String(14), nullable=True)
    whatsapp = db.Column(db.String(20), nullable=True)
    
    # Nova coluna para a foto!
    foto_perfil = db.Column(db.String(120), default='default.png') 

    # Dados específicos do profissional
    profissao = db.Column(db.String(50), nullable=True)
    bairro = db.Column(db.String(50), nullable=True)
    descricao = db.Column(db.Text, nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# --- ROTAS ---

@app.route('/')
def index():
    termo = request.args.get('q', '')
    filtro_bairro = request.args.get('bairro', '')
    
    query = Usuario.query.filter_by(tipo='profissional')
    
    if termo:
        query = query.filter(
            (Usuario.profissao.contains(termo)) | 
            (Usuario.nome.contains(termo)) |
            (Usuario.descricao.contains(termo))
        )
    
    if filtro_bairro and filtro_bairro != 'Todos':
        query = query.filter_by(bairro=filtro_bairro)
        
    profissionais = query.all()
    bairros_garanhuns = ['Heliópolis', 'Magano', 'Boa Vista', 'Cohab 1', 'Cohab 2', 'Centro', 'Brasília', 'Aloísio Pinto']
    
    return render_template('index.html', 
                         profissionais=profissionais, 
                         bairros=bairros_garanhuns,
                         termo_atual=termo)

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        try:
            # Pega os dados do formulário
            nome = request.form.get('nome')
            email = request.form.get('email')
            senha_bruta = request.form.get('senha') # Senha que o usuário digitou (ex: 12345)
            cpf = request.form.get('cpf')
            whatsapp = request.form.get('whatsapp')
            tipo = request.form.get('tipo')
            
            # 1. Verifica se o email já existe
            if Usuario.query.filter_by(email=email).first():
                flash('Este email já está cadastrado! Tente fazer login.', 'danger')
                return redirect(url_for('cadastro'))
            
            # 2. CRIPTOGRAFA A SENHA (SEGURANÇA)
            senha_hash = generate_password_hash(senha_bruta) 
            
            # 3. Cria o objeto Usuário
            novo_usuario = Usuario(
                nome=nome, 
                email=email, 
                senha=senha_hash, # Salva o HASH, nunca a senha pura
                tipo=tipo, 
                cpf=cpf, 
                whatsapp=whatsapp
            )
            
            # 4. Se for profissional, pega os dados extras
            if tipo == 'profissional':
                novo_usuario.profissao = request.form.get('profissao')
                novo_usuario.bairro = request.form.get('bairro')
                novo_usuario.descricao = request.form.get('descricao')
                
            # 5. Salva no Banco
            db.session.add(novo_usuario)
            db.session.commit()
            
            flash('Conta criada com sucesso! Pode entrar.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            flash(f'Erro ao cadastrar: {str(e)}', 'danger')
            return redirect(url_for('cadastro'))
            
    return render_template('cadastro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        # Busca o usuário pelo email
        usuario = Usuario.query.filter_by(email=email).first()
        
        # Verifica: 1. Se usuário existe E 2. Se a senha bate com o Hash
        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario)
            
            # Redireciona direto para o perfil para ele ver os dados dele
            return redirect(url_for('perfil'))
        else:
            flash('Login inválido. Verifique seu email e senha.', 'danger')
            
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/perfil')
@login_required
def perfil():
    return render_template('perfil.html')

# --- ROTA DE EDIÇÃO COM UPLOAD ---
@app.route('/editar_perfil', methods=['POST'])
@login_required
def editar_perfil():
    try:
        current_user.nome = request.form.get('nome')
        current_user.whatsapp = request.form.get('whatsapp')
        
        # --- Lógica da Foto ---
        # Verifica se enviou arquivo
        if 'foto' in request.files:
            file = request.files['foto']
            # Verifica se tem nome e extensão permitida
            if file and file.filename != '' and allowed_file(file.filename):
                # Cria um nome seguro (e único, usando o ID do usuario para não misturar)
                extensao = file.filename.rsplit('.', 1)[1].lower()
                novo_nome = f"user_{current_user.id}.{extensao}"
                
                # Salva na pasta
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], novo_nome))
                
                # Atualiza no banco
                current_user.foto_perfil = novo_nome

        if current_user.tipo == 'profissional':
            current_user.profissao = request.form.get('profissao')
            current_user.bairro = request.form.get('bairro')
            current_user.descricao = request.form.get('descricao')
            
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao atualizar: {str(e)}', 'danger')
        
    return redirect(url_for('perfil'))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)