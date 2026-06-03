def test_registrar_persona(client):
    r = client.post("/api/personas", json={"carnet": "A1", "nombre": "Ana"})
    assert r.status_code == 201
    assert r.json()["carnet"] == "A1"


def test_no_duplicar_carnet(client):
    client.post("/api/personas", json={"carnet": "A1"})
    r = client.post("/api/personas", json={"carnet": "A1"})
    assert r.status_code == 409


def test_comprar_sin_registro_falla(client):
    r = client.post("/api/compras", json={"carnet": "NO", "litros": 10})
    assert r.status_code == 409


def test_comprar_una_vez_ok_y_segunda_bloqueada(client):
    client.post("/api/personas", json={"carnet": "A1"})
    r1 = client.post("/api/compras", json={"carnet": "A1", "litros": 20})
    assert r1.status_code == 201
    # Segunda compra dentro de la ventana de 7 días -> bloqueada.
    r2 = client.post("/api/compras", json={"carnet": "A1", "litros": 20})
    assert r2.status_code == 409


def test_estado_carnet(client):
    client.post("/api/personas", json={"carnet": "A1"})
    estado = client.get("/api/personas/A1/estado").json()
    assert estado["puede_comprar"] is True
    client.post("/api/compras", json={"carnet": "A1", "litros": 5})
    estado2 = client.get("/api/personas/A1/estado").json()
    assert estado2["puede_comprar"] is False
    assert estado2["proxima_habilitacion"] is not None


def test_estado_carnet_no_registrado(client):
    estado = client.get("/api/personas/ZZZ/estado").json()
    assert estado["registrado"] is False
    assert estado["puede_comprar"] is False


def test_historial_y_filtro(client):
    client.post("/api/personas", json={"carnet": "A1"})
    client.post("/api/personas", json={"carnet": "B2"})
    client.post("/api/compras", json={"carnet": "A1", "litros": 10})
    client.post("/api/compras", json={"carnet": "B2", "litros": 15})
    todas = client.get("/api/compras").json()
    assert len(todas) == 2
    solo_a1 = client.get("/api/compras?carnet=A1").json()
    assert len(solo_a1) == 1
    assert solo_a1[0]["carnet"] == "A1"


def test_litros_sobre_maximo(client):
    client.post("/api/personas", json={"carnet": "A1"})
    r = client.post("/api/compras", json={"carnet": "A1", "litros": 99999})
    assert r.status_code == 422
