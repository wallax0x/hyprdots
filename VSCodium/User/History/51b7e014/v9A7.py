# app.py - versão final atualizada
import re
from datetime import datetime

import requests
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from validate_docbr import CPF
from sqlalchemy import or_

# ---------- Config do Flask ----------
app = Flask(__name__)
from dotenv import load_dotenv
import os

load_dotenv()
app.secret_key = os.getenv("SECRET_KEY", "chave_padrao_desenvolvimento")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ---------- Inicializar DB ----------
try:
    from database import db
except Exception as e:
    raise RuntimeError(
        "Erro ao importar 'db' de database.py. Verifique se existe database.py e contém 'db = SQLAlchemy()'."
    ) from e

db.init_app(app)

# ---------- Importar models ----------
try:
    from models import User, Professional, ServiceCategory, ServiceRequest, Review
except Exception as e:
    raise RuntimeError(
        "Erro ao importar models. Verifique models.py e ajuste nomes/classes: User, Professional, ServiceCategory, ServiceRequest, Review."
    ) from e

# ---------- Login manager ----------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None

# ---------- CPF validator ----------
cpf_validator = CPF()

# --------------------------
# HELPERS
# --------------------------
def normalize_cpf_masked(cpf_masked: str) -> str:
    """Converte qualquer entrada para formato 000.000.000-00 (se possível)."""
    if not cpf_masked:
        return ''
    digits = re.sub(r'\D', '', cpf_masked)
    if len(digits) != 11:
        return cpf_masked
    return f"{digits[0:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:11]}"

def validate_cep_garanhuns(cep: str):
    """Valida via ViaCEP e garante Garanhuns/PE. Retorna dict ou None."""
    if not cep:
        return None
    cep_digits = re.sub(r'\D', '', cep)
    if len(cep_digits) != 8:
        return None
    try:
        r = requests.get(f"https://viacep.com.br/ws/{cep_digits}/json/", timeout=5)
        if not r.ok:
            return None
        data = r.json()
        if 'erro' in data:
            return None
        # garante cidade/UF
        if data.get('localidade') != 'Garanhuns' or data.get('uf') != 'PE':
            return None
        return {
            'cep': cep_digits,
            'address': data.get('logradouro', '') or '',
            'neighborhood': data.get('bairro', '') or '',
            'city': data.get('localidade', '') or '',
            'state': data.get('uf', '') or ''
        }
    except Exception:
        return None

# --------------------------
# ROTAS
# --------------------------

@app.route('/')
def index():
    categories = ServiceCategory.query.order_by(ServiceCategory.name).all()
    professionals = Professional.query.order_by(Professional.created_at.desc()).limit(6).all()
    return render_template('index.html', categories=categories, professionals=professionals)


