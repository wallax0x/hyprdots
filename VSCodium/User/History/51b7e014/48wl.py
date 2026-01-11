import os
import re
import requests
from flask import Flask, render_template, redirect, url_for, flash, jsonify, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
# Importe seus models e forms aqui
from models import User, Professional, ServiceCategory, ServiceRequest, Review
from forms import RegistroForm # Importar o form criado acima

app = Flask(__name__)

# ------------------------------
# CONFIGURAÇÃO SEGURA
# ------------------------------
# Em produção, use variáveis de ambiente!
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "chave_padrao_dev_apenas")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Por favor, faça login para acessar essa página."

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------------------
# HELPERS OTIMIZADOS
# ------------------------------
def validate_cep_garanhuns(cep: str):
    """Valida CEP via ViaCEP e garante Garanhuns–PE."""
    if not cep: return None
    cep_digits = re.sub(r'\D', '', cep)
    
    if len(cep_digits) != 8: return None

    try:
        # Timeout reduzido para não travar o app se a API cair
        r = requests.get(f"https://viacep.com.br/ws/{cep_digits}/json/", timeout=3)
        if not r.ok: return None
        
        data = r.json()
        if 'erro' in data: return None

        # Lógica de Negócio: Apenas Garanhuns
        if data.get('localidade') != 'Garanhuns' or data.get('uf') != 'PE':
            return {'error': 'servico_indisponivel', 'msg': 'Atendemos apenas em Garanhuns-PE no momento.'}

        return {
            'cep': cep_digits,
            'address': data.get('logradouro', ''),
            'neighborhood': data.get('bairro', ''),
            'city': data.get('localidade', ''),
            'state': data.get('uf', '')
        }
    except requests.exceptions.RequestException:
        # Logar erro aqui seria ideal
        return None

# ------------------------------
# ROTAS PRINCIPAIS
# ------------------------------

@app.route('/registro', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistroForm()

    if form.validate_on_submit(): # Validação automática do WTForms
        # Verificar duplicidade
        # Nota: Remova a formatação do CPF para buscar no banco se você salva apenas números
        cpf_limpo = re.sub(r'\D', '', form.cpf.data)
        
        if User.query.filter((User.cpf == form.cpf.data) | (User.email == form.email.data)).first():
            flash('CPF ou Email já cadastrados.', 'error')
            return render_template('register.html', form=form)

        # Validar CEP
        cep_data = validate_cep_garanhuns(form.cep.data)
        if not cep_data or 'error' in cep_data:
            msg = cep_data['msg'] if cep_data and 'msg' in cep_data else 'CEP inválido ou erro na consulta.'
            flash(msg, 'error')
            return render_template('register.html', form=form)

        # Criar Usuário
        user = User(
            name=form.name.data,
            email=form.email.data,
            cpf=form.cpf.data, # Idealmente salvar limpo ou mascarado consistentemente
            password_hash=generate_password_hash(form.password.data),
            user_type=form.user_type.data,
            phone=form.phone.data,
            cep=cep_data['cep'],
            address=cep_data['address'],
            neighborhood=cep_data['neighborhood'],
            city=cep_data['city'],
            state=cep_data['state']
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            login_user(user)
            
            if user.user_type == 'professional':
                flash('Conta criada! Agora complete seu perfil profissional.', 'info')
                return redirect(url_for('complete_professional_profile'))
            
            flash('Cadastro realizado com sucesso!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao salvar no banco de dados.', 'error')

    return render_template('register.html', form=form)

@app.route('/excluir_proprio_usuario', methods=['POST'])
@login_required
def excluir_proprio_usuario():
    """
    Versão otimizada. Se os models tiverem cascade='all, delete',
    você só precisa deletar o usuário.
    """
    user = User.query.get_or_404(current_user.id)
    
    # Logout imediato para evitar problemas de sessão
    logout_user()
    
    try:
        # Se configurou cascade nos models, basta isso:
        db.session.delete(user)
        db.session.commit()
        flash("Sua conta e dados vinculados foram excluídos.", "success")
    except Exception as e:
        db.session.rollback() db.session.rollback()
        flash("Erro ao excluir conta. Tente novamente.", "error")
        
    return redirect(url_for('index'))

# ... (Mantenha as outras rotas: login, index, dashboard, etc.)

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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)