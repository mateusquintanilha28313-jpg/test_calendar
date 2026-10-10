import csv
import io
import json
import os
from functools import wraps
from pathlib import Path

from flask import Flask, render_template_string, request, redirect, url_for, Response, session


def get_users_file():
    return Path(os.environ.get("USERS_FILE", str(Path(__file__).with_name("users.json"))))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
if not app.config["SECRET_KEY"]:
    raise RuntimeError("SECRET_KEY environment variable must be set")


def get_agendamentos_file():
    return Path(os.environ.get("AGENDAMENTOS_FILE", str(Path(__file__).with_name("agendamentos.json"))))


def carregar_agendamentos():
    arquivo = get_agendamentos_file()
    if not arquivo.exists():
        return []

    try:
        with arquivo.open("r", encoding="utf-8") as f:
            dados = json.load(f)
            if isinstance(dados, list):
                return dados
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass

    return []


def salvar_agendamentos(agendamentos):
    arquivo = get_agendamentos_file()
    arquivo.parent.mkdir(parents=True, exist_ok=True)

    with arquivo.open("w", encoding="utf-8") as f:
        json.dump(agendamentos, f, ensure_ascii=False, indent=2)


# Lista inicial carregada do arquivo de persistência
agendamentos = carregar_agendamentos()


def carregar_usuarios():
    arquivo = get_users_file()
    if not arquivo.exists():
        return []

    try:
        with arquivo.open("r", encoding="utf-8") as f:
            dados = json.load(f)
            if isinstance(dados, list):
                return dados
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass

    return []


def salvar_usuarios(usuarios):
    arquivo = get_users_file()
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    with arquivo.open("w", encoding="utf-8") as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=2)


def get_default_user():
    username = os.environ.get("APP_USERNAME")
    password = os.environ.get("APP_PASSWORD")
    if not username or not password:
        return None

    return {
        "username": username,
        "password": password,
        "role": "professor",
    }


def autenticar_usuario(username, password):
    username = (username or '').strip()
    password = (password or '').strip()

    for usuario in carregar_usuarios():
        if usuario.get('username') == username and usuario.get('password') == password:
            return True

    default_user = get_default_user()
    if default_user and username == default_user["username"] and password == default_user["password"]:
        return True

    return False


def get_user_role(username):
    username = (username or '').strip()
    for usuario in carregar_usuarios():
        if usuario.get('username') == username:
            return (usuario.get('role') or 'aluno').lower()

    default_user = get_default_user()
    if default_user and username == default_user["username"]:
        return default_user["role"]

    return 'aluno'


def e_dono_do_teste(item, username):
    if item.get('usuario'):
        return item.get('usuario') == username
    if username == 'admin':
        return True
    return (item.get('nome') or '').lower() == username.lower()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login_page"))
        return view(*args, **kwargs)

    return wrapped


def professor_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login_page"))
        if (session.get('role') or get_user_role(session.get('username'))) != 'professor':
            return redirect(url_for('home'))
        return view(*args, **kwargs)

    return wrapped


HTML_LOGIN = """
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>Login</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
        .box { background: white; padding: 30px; border-radius: 12px; width: min(420px, 90%); box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08); }
        .logo { display: block; width: 140px; height: 140px; object-fit: contain; margin: 0 auto 16px; }
        h2 { margin-bottom: 20px; color: #0f172a; }
        form { display: flex; flex-direction: column; gap: 16px; }
        input { padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; }
        button { background: #2563eb; color: white; border: none; border-radius: 8px; padding: 12px; font-weight: 600; cursor: pointer; }
        .error { color: #b91c1c; margin-bottom: 10px; font-size: 14px; }
        .link { margin-top: 12px; text-align: center; font-size: 14px; }
        a { color: #2563eb; text-decoration: none; }
    </style>
</head>
<body>
    <div class="box">
        <img class="logo" src="{{ url_for('static', filename='images/465265618_1118096523653749_7654686943570440081_n.jpg') }}" alt="Teoria dos Números">
        <h2>Login</h2>
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Utilizador" required>
            <input type="password" name="password" placeholder="Palavra-passe" required>
            <button type="submit">Entrar</button>
        </form>
        <div class="link">
            Ainda não tem conta? <a href="/logon">Crie uma</a>
        </div>
    </div>
</body>
</html>
"""