# --------------------------
# REGISTRO
# --------------------------
@app.route('/registro', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = (request.form.get('name') or "").strip()
        email = (request.form.get('email') or "").strip().lower()
        cpf_raw = request.form.get('cpf') or ""
        cpf_mask = normalize_cpf_masked(cpf_raw)
        password = request.form.get('password') or ""
        user_type = request.form.get('user_type', 'client')
        phone = (request.form.get('phone') or "").strip()
        cep_raw = request.form.get('cep') or ""

        # validações básicas
        if not name or not email or not password:
            flash('Nome, email e senha são obrigatórios.', 'danger')
            return render_template('register.html')

        digits_only_cpf = re.sub(r'\D', '', cpf_mask)
        if not cpf_mask or not cpf_validator.validate(digits_only_cpf):
            flash('CPF inválido.', 'danger')
            return render_template('register.html')

        cep_data = validate_cep_garanhuns(cep_raw)
        if not cep_data:
            flash('CEP inválido ou fora de Garanhuns-PE.', 'danger')
            return render_template('register.html')

        # verifica duplicidade
        if User.query.filter(or_(User.cpf == cpf_mask, User.email == email)).first():
            flash('CPF ou email já cadastrado.', 'danger')
            return render_template('register.html')

        user = User(
            name=name,
            email=email,
            cpf=cpf_mask,
            password_hash=generate_password_hash(password),
            user_type=user_type,
            phone=phone,
            cep=cep_data['cep'],
            address=cep_data['address'],
            neighborhood=cep_data['neighborhood'],
            city=cep_data['city'],
            state=cep_data['state'],
            created_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)

        if user_type == 'professional':
            return redirect(url_for('complete_professional_profile'))

        return redirect(url_for('index'))

    return render_template('register.html')


# --------------------------
# LOGIN
# --------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        cpf_raw = request.form.get('cpf') or ""
        cpf_mask = normalize_cpf_masked(cpf_raw)
        password = request.form.get('password') or ""

        user = User.query.filter_by(cpf=cpf_mask).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('CPF ou senha incorretos.', 'danger')

    return render_template('login.html')


# --------------------------
# LOGOUT
# --------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# --------------------------
# SEARCH
# --------------------------
@app.route('/search')
def search():
    name = (request.args.get('name') or '').strip()
    category_id = request.args.get('category', '')
    neighborhood = (request.args.get('neighborhood') or '').strip()
    min_price = (request.args.get('min_price') or '').strip()
    max_price = (request.args.get('max_price') or '').strip()

    # junção segura (Professional tem relationship user via backref)
    query = Professional.query.join(User)

    if name:
        query = query.filter(User.name.ilike(f"%{name}%"))

    if category_id and category_id.isdigit():
        query = query.filter(Professional.category_id == int(category_id))

    if neighborhood:
        query = query.filter(User.neighborhood.ilike(f"%{neighborhood}%"))

    try:
        if min_price:
            query = query.filter(Professional.starting_price >= float(min_price))
        if max_price:
            query = query.filter(Professional.starting_price <= float(max_price))
    except ValueError:
        # se preço inválido, ignora o filtro
        pass

    professionals = query.all()
    categories = ServiceCategory.query.order_by(ServiceCategory.name).all()
    return render_template('search.html', professionals=professionals, categories=categories)


# --------------------------
# COMPLETAR PERFIL PROFISSIONAL
# --------------------------
@app.route('/completar-perfil-profissional', methods=['GET', 'POST'])
@login_required
def complete_professional_profile():
    if getattr(current_user, 'user_type', None) != 'professional':
        return redirect(url_for('index'))

    # se já existe perfil, redireciona
    if Professional.query.filter_by(user_id=current_user.id).first():
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            category_id = int(request.form.get('category_id')) if request.form.get('category_id') else None
        except ValueError:
            category_id = None

        prof = Professional(
            user_id=current_user.id,
            category_id=category_id,
            bio=(request.form.get('bio') or '').strip(),
            experience_years=int(request.form.get('experience_years')) if request.form.get('experience_years') else None,
            starting_price=float(request.form.get('starting_price')) if request.form.get('starting_price') else None,
            response_time=request.form.get('response_time') or '24 horas',
            created_at=datetime.utcnow()
        )
        db.session.add(prof)
        db.session.commit()
        flash('Perfil profissional criado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    categories = ServiceCategory.query.order_by(ServiceCategory.name).all()
    return render_template('complete_profile.html', categories=categories)


# --------------------------
# DASHBOARD
# --------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    if getattr(current_user, 'user_type', None) == 'professional':
        prof = Professional.query.filter_by(user_id=current_user.id).first()
        if not prof:
            return redirect(url_for('complete_professional_profile'))
        requests_list = ServiceRequest.query.filter_by(professional_id=prof.id).order_by(ServiceRequest.created_at.desc()).all()
        return render_template('dashboard_professional.html', professional=prof, requests=requests_list)
    else:
        requests_list = ServiceRequest.query.filter_by(client_id=current_user.id).order_by(ServiceRequest.created_at.desc()).all()
        return render_template('dashboard_client.html', requests=requests_list)


# --------------------------
# PERFIL
# --------------------------
@app.route('/perfil')
@login_required
def perfil():
    user = User.query.get_or_404(current_user.id)
    prof = Professional.query.filter_by(user_id=user.id).first()
    return render_template("perfil.html", user=user, prof=prof)


# --------------------------
# EXCLUIR PRÓPRIO USUÁRIO
# --------------------------
@app.route('/excluir_proprio_usuario', methods=['POST'])
@login_required
def excluir_proprio_usuario():
    user = User.query.get(int(current_user.id))
    if not user:
        flash("Usuário não encontrado.", "danger")
        return redirect(url_for('dashboard'))

    user_id = user.id

    # Logout antes de apagar
    logout_user()

    # Excluir requests onde ele é cliente
    ServiceRequest.query.filter(ServiceRequest.client_id == user_id).delete(synchronize_session=False)

    # Se for profissional, excluir requests onde profissional é o perfil do usuário
    prof = Professional.query.filter_by(user_id=user_id).first()
    if prof:
        ServiceRequest.query.filter(ServiceRequest.professional_id == prof.id).delete(synchronize_session=False)
        # excluir reviews relacionadas ao profissional
        Review.query.filter_by(professional_id=prof.id).delete(synchronize_session=False)
        # remover perfil profissional
        db.session.delete(prof)

    # excluir reviews onde foi cliente
    Review.query.filter_by(client_id=user_id).delete(synchronize_session=False)

    # excluir usuário
    db.session.delete(user)
    db.session.commit()

    flash("Conta excluída com sucesso!", "success")
    return redirect(url_for('index'))


# --------------------------
# API – validar CEP
# --------------------------
@app.route('/api/validar-cep/<string:cep>')
def api_validate_cep(cep):
    data = validate_cep_garanhuns(cep)
    if data:
        return jsonify(data)
    return jsonify({'error': 'CEP inválido ou fora de Garanhuns–PE'}), 400


# --------------------------
# CATEGORIAS CRUD
# --------------------------
@app.route('/categorias')
@login_required
def listar_categorias():
    categorias = ServiceCategory.query.order_by(ServiceCategory.name).all()
    return render_template('categorias/listar.html', categorias=categorias)

@app.route('/categorias/add', methods=['GET', 'POST'])
@login_required
def adicionar_categoria():
    if request.method == 'POST':
        nome = (request.form.get('name') or '').strip()
        descricao = (request.form.get('description') or '').strip()
        if not nome:
            flash('Nome da categoria é obrigatório.', 'danger')
            return redirect(url_for('adicionar_categoria'))
        if ServiceCategory.query.filter_by(name=nome).first():
            flash('Categoria já existe.', 'danger')
            return redirect(url_for('adicionar_categoria'))
        cat = ServiceCategory(name=nome, description=descricao, created_at=datetime.utcnow())
        db.session.add(cat)
        db.session.commit()
        flash('Categoria adicionada com sucesso!', 'success')
        return redirect(url_for('listar_categorias'))
    return render_template('categorias/add.html')

@app.route('/categorias/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_categoria(id):
    categoria = ServiceCategory.query.get_or_404(id)
    if request.method == 'POST':
        categoria.name = (request.form.get('name') or categoria.name).strip()
        categoria.description = (request.form.get('description') or categoria.description).strip()
        db.session.commit()
        flash('Categoria atualizada.', 'success')
        return redirect(url_for('listar_categorias'))
    return render_template('categorias/edit.html', categoria=categoria)

@app.route('/categorias/delete/<int:id>', methods=['POST'])
@login_required
def deletar_categoria(id):
    categoria = ServiceCategory.query.get_or_404(id)
    # evita exclusão se houver profissionais vinculados
    if getattr(categoria, 'professionals', None) and len(categoria.professionals) > 0:
        flash('Não é possível remover: existem profissionais vinculados a essa categoria.', 'danger')
        return redirect(url_for('listar_categorias'))
    db.session.delete(categoria)
    db.session.commit()
    flash('Categoria removida.', 'success')
    return redirect(url_for('listar_categorias'))


# --------------------------
# PROFISSÕES CRUD
# --------------------------
@app.route('/profissoes')
@login_required
def listar_profissoes():
    profs = Professional.query.order_by(Professional.created_at.desc()).all()
    return render_template('profissoes/listar.html', profissoes=profs)

@app.route('/profissoes/add', methods=['GET', 'POST'])
@login_required
def adicionar_profissao():
    categories = ServiceCategory.query.order_by(ServiceCategory.name).all()
    if request.method == 'POST':
        try:
            category_id = int(request.form.get('category_id')) if request.form.get('category_id') else None
        except ValueError:
            category_id = None
        prof = Professional(
            user_id=current_user.id,
            category_id=category_id,
            bio=(request.form.get('bio') or '').strip(),
            experience_years=int(request.form.get('experience_years')) if request.form.get('experience_years') else None,
            starting_price=float(request.form.get('starting_price')) if request.form.get('starting_price') else None,
            response_time=request.form.get('response_time') or '24 horas',
            created_at=datetime.utcnow()
        )
        db.session.add(prof)
        db.session.commit()
        flash('Perfil profissional criado!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('profissoes/add.html', categories=categories)

@app.route('/profissoes/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_profissao(id):
    prof = Professional.query.get_or_404(id)
    if prof.user_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))
    categories = ServiceCategory.query.order_by(ServiceCategory.name).all()
    if request.method == 'POST':
        prof.category_id = int(request.form.get('category_id')) if request.form.get('category_id') else None
        prof.bio = (request.form.get('bio') or prof.bio).strip()
        prof.experience_years = int(request.form.get('experience_years')) if request.form.get('experience_years') else None
        prof.starting_price = float(request.form.get('starting_price')) if request.form.get('starting_price') else None
        prof.response_time = request.form.get('response_time') or prof.response_time
        db.session.commit()
        flash('Perfil atualizado.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('profissoes/edit.html', prof=prof, categories=categories)

@app.route('/profissoes/delete/<int:id>', methods=['POST'])
@login_required
def deletar_profissao(id):
    prof = Professional.query.get_or_404(id)
    if prof.user_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))
    # Remove reviews associados ao profissional
    Review.query.filter_by(professional_id=prof.id).delete(synchronize_session=False)
    db.session.delete(prof)
    db.session.commit()
    flash('Perfil profissional excluído.', 'success')
    return redirect(url_for('dashboard'))


# --------------------------
# EDITAR PERFIL DO USUÁRIO
# --------------------------
@app.route('/perfil/editar', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    user = User.query.get_or_404(current_user.id)
    prof = Professional.query.filter_by(user_id=user.id).first()
    categories = ServiceCategory.query.order_by(ServiceCategory.name).all()

    if request.method == 'POST':
        user.name = (request.form.get('name') or user.name).strip()
        user.email = (request.form.get('email') or user.email).strip().lower()
        user.phone = (request.form.get('phone') or user.phone).strip()
        senha = (request.form.get('password') or '').strip()
        if senha:
            user.password_hash = generate_password_hash(senha)
        # opcional: atualizar endereço/cep – fazer validação se necessário
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('perfil'))

    return render_template('usuarios/edit.html', user=user, prof=prof, categories=categories)


# --------------------------
# execução
# --------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
