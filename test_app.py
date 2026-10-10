import importlib
import json

import pytest


@pytest.fixture(autouse=True)
def configurar_ambiente_teste(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-only-secret-key")
    monkeypatch.setenv("APP_USERNAME", "admin")
    monkeypatch.setenv("APP_PASSWORD", "admin123")


def test_agendar_salva_no_arquivo(monkeypatch, tmp_path):
    arquivo = tmp_path / "agendamentos.json"
    monkeypatch.setenv("AGENDAMENTOS_FILE", str(arquivo))
    monkeypatch.setenv("USERS_FILE", str(tmp_path / "users.json"))

    import app as app_module
    importlib.reload(app_module)

    client = app_module.app.test_client()
    client.post("/login", data={"username": "admin", "password": "admin123"})
    response = client.post(
        "/agendar",
        data={
            "nome": "Ana",
            "ano": "9.º Ano",
            "disciplina": "Matemática",
            "data": "2026-10-20",
            "nota": "17.5",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert arquivo.exists()
    with arquivo.open("r", encoding="utf-8") as f:
        dados = json.load(f)
    assert dados[0]["nome"] == "Ana"
    assert dados[0]["disciplina"] == "Matemática"
    assert dados[0]["nota"] == "17.5"


def test_home_carrega_agendamentos_salvos(monkeypatch, tmp_path):
    arquivo = tmp_path / "agendamentos.json"
    arquivo.write_text(
        json.dumps([
            {"nome": "Pedro", "ano": "8.º Ano", "disciplina": "Português", "data": "2026-10-22", "nota": "15"}
        ]),
        encoding="utf-8",
    )
    monkeypatch.setenv("AGENDAMENTOS_FILE", str(arquivo))
    monkeypatch.setenv("USERS_FILE", str(tmp_path / "users.json"))

    import app as app_module
    importlib.reload(app_module)

    client = app_module.app.test_client()
    client.post("/login", data={"username": "admin", "password": "admin123"})
    response = client.get("/")

    assert response.status_code == 200
    assert b"Pedro" in response.data
    assert b"Portugu\xc3\xaas" in response.data
    assert b"15" in response.data


def test_exporta_historico_por_aluno(monkeypatch, tmp_path):
    arquivo = tmp_path / "agendamentos.json"
    arquivo.write_text(
        json.dumps([
            {"nome": "Pedro", "ano": "8.º Ano", "disciplina": "Português", "data": "2026-10-22", "nota": "15"},
            {"nome": "Ana", "ano": "9.º Ano", "disciplina": "Matemática", "data": "2026-10-24", "nota": "17"},
        ]),
        encoding="utf-8",
    )
    monkeypatch.setenv("AGENDAMENTOS_FILE", str(arquivo))
    monkeypatch.setenv("USERS_FILE", str(tmp_path / "users.json"))

    import app as app_module
    importlib.reload(app_module)

    client = app_module.app.test_client()
    client.post("/login", data={"username": "admin", "password": "admin123"})
    response = client.get("/exportar-historico?aluno=Pedro")

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/csv")
    assert b"Pedro" in response.data
    assert b"15" in response.data
    assert b"Ana" not in response.data


def test_login_sucesso(monkeypatch, tmp_path):
    arquivo = tmp_path / "agendamentos.json"
    monkeypatch.setenv("AGENDAMENTOS_FILE", str(arquivo))
    monkeypatch.setenv("USERS_FILE", str(tmp_path / "users.json"))
    monkeypatch.setenv("APP_USERNAME", "prof")
    monkeypatch.setenv("APP_PASSWORD", "secret")

    import app as app_module
    importlib.reload(app_module)

    client = app_module.app.test_client()
    response = client.post("/login", data={"username": "prof", "password": "secret"}, follow_redirects=True)

    assert response.status_code == 200
    assert b"Testes Registados" in response.data


def test_logon_cria_utilizador(monkeypatch, tmp_path):
    arquivo = tmp_path / "agendamentos.json"
    monkeypatch.setenv("AGENDAMENTOS_FILE", str(arquivo))
    monkeypatch.setenv("USERS_FILE", str(tmp_path / "users.json"))
    monkeypatch.setenv("APP_USERNAME", "prof")
    monkeypatch.setenv("APP_PASSWORD", "secret")

    import app as app_module
    importlib.reload(app_module)

    client = app_module.app.test_client()
    response = client.post("/logon", data={"username": "novo", "password": "1234"}, follow_redirects=True)

    assert response.status_code == 200
    assert b"Conta criada com sucesso" in response.data


def test_login_falha_redireciona_para_login(monkeypatch, tmp_path):
    arquivo = tmp_path / "agendamentos.json"
    monkeypatch.setenv("AGENDAMENTOS_FILE", str(arquivo))
    monkeypatch.setenv("USERS_FILE", str(tmp_path / "users.json"))
    monkeypatch.setenv("APP_USERNAME", "prof")
    monkeypatch.setenv("APP_PASSWORD", "secret")

    import app as app_module
    importlib.reload(app_module)

    client = app_module.app.test_client()
    response = client.get("/login")

    assert response.status_code == 200
    assert b"Login" in response.data


def test_login_padrao_nao_existe_sem_credenciais_configuradas(monkeypatch, tmp_path):
    monkeypatch.setenv("USERS_FILE", str(tmp_path / "users.json"))
    monkeypatch.delenv("APP_USERNAME")
    monkeypatch.delenv("APP_PASSWORD")

    import app as app_module
    importlib.reload(app_module)

    assert not app_module.autenticar_usuario("admin", "admin123")


def test_utilizador_ve_so_os_seus_testes(monkeypatch, tmp_path):
    arquivo = tmp_path / "agendamentos.json"
    arquivo.write_text(
        json.dumps([
            {"nome": "Pedro", "ano": "8.º Ano", "disciplina": "Português", "data": "2026-10-22", "nota": "15", "usuario": "pedro"},
            {"nome": "Ana", "ano": "9.º Ano", "disciplina": "Matemática", "data": "2026-10-24", "nota": "17", "usuario": "ana"},
        ]),
        encoding="utf-8",
    )
    users_file = tmp_path / "users.json"
    users_file.write_text(
        json.dumps([
            {"username": "ana", "password": "123", "role": "aluno"},
        ]),
        encoding="utf-8",
    )
    monkeypatch.setenv("AGENDAMENTOS_FILE", str(arquivo))
    monkeypatch.setenv("USERS_FILE", str(users_file))
    monkeypatch.setenv("APP_USERNAME", "ana")
    monkeypatch.setenv("APP_PASSWORD", "123")

    import app as app_module
    importlib.reload(app_module)

    client = app_module.app.test_client()
    client.post("/login", data={"username": "ana", "password": "123"})
    response = client.get("/")

    assert response.status_code == 200
    assert b"Ana" in response.data
    assert b"Pedro" not in response.data


def test_professor_pode_aceder_gestao_utilizadores(monkeypatch, tmp_path):
    users_file = tmp_path / "users.json"
    users_file.write_text(
        json.dumps([
            {"username": "prof", "password": "secret", "role": "professor"},
            {"username": "ana", "password": "123", "role": "aluno"},
        ]),
        encoding="utf-8",
    )
    monkeypatch.setenv("AGENDAMENTOS_FILE", str(tmp_path / "agendamentos.json"))
    monkeypatch.setenv("USERS_FILE", str(users_file))
    monkeypatch.setenv("APP_USERNAME", "prof")
    monkeypatch.setenv("APP_PASSWORD", "secret")

    import app as app_module
    importlib.reload(app_module)

    client = app_module.app.test_client()
    client.post("/login", data={"username": "prof", "password": "secret"})
    response = client.get("/gestao-utilizadores")

    assert response.status_code == 200
    assert b"Gestao de Utilizadores" in response.data
    assert b"ana" in response.data


def test_aluno_nao_pode_aceder_gestao_utilizadores(monkeypatch, tmp_path):
    users_file = tmp_path / "users.json"
    users_file.write_text(
        json.dumps([
            {"username": "ana", "password": "123", "role": "aluno"},
        ]),
        encoding="utf-8",
    )
    monkeypatch.setenv("AGENDAMENTOS_FILE", str(tmp_path / "agendamentos.json"))
    monkeypatch.setenv("USERS_FILE", str(users_file))
    monkeypatch.setenv("APP_USERNAME", "prof")
    monkeypatch.setenv("APP_PASSWORD", "secret")

    import app as app_module
    importlib.reload(app_module)

    client = app_module.app.test_client()
    client.post("/login", data={"username": "ana", "password": "123"})
    response = client.get("/gestao-utilizadores", follow_redirects=True)

    assert response.status_code == 200
    assert b"Gestao de Utilizadores" not in response.data
    assert b"Testes Registados" in response.data
