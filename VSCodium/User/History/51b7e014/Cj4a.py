from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from validate_docbr import CPF
import requests
from datetime import datetime
import re
from sqlalchemy import or_, and_

# ------------------------------
# CONFIGURAÇÃO DO APP
# ------------------------------
app = Flask(__name__)
app.secret_key = "uma_chave_muito_secreta"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# importar e inicializar db
from database import db
db.init_app(app)

# importar models
from models import User, Professional, ServiceCategory, ServiceRequest, Review

# LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# CPF validator
cpf_validator = CPF()

# ------------------------------
# HELPERS
# ------------------------------
def normalize_cpf_masked(cpf_masked: str) -> str:
    """Transforma para 000.000.000-00."""
    if not cpf_masked:
        return ''
    digits = re.sub(r'\D', '', cpf_masked)
    if len(digits) != 11:
        return cpf_masked
    return f"{digits[0:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:11]}"

def validate_cep_garanhuns(cep: str):
    """Valida CEP via ViaCEP e garante Garanhuns–PE."""
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
        if data.get('localidade') != 'Garanhuns' or data.get('uf') != 'PE':
            return None

        return {
            'cep': cep_digits,
            'address': data.get('logradouro', ''),
            'neighborhood': data.get('bairro', ''),
            'city': data.get('localidade', ''),
            'state': data.get('uf', '')
        }
    except Exception:
        return None

# ------------------------------
# ROTAS
# ------------------------------

@app.route('/')
def index():
    categories = ServiceCategory.query.all()
    professionals = Professional.query.order_by(Professional.created_at.desc()).limit(6).all()
    return render_template('index.html', categories=categories, professionals=professionals)


# REGISTRO
@app.route('/registro', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        cpf_raw = request.form.get('cpf')
        cpf_mask = normalize_cpf_masked(cpf_raw)
        password = request.form.get('password')
        user_type = request.form.get('user_type', 'client')
        phone = request.form.get('phone')
        cep_raw = request.form.get('cep')

        if not cpf_mask or not cpf_validator.validate(re.sub(r'\D', '', cpf_mask)):
            flash('CPF inválido', 'error')
            return render_template('register.html')

        cep_data = validate_cep_garanhuns(cep_raw)
        if not cep_data:
            flash('CEP inválido ou fora de Garanhuns-PE', 'error')
            return render_template('register.html')

        if User.query.filter_by(cpf=cpf_mask).first() or User.query.filter_by(email=email).first():
            flash('CPF ou email já cadastrado', 'error')
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
            state=cep_data['state']
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)

        if user_type == 'professional':
            return redirect(url_for('complete_professional_profile'))

        return redirect(url_for('index'))

    return render_template('register.html')


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        cpf_raw = request.form.get('cpf')
        cpf_mask = normalize_cpf_masked(cpf_raw)
        password = request.form.get('password')

        user = User.query.filter_by(cpf=cpf_mask).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))

        flash('CPF ou senha incorretos', 'error')

    return render_template('login.html')


# LOGOUT
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# SEARCH
@app.route('/search')
def search():
    name = request.args.get('name', '').strip()
    category_id = request.args.get('category', '')
    neighborhood = request.args.get('neighborhood', '').strip()
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')

    query = Professional.query.join(User)

    if name:
        query = query.filter(User.name.ilike(f"%{name}%"))

    if category_id and category_id.isdigit():
        query = query.filter(Professional.category_id == int(category_id))

    if neighborhood:
        query = query.filter(User.neighborhood.ilike(f"%{neighborhood}%"))

    if min_price:
        try:
            query = query.filter(Professional.starting_price >= float(min_price))
        except:
            pass

    if max_price:
        try:
            query = query.filter(Professional.starting_price <= float(max_price))
        except:
            pass

    professionals = query.all()
    categories = ServiceCategory.query.all()

    return render_template('search.html', professionals=professionals, categories=categories)


# COMPLETAR PERFIL PROFISSIONAL
@app.route('/completar-perfil-profissional', methods=['GET', 'POST'])
@login_required
def complete_professional_profile():
    if current_user.user_type != 'professional':
        return redirect(url_for('index'))

    if Professional.query.filter_by(user_id=current_user.id).first():
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        prof = Professional(
            user_id=current_user.id,
            category_id=int(request.form.get('category_id')) if request.form.get('category_id') else None,
            bio=request.form.get('bio'),
            experience_years=int(request.form.get('experience_years')) if request.form.get('experience_years') else None,
            starting_price=float(request.form.get('starting_price')) if request.form.get('starting_price') else None,
            response_time='24 horas'
        )

        db.session.add(prof)
        db.session.commit()

        flash('Perfil profissional criado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    categories = ServiceCategory.query.all()
    return render_template('complete_profile.html', categories=categories)


# DASHBOARD
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.user_type == 'professional':

        prof = Professional.query.filter_by(user_id=current_user.id).first()
        if not prof:
            return redirect(url_for('complete_professional_profile'))

        requests_list = ServiceRequest.query.filter_by(
            professional_id=prof.id
        ).order_by(ServiceRequest.created_at.desc()).all()

        return render_template('dashboard_professional.html', professional=prof, requests=requests_list)

    else:
        requests_list = ServiceRequest.query.filter_by(
            client_id=current_user.id
        ).order_by(ServiceRequest.created_at.desc()).all()

        return render_template('dashboard_client.html', requests=requests_list)


# PERFIL
@app.route('/perfil')
@login_required
def perfil():
    return render_template("perfil.html")


# EXCLUIR PRÓPRIO USUÁRIO — versão corrigida
@app.route('/excluir_proprio_usuario', methods=['POST'])
@login_required
def excluir_proprio_usuario():

    user = User.query.get(int(current_user.id))

    if not user:
        flash("Usuário não encontrado.", "error")
        return redirect(url_for('dashboard'))

    user_id = user.id

    # Logout antes de excluir
    logout_user()

    # Delete Requests
    ServiceRequest.query.filter(
        (ServiceRequest.client_id == user_id) |
        (ServiceRequest.professional_id == user_id)
    ).delete(synchronize_session=False)

    # Delete Reviews
    Review.query.filter_by(client_id=user_id).delete(synchronize_session=False)

    # Delete Professional profile
    prof = Professional.query.filter_by(user_id=user_id).first()
    if prof:
        Review.query.filter_by(professional_id=prof.id).delete(synchronize_session=False)
        db.session.delete(prof)

    db.session.delete(user)
    db.session.commit()

    flash("Conta excluída com sucesso!", "success")
    return redirect(url_for('index'))


# API – validar CEP
@app.route('/api/validar-cep/<cep>')
def api_validate_cep(cep):
    data = validate_cep_garanhuns(cep)
    if data:
        return jsonify(data)
    return jsonify({'error': 'CEP inválido ou fora de Garanhuns–PE'}), 400


# EXECUÇÃO
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)