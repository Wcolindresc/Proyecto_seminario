
# La Bodegona (Flask)

Catálogo con Flask + Supabase (DB y Storage). Incluye panel admin para subir/reemplazar/eliminar imágenes.

## Local
```
cp .env.example .env
# Rellena SUPABASE_URL y SUPABASE_ANON_KEY
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py  # http://127.0.0.1:5000
```

## Render
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app`
- Env: SUPABASE_URL, SUPABASE_ANON_KEY, SECRET_KEY

## SQL (Supabase)
Ver README original del proyecto para admins y policies del bucket `products`.
