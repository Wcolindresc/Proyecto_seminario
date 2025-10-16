
import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")

app = Flask(__name__)
app.secret_key = SECRET_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
BUCKET = "products"

def public_url(path):
    if not path:
        return None
    data = supabase.storage.from_(BUCKET).get_public_url(path)
    return data.get("publicUrl")

def current_user():
    return session.get("user")

def is_admin(user_id):
    if not user_id:
        return False
    res = supabase.table("admins").select("user_id").eq("user_id", user_id).execute()
    return len(res.data or []) > 0

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user():
            flash("Debes iniciar sesión.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            flash("Debes iniciar sesión.", "warning")
            return redirect(url_for("login", next=request.path))
        if not is_admin(user.get("id")):
            flash("No autorizado.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper

@app.get("/")
def index():
    res = supabase.table("products").select("id,name,slug,price,stock,image_path").order("name").execute()
    products = res.data or []
    for p in products:
        p["image_url"] = public_url(p.get("image_path"))
    return render_template("index.html", products=products, user=current_user())

@app.get("/login")
def login():
    return render_template("login.html")

@app.post("/login")
def login_post():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    try:
        auth_res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        user = auth_res.user
        if not user:
            flash("Credenciales inválidas", "danger")
            return redirect(url_for("login"))
        session["user"] = {"id": user.id, "email": email}
        flash("Bienvenido.", "success")
        nxt = request.args.get("next") or url_for("index")
        return redirect(nxt)
    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for("login"))

@app.post("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("index"))

@app.get("/admin/upload-image")
@admin_required
def admin_upload_image():
    res = supabase.table("products").select("id,name,slug,image_path").order("name").execute()
    products = res.data or []
    for p in products:
        p["image_url"] = public_url(p.get("image_path"))
    return render_template("admin_upload.html", products=products)

@app.post("/admin/upload-image")
@admin_required
def admin_upload_image_post():
    product_id = request.form.get("product_id")
    file = request.files.get("file")
    if not product_id or not file:
        flash("Selecciona un producto y un archivo.", "warning")
        return redirect(url_for("admin_upload_image"))
    prod = supabase.table("products").select("slug").eq("id", product_id).single().execute().data
    if not prod:
        flash("Producto no encontrado.", "danger")
        return redirect(url_for("admin_upload_image"))
    slug = prod["slug"]
    ext = (file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg").lower()
    path = f"products/{slug}.{ext}"
    try:
        supabase.storage.from_(BUCKET).remove([path])
    except Exception:
        pass
    supabase.storage.from_(BUCKET).upload(path, file.stream, file_options={"cacheControl": "3600", "upsert": True})
    supabase.table("products").update({"image_path": path}).eq("id", product_id).execute()
    flash("Imagen actualizada ✅", "success")
    return redirect(url_for("admin_upload_image"))

@app.post("/admin/delete-image")
@admin_required
def admin_delete_image():
    product_id = request.form.get("product_id")
    prod = supabase.table("products").select("slug").eq("id", product_id).single().execute().data
    if not prod:
        flash("Producto no encontrado.", "danger")
        return redirect(url_for("admin_upload_image"))
    slug = prod["slug"]
    for ext in ["jpg","jpeg","png","webp","gif","avif"]:
        path = f"products/{slug}.{ext}"
        try:
            supabase.storage.from_(BUCKET).remove([path])
        except Exception:
            pass
    supabase.table("products").update({"image_path": None}).eq("id", product_id).execute()
    flash("Imagen eliminada ✅", "info")
    return redirect(url_for("admin_upload_image"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
