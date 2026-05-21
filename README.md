
## Estructura del proyecto

## TODO: Limpiar readme

```
project/
├── app.py
├── requirements.txt
├── routes/
│   ├── __init__.py
│   ├── auth.py          # Login y registro
│   └── protected.py     # Rutas protegidas con JWT
└── utils/
    ├── __init__.py
    └── jwt_helper.py    # Generación y validación de tokens
```

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecutar el servidor

```bash
python app.py
```

## Endpoints

### Públicos

| Método | Ruta             | Descripción         |
|--------|------------------|---------------------|
| GET    | `/`              | Health check        |
| POST   | `/auth/register` | Registrar usuario   |
| POST   | `/auth/login`    | Login → devuelve token |

### Protegidos (requieren `Authorization: Bearer <token>`)

| Método | Ruta          | Descripción              |
|--------|---------------|--------------------------|
| GET    | `/api/perfil` | Retorna datos del usuario |

## Ejemplo de uso

### Registrar usuario
```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "1234"}'
```

### Login
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "1234"}'
```

### Usar ruta protegida
```bash
curl http://localhost:5000/api/perfil \
  -H "Authorization: Bearer <tu_token>"
```

## Kv Store library install

Build kv store library and copy to kv store service folder 

poetry build -P src/libs/kv_store_lib
mv src/libs/kv_store_lib/dist/* src/kv_store/dist
rm -d src/libs/kv_store_lib/dist

## Run KV Store

cd src/kv_store
python -m venv .venv
source .venv/bin/activate
poetry install
start_kv_store

## Id generator library install
cd src/libs/id_generator_lib
python -m venv .venv
source .venv/bin/activate
poetry build
cd ../../..
mv src/libs/id_generator_lib/dist/* src/id_generator/dist

## Run Id generator
cd src/id_generator
python -m venv .venv
poetry install
run_id_generator

## Run Coordinator instance
python -m venv .venv
source .venv/bin/activate
poetry install
start_coordinator