HTML_LOGON = """
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>Logon</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
        .box { background: white; padding: 30px; border-radius: 12px; width: min(420px, 90%); box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08); }
        h2 { margin-bottom: 20px; color: #0f172a; }
        form { display: flex; flex-direction: column; gap: 16px; }
        input { padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; }
        button { background: #16a34a; color: white; border: none; border-radius: 8px; padding: 12px; font-weight: 600; cursor: pointer; }
        .error { color: #b91c1c; margin-bottom: 10px; font-size: 14px; }
        .success { color: #166534; margin-bottom: 10px; font-size: 14px; }
        .link { margin-top: 12px; text-align: center; font-size: 14px; }
        a { color: #2563eb; text-decoration: none; }
    </style>
</head>
<body>
    <div class="box">
        <h2>Criar conta</h2>
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        {% if success %}
            <div class="success">{{ success }}</div>
        {% endif %}
        <form method="POST" action="/logon">
            <input type="text" name="username" placeholder="Utilizador" required>
            <input type="password" name="password" placeholder="Palavra-passe" required>
            <select name="role" required>
                <option value="aluno">Aluno</option>
                <option value="professor" disabled>Professor (só por gestão interna)</option>
            </select>
            <button type="submit">Criar conta</button>
        </form>
        <div class="link">
            Já tem conta? <a href="/login">Voltar ao login</a>
        </div>
    </div>
</body>
</html>
"""

