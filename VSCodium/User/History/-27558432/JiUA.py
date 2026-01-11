import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# ---- VALIDADORES ---- #

def validar_cpf(cpf):
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * len(cpf):
        return False

    # cálculo do CPF
    for i in range(9, 11):
        soma = sum(int(cpf[num]) * ((i + 1) - num) for num in range(0, i))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(cpf[i]):
            return False
    return True


def validar_whatsapp(numero):
    numero = re.sub(r'\D', '', numero)
    return len(numero) >= 10 and len(numero) <= 11


def validar_email(email):
    padrao = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(padrao, email) is not None


def validar_senha(senha):
    return len(senha) >= 6


def validar_bairro(bairro):
    bairros = ["Heliópolis", "Magano", "Boa Vista", "Cohab 1", "Cohab 2", "Centro", "Brasília", "Outro"]
    return bairro in bairros


def limpar(texto):
    return re.sub(r"[<>]", "", texto)  # Protege contra XSS


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


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":

        nome = limpar(request.form.get("nome"))
        cpf = request.form.get("cpf", "")
        whatsapp = request.form.get("whatsapp", "")
        email = request.form.get("email", "")
        senha = request.form.get("senha", "")
        tipo = request.form.get("tipo", "")
        
        profissao = request.form.get("profissao", "")
        bairro = request.form.get("bairro", "")
        descricao = limpar(request.form.get("descricao", ""))

        # --- VALIDACOES ---
        if not nome or len(nome) < 3:
            flash("Nome inválido!", "danger")
            return redirect("/cadastro")

        if cpf and not validar_cpf(cpf):
            flash("CPF inválido!", "danger")
            return redirect("/cadastro")

        if whatsapp and not validar_whatsapp(whatsapp):
            flash("WhatsApp inválido!", "danger")
            return redirect("/cadastro")

        if not validar_email(email):
            flash("E-mail inválido!", "danger")
            return redirect("/cadastro")

        if not validar_senha(senha):
            flash("A senha deve ter pelo menos 6 caracteres!", "danger")
            return redirect("/cadastro")

        if tipo not in ["cliente", "profissional"]:
            flash("Tipo de conta inválido!", "danger")
            return redirect("/cadastro")

        if tipo == "profissional":
            if not profissao or len(profissao) < 3:
                flash("Profissão inválida!", "danger")
                return redirect("/cadastro")

            if not validar_bairro(bairro):
                flash("Bairro inválido!", "danger")
                return redirect("/cadastro")

        # --- Verificar email já cadastrado ---
        if Usuario.query.filter_by(email=email).first():
            flash("Este e-mail já está cadastrado!", "danger")
            return redirect("/cadastro")

        # --- Criar usuário ---
        user = Usuario(
            nome=nome,
            cpf=re.sub(r'\D', '', cpf),
            whatsapp=re.sub(r'\D', '', whatsapp),
            email=email,
            senha=senha,  # você deve colocar hash aqui!
            tipo=tipo,
            profissao=profissao,
            bairro=bairro,
            descricao=descricao
        )

        db.session.add(user)
        db.session.commit()

        flash("Conta criada com sucesso!", "success")
        return redirect("/login")

    return render_template("cadastro.html")



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
