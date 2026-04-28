from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_dance.contrib.google import make_google_blueprint, google
from datetime import datetime
import math
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
app.secret_key = "supersecretkey"

# 🔐 GOOGLE LOGIN
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

blueprint = make_google_blueprint(
    client_id="TU_CLIENT_ID",
    client_secret="TU_CLIENT_SECRET",
    scope=["profile", "email"]
)
app.register_blueprint(blueprint, url_prefix="/login")

# 📍 UBICACIÓN
LAT_REF = -16.365188331949714
LON_REF = -71.56534757186213
RANGO = 70

# 👥 ÁREAS POR EMAIL
USUARIOS = {
    "andrew@tuinstitucion.edu.pe": "Tecnologías de la Información",
    # agrega los demás correos aquí
}

# 📊 GOOGLE SHEETS
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

if "GOOGLE_CREDENTIALS" in os.environ:
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        json.loads(os.environ["GOOGLE_CREDENTIALS"]), scope)
else:
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "credenciales.json", scope)

client = gspread.authorize(creds)
sheet = client.open("Asistencia").sheet1

# 📏 DISTANCIA
def distancia(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# 🔐 LOGIN
@app.route("/")
def index():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    email = resp.json()["email"]

    if not email.endswith("@tuinstitucion.edu.pe"):
        return "❌ Usa tu correo institucional"

    return render_template("index.html", email=email)

# 📌 REGISTRO
@app.route("/registrar", methods=["POST"])
def registrar():
    if not google.authorized:
        return "No autorizado"

    resp = google.get("/oauth2/v2/userinfo")
    email = resp.json()["email"]

    if email not in USUARIOS:
        return "❌ Usuario no registrado"

    data = request.get_json()

    lat = data.get("lat")
    lon = data.get("lon")
    tipo = data.get("tipo")  # Ingreso o Salida

    if not lat or not lon or not tipo:
        return "❌ Datos incompletos"

    area = USUARIOS[email]

    dist = distancia(lat, lon, LAT_REF, LON_REF)
    estado = "Dentro" if dist <= RANGO else "Fuera"

    ahora = datetime.now()
    fecha = ahora.strftime("%d/%m/%Y")
    hora = ahora.strftime("%H:%M")

    registros = sheet.get_all_values()

    # 🔁 VALIDAR ÚLTIMO REGISTRO
    ultimo = None
    for fila in reversed(registros):
        if fila and fila[0] == email and fila[2] == fecha:
            ultimo = fila
            break

    if ultimo:
        ultimo_tipo = ultimo[4]

        if tipo == "Ingreso" and ultimo_tipo == "Ingreso":
            return "⚠ Ya estás dentro"

        if tipo == "Salida" and ultimo_tipo == "Salida":
            return "⚠ Ya estás fuera"

    # 📊 GUARDAR
    sheet.append_row([
        email, area, fecha, hora, tipo, lat, lon, round(dist, 2), estado
    ])

    return f"✅ {tipo} registrado ({estado})"

if __name__ == "__main__":
    app.run(debug=True)