# Template HTML atualizado (PT-PT)
HTML_GESTAO = """
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>Gestão de Utilizadores</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f8fafc; color: #0f172a; }
        nav { background: #1e293b; color: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; }
        nav h2 { font-size: 20px; }
        nav .brand { display: flex; align-items: center; gap: 12px; }
        nav .brand-logo { width: 58px; height: 58px; object-fit: contain; background: white; border-radius: 8px; }
        .nav-actions { display: flex; gap: 12px; align-items: center; }
        .btn { display: inline-block; border-radius: 20px; text-decoration: none; padding: 8px 16px; font-size: 13px; font-weight: 600; }
        .btn-primary { background: #2563eb; color: white; }
        .btn-danger { background: #ef4444; color: white; }
        .container { max-width: 900px; margin: 30px auto; padding: 0 20px; }
        .card { background: white; border-radius: 12px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); padding: 24px; }
        h3 { margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 12px 10px; border-bottom: 1px solid #e2e8f0; text-align: left; }
        th { background: #f8fafc; }
        select, button { padding: 10px 12px; border-radius: 8px; border: 1px solid #cbd5e1; }
        form { display: flex; align-items: center; gap: 12px; }
        button { background: #16a34a; color: white; border: none; cursor: pointer; }
        .msg { margin-bottom: 12px; color: #166534; font-weight: 600; }
    </style>
</head>
<body>
    <nav>
        <div class="brand">
            <img class="brand-logo" src="{{ url_for('static', filename='images/465265618_1118096523653749_7654686943570440081_n.jpg') }}" alt="Logótipo Teoria dos Números">
            <h2>Teoria dos Números</h2>
        </div>
        <div class="nav-actions">
            <a href="/" class="btn btn-primary">Voltar</a>
            <a href="/logout" class="btn btn-danger">Sair</a>
        </div>
    </nav>
    <div class="container">
        <div class="card">
            <h3>Gestao de Utilizadores</h3>
            {% if message %}
                <div class="msg">{{ message }}</div>
            {% endif %}
            <table>
                <thead>
                    <tr>
                        <th>Utilizador</th>
                        <th>Papel</th>
                        <th>Alterar</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user in users %}
                    <tr>
                        <td>{{ user.username }}</td>
                        <td>{{ user.role }}</td>
                        <td>
                            <form method="POST" action="/gestao-utilizadores">
                                <input type="hidden" name="username" value="{{ user.username }}">
                                <select name="role">
                                    <option value="aluno" {% if user.role == 'aluno' %}selected{% endif %}>Aluno</option>
                                    <option value="professor" {% if user.role == 'professor' %}selected{% endif %}>Professor</option>
                                </select>
                                <button type="submit">Guardar</button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

HTML_HOME = """
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>Calendário de Testes</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html { scroll-behavior: smooth; } /* Efeito de deslize suave ao clicar no botão */
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; color: #333; }
        
        /* Menu de Navegação Superior */
        nav { background-color: #1e293b; color: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        nav h2 { font-size: 20px; font-weight: 600; letter-spacing: 0.5px; }
        nav .brand { display: flex; align-items: center; gap: 12px; }
        nav .brand-logo { width: 58px; height: 58px; object-fit: contain; background: white; border-radius: 8px; }
        
        /* Botão interativo no canto superior direito */
        .btn-topo { background-color: #3b82f6; color: white; padding: 8px 16px; border-radius: 20px; font-size: 13px; font-weight: 500; text-decoration: none; transition: background-color 0.2s; display: inline-block; }
        .btn-topo:hover { background-color: #2563eb; }

        /* Container Principal */
        .container { max-width: 800px; margin: 30px auto; padding: 0 20px; }
        
        .card { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 25px; }
        h2.section-title { margin-bottom: 20px; color: #1e293b; font-size: 22px; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px; }

        /* Formulário */
        form { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .form-group { display: flex; flex-direction: column; gap: 8px; }
        .form-group.full-width { grid-column: span 2; }
        
        label { font-weight: 600; font-size: 14px; color: #475569; }
        input, select { padding: 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px; transition: border-color 0.2s; background-color: #fff; }
        input:focus, select:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); }
        
        button[type="submit"] { grid-column: span 2; background-color: #3b82f6; color: white; padding: 12px; border: none; border-radius: 6px; font-size: 16px; font-weight: 600; cursor: pointer; transition: background-color 0.2s; }
        button[type="submit"]:hover { background-color: #2563eb; }

        /* Lista de Marcações */
        .lista-container { margin-top: 10px; }
        .item-marcação { background: #f8fafc; border: 1px solid #e2e8f0; padding: 15px 20px; border-radius: 8px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; gap: 16px; }
        .info-aluno { display: flex; flex-direction: column; gap: 4px; }
        .info-aluno strong { font-size: 16px; color: #0f172a; }
        .info-aluno span { font-size: 13px; color: #64748b; }
        
        .badges { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
        .badge { padding: 5px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; }
        .badge-teste { background-color: #fee2e2; color: #991b1b; }
        .badge-nota { background-color: #dcfce7; color: #166534; }
        .badge-vazia { background-color: #f1f5f9; color: #475569; }
        .data-hora { font-size: 13px; font-weight: 500; color: #475569; background: #e2e8f0; padding: 5px 10px; border-radius: 6px; }

        .nota-form { display: flex; align-items: center; gap: 10px; }
        .nota-form input { width: 90px; }
        .nota-form button, .btn-export, .btn-limpar { border: none; border-radius: 6px; padding: 10px 12px; font-size: 13px; font-weight: 600; cursor: pointer; text-decoration: none; }
        .nota-form button { background-color: #10b981; color: white; }
        .btn-export { background-color: #0f766e; color: white; }
        .btn-limpar { background-color: #e2e8f0; color: #0f172a; }
        .toolbar { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-bottom: 20px; }
        .toolbar form { display: flex; gap: 10px; align-items: center; margin: 0; }
        .toolbar input { min-width: 220px; }
        
        .vazio { text-align: center; color: #94a3b8; padding: 20px; font-style: italic; }
    </style>
</head>
<body>

    <!-- Menu Superior -->
    <nav>
        <div class="brand">
            <img class="brand-logo" src="{{ url_for('static', filename='images/465265618_1118096523653749_7654686943570440081_n.jpg') }}" alt="Logótipo Teoria dos Números">
            <h2>Teoria dos Números</h2>
        </div>
        <div style="display: flex; gap: 12px; align-items: center;">
            <a href="#testes" class="btn-topo">Testes Registados</a>
            {% if session.get('role') == 'professor' %}
                <a href="/gestao-utilizadores" class="btn-topo" style="background-color: #10b981;">Gestão de Utilizadores</a>
            {% endif %}
            <a href="/logout" class="btn-topo" style="background-color: #ef4444;">Sair</a>
        </div>
    </nav>

    <div class="container">
        
        <!-- Formulário de Registo -->
        <div class="card">
            <h2 class="section-title">Calendário de Testes</h2>
            <form action="/agendar" method="POST">
                <div class="form-group">
                    <label for="nome">Nome do Aluno</label>
                    <input type="text" id="nome" name="nome" required>
                </div>

                <div class="form-group">
                    <label for="ano">Ano</label>
                    <select id="ano" name="ano" required>
                        <option value="" disabled selected>Selecionar</option>
                        <option value="1.º Ano">1.º Ano</option>
                        <option value="2.º Ano">2.º Ano</option>
                        <option value="3.º Ano">3.º Ano</option>
                        <option value="4.º Ano">4.º Ano</option>
                        <option value="5.º Ano">5.º Ano</option>
                        <option value="6.º Ano">6.º Ano</option>
                        <option value="7.º Ano">7.º Ano</option>
                        <option value="8.º Ano">8.º Ano</option>
                        <option value="9.º Ano">9.º Ano</option>
                        <option value="10.º Ano">10.º Ano</option>
                        <option value="11.º Ano">11.º Ano</option>
                        <option value="12.º Ano">12.º Ano</option>
                    </select>
                </div>

                <div class="form-group full-width">
                    <label for="disciplina">Disciplina</label>
                    <select id="disciplina" name="disciplina" required>
                        <option value="" disabled selected>Selecionar</option>
                        <option value="Matemática">Matemática</option>
                        <option value="Português">Português</option>
                        <option value="Estudo do Meio">Estudo do Meio</option>
                        <option value="HGP">HGP</option>
                        <option value="Ciências">Ciências</option>
                        <option value="Inglês">Inglês</option>
                        <option value="Francês">Francês</option>
                        <option value="História">História</option>
                        <option value="Geografia">Geografia</option>
                        <option value="Espanhol">Espanhol</option>
                        <option value="Físico-Química">Físico-Química</option>
                        <option value="MACS">MACS</option>
                    </select>
                </div>

                <div class="form-group full-width">
                    <label for="data">Data do Teste</label>
                    <input type="date" id="data" name="data" required>
                </div>

                <div class="form-group full-width">
                    <label for="nota">Nota do Teste (opcional)</label>
                    <input type="number" id="nota" name="nota" step="0.1" min="0" max="20" placeholder="Ex.: 16.5">
                </div>

                <button type="submit">Guardar Teste</button>
            </form>
        </div>

        <!-- Lista de Testes Registados (Com ID para o botão redirecionar) -->
        <div class="card" id="testes">
            <h2 class="section-title">Testes Registados</h2>
            <div class="toolbar">
                <form action="/" method="GET">
                    <input type="text" name="aluno" value="{{ filtro_aluno or '' }}" placeholder="Pesquisar aluno">
                    <button type="submit" class="btn-export">Filtrar</button>
                </form>
                {% if filtro_aluno %}
                    <a href="/" class="btn-limpar">Limpar</a>
                    <a href="/exportar-historico?aluno={{ filtro_aluno | urlencode }}" class="btn-export">Extrair histórico</a>
                {% endif %}
            </div>
            <div class="lista-container">
                {% if agendamentos %}
                    {% for a in agendamentos %}
                        <div class="item-marcação">
                            <div class="info-aluno">
                                <strong>{{ a.nome }}</strong>
                                <span>🎓 {{ a.ano }} | 📚 {{ a.disciplina }}</span>
                            </div>
                            <div class="badges">
                                <span class="badge badge-teste">Teste</span>
                                <span class="data-hora">📅 {{ a.data }}</span>
                                {% if a.nota %}
                                    <span class="badge badge-nota">Nota: {{ a.nota }}</span>
                                {% else %}
                                    <span class="badge badge-vazia">Sem nota</span>
                                {% endif %}
                            </div>
                            <form class="nota-form" action="/atualizar-nota" method="POST">
                                <input type="hidden" name="indice" value="{{ loop.index0 }}">
                                <input type="number" name="nota" step="0.1" min="0" max="20" value="{{ a.nota or '' }}" placeholder="Nota">
                                <button type="submit">Guardar nota</button>
                            </form>
                        </div>
                    {% endfor %}
                {% else %}
                    <p class="vazio">Ainda não existem testes registados.</p>
                {% endif %}
            </div>
        </div>

    </div>

</body>
</html>
"""

@app.route('/logon', methods=['GET', 'POST'])
def logon_page():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = (request.form.get('role', 'aluno') or 'aluno').strip().lower()

        if not username or not password:
            return render_template_string(HTML_LOGON, error='Preencha todos os campos.', success=None)

        if role not in {'aluno', 'professor'}:
            role = 'aluno'

        if role == 'professor':
            return render_template_string(
                HTML_LOGON,
                error='Apenas um professor pode criar outra conta de professor. Peça ao professor responsável.',
                success=None,
            )

        usuarios = carregar_usuarios()
        if any(u.get('username') == username for u in usuarios):
            return render_template_string(HTML_LOGON, error='Este utilizador já existe.', success=None)

        usuarios.append({"username": username, "password": password, "role": role})
        salvar_usuarios(usuarios)
        return render_template_string(HTML_LOGON, error=None, success='Conta criada com sucesso! Pode fazer login.')

    if session.get('logged_in'):
        return redirect(url_for('home'))

    return render_template_string(HTML_LOGON, error=None, success=None)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if autenticar_usuario(username, password):
            session['logged_in'] = True
            session['username'] = username
            session['role'] = get_user_role(username)
            return redirect(url_for('home'))

        return render_template_string(HTML_LOGIN, error='Credenciais inválidas.')

    if session.get('logged_in'):
        return redirect(url_for('home'))

    return render_template_string(HTML_LOGIN, error=None)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/')
@login_required
def home():
    filtro_aluno = (request.args.get('aluno') or '').strip()
    username = session.get('username')
    role = session.get('role') or get_user_role(username)

    if role == 'professor':
        agendamentos_atuais = carregar_agendamentos()
    else:
        agendamentos_atuais = [
            a for a in carregar_agendamentos()
            if e_dono_do_teste(a, username)
        ]

    if filtro_aluno:
        agendamentos_atuais = [
            a for a in agendamentos_atuais
            if filtro_aluno.lower() in (a.get('nome') or '').lower()
        ]

    return render_template_string(HTML_HOME, agendamentos=agendamentos_atuais, filtro_aluno=filtro_aluno)


@app.route('/gestao-utilizadores', methods=['GET', 'POST'])
@login_required
@professor_required
def gestao_utilizadores():
    message = None
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        role = (request.form.get('role') or 'aluno').strip().lower()
        if username and role in {'aluno', 'professor'}:
            usuarios = carregar_usuarios()
            for usuario in usuarios:
                if usuario.get('username') == username:
                    usuario['role'] = role
                    break
            salvar_usuarios(usuarios)
            message = f'Utilizador {username} atualizado para {role}.'

    usuarios = []
    for usuario in carregar_usuarios():
        usuarios.append({
            'username': usuario.get('username', ''),
            'role': (usuario.get('role') or 'aluno').lower(),
        })
    return render_template_string(HTML_GESTAO, users=usuarios, message=message)


@app.route('/agendar', methods=['POST'])
@login_required
def agendar():
    nome = request.form.get('nome')
    ano = request.form.get('ano')
    disciplina = request.form.get('disciplina')
    data = request.form.get('data')
    nota = request.form.get('nota', '').strip()

    if nome and ano and disciplina and data:
        agendamentos_atuais = carregar_agendamentos()
        agendamentos_atuais.append({
            'nome': nome,
            'ano': ano,
            'disciplina': disciplina,
            'data': data,
            'nota': nota,
            'usuario': session.get('username'),
        })
        salvar_agendamentos(agendamentos_atuais)

    return redirect(url_for('home'))


@app.route('/atualizar-nota', methods=['POST'])
@login_required
def atualizar_nota():
    indice = request.form.get('indice', '').strip()
    nota = request.form.get('nota', '').strip()

    try:
        indice_int = int(indice)
    except (TypeError, ValueError):
        return redirect(url_for('home'))

    agendamentos_atuais = carregar_agendamentos()

    if 0 <= indice_int < len(agendamentos_atuais):
        item = agendamentos_atuais[indice_int]
        role = session.get('role') or get_user_role(session.get('username'))
        if role == 'professor' or item.get('usuario') == session.get('username') or e_dono_do_teste(item, session.get('username')):
            item['nota'] = nota
            salvar_agendamentos(agendamentos_atuais)

    return redirect(url_for('home'))


@app.route('/exportar-historico')
@login_required
def exportar_historico():
    aluno = (request.args.get('aluno') or '').strip()
    username = session.get('username')
    role = session.get('role') or get_user_role(username)
    historico = []

    for a in carregar_agendamentos():
        if role == 'professor':
            permitido = True
        else:
            permitido = e_dono_do_teste(a, username)

        if permitido and (not aluno or aluno.lower() in (a.get('nome') or '').lower()):
            historico.append(a)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Nome', 'Ano', 'Disciplina', 'Data', 'Nota'])

    for item in historico:
        writer.writerow([
            item.get('nome', ''),
            item.get('ano', ''),
            item.get('disciplina', ''),
            item.get('data', ''),
            item.get('nota', ''),
        ])

    response = Response(output.getvalue(), mimetype='text/csv; charset=utf-8')
    nome_arquivo = (aluno or 'historico').replace(' ', '_').lower()
    response.headers['Content-Disposition'] = f'attachment; filename="{nome_arquivo}.csv"'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)