import importlib
import json


def test_agendar_salva_no_arquivo(monkeypatch, tmp_path):
    arquivo = tmp_path / "agendamentos.json"
    monkeypatch.setenv("AGENDAMENTOS_FILE", str(arquivo))

    import app as app_module
    importlib.reload(app_module)

    client = app_module.app.test_client()
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

    import app as app_module
    importlib.reload(app_module)

    response = app_module.app.test_client().get("/")

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

    import app as app_module
    importlib.reload(app_module)

    response = app_module.app.test_client().get("/exportar-historico?aluno=Pedro")

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/csv")
    assert b"Pedro" in response.data
    assert b"15" in response.data
    assert b"Ana" not in response.data
