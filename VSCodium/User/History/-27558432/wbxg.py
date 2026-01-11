import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# -----------------------------------
# CONFIGURAÇÃO DO APP
# -----------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_garanhuns'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///garanhuns.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ---- CONFIGURAÇÃO DE UPLOAD ----
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Cria a pasta de uploads se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -----------------------------------
# LOGIN MANAGER
# -----------------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Por favor, faça login para acessar essa página."
login_manager.login_message_category = "info"

# -----------------------------------
# BANCO DE DADOS
# -----------------------------------
db = SQLAlchemy(app)

# MODELO DO USUÁRIO
class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    cpf = db.Column(db.String(14), nullable=True)
    whatsapp = db.Column(db.String(20), nullable=True)

    # Foto do perfil
    foto_perfil = db.Column(db.String(120), default='default.png')

    # Dados do profissional
    profissao = db.Column(db.String(50), nullable=True)
    bairro = db.Column(db.String(50), nullable=True)
    descricao = db.Column(db.Text, nullable=True)


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


# -----------------------------------
# ROTAS
# -----------------------------------

@app.route('/')
def index():
    termo = request.args.get('q', '')
    filtro_bairro = request.args.get('bairro', '')

    query = Usuario.query.filter_by(tipo='profissional')

    # Busca por nome, profissão ou descrição
    if termo:
        query = query.filter(
            (Usuario.profissao.contains(termo)) |
            (Usuario.nome.contains(termo)) |
            (Usuario.descricao.contains(termo))
        )

    # Filtro de bairro
    if filtro_bairro and filtro_bairro != 'Todos':
        query = query.filter_by(bairro=filtro_bairro)

    profissionais = query.all()

    bairros_garanhuns = [
        'Heliópolis', 'Magano', 'Boa Vista', 'Cohab 1', 'Cohab 2',
        'Centro', 'Brasília', 'Aloísio Pinto'
    ]

    return render_template(
        'index.html',
        profissionais=profissionais,
        bairros=bairros_garanhuns,
        termo_atual=termo
    )


# -----------------------------------
# CADASTRO
# -----------------------------------
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        try:
            nome = request.form.get('nome')
            email = request.form.get('email')
            senha_bruta = request.form.get('senha')
            cpf = request.form.get('cpf')
            whatsapp = request.form.get('whatsapp')
            tipo = request.form.get('tipo')

            # Verifica email duplicado
            if Usuario.query.filter_by(email=email).first():
                flash('Este email já está cadastrado! Tente fazer login.', 'danger')
                return redirect(url_for('cadastro'))

            # Criptografa senha
            senha_hash = generate_password_hash(senha_bruta)

            novo_usuario = Usuario(
                nome=nome,
                email=email,
                senha=senha_hash,
                tipo=tipo,
                cpf=cpf,
                whatsapp=whatsapp
            )

            # Dados extras de profissional
            if tipo == 'profissional':
                novo_usuario.profissao = request.form.get('profissao')
                novo_usuario.bairro = request.form.get('bairro')
                novo_usuario.descricao = request.form.get('descricao')

            db.session.add(novo_usuario)
            db.session.commit()

            flash('Conta criada com sucesso! Pode entrar agora.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            flash(f'Erro ao cadastrar: {str(e)}', 'danger')
            return redirect(url_for('cadastro'))

    return render_template('cadastro.html')


# -----------------------------------
# LOGIN
# -----------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario)
            return redirect(url_for('perfil'))
        else:
            flash('Login inválido. Verifique seu email e senha.', 'danger')

    return render_template('login.html')


# -----------------------------------
# LOGOUT
# -----------------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# -----------------------------------
# PERFIL
# -----------------------------------
@app.route('/perfil')
@login_required
def perfil():
    return render_template('perfil.html')


# -----------------------------------
# EDITAR PERFIL + UPLOAD DE FOTO
# -----------------------------------
@app.route('/editar_perfil', methods=['POST'])
@login_required
def editar_perfil():
    try:
        current_user.nome = request.form.get('nome')
        current_user.whatsapp = request.form.get('whatsapp')

        # FOTO DE PERFIL
        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename != '' and allowed_file(file.filename):
                extensao = file.filename.rsplit('.', 1)[1].lower()
                novo_nome = f"user_{current_user.id}.{extensao}"

                file.save(os.path.join(app.config['UPLOAD_FOLDER'], novo_nome))

                current_user.foto_perfil = novo_nome

        # Dados de profissional
        if current_user.tipo == 'profissional':
            current_user.profissao = request.form.get('profissao')
            current_user.bairro = request.form.get('bairro')
            current_user.descricao = request.form.get('descricao')

        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')

    except Exception as e:
        flash(f'Erro ao atualizar: {str(e)}', 'danger')

    return redirect(url_for('perfil'))


# -----------------------------------
# CRIA BANCO
# -----------------------------------
with app.app_context():
    db.create_all()


# -----------------------------------
# RODAR O SERVIDOR
# -----------------------------------
if __name__ == '__main__':
    app.run(debug=True)
