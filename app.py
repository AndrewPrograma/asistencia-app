from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_dance.contrib.google import make_google_blueprint, google
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
from zoneinfo import ZoneInfo
import math
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_proto=1,
    x_host=1
)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "cambiar-esta-clave")

# =========================================================
# GOOGLE LOGIN
# =========================================================

blueprint = make_google_blueprint(
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    scope=["openid", "profile", "email"],
    redirect_url="https://asistencia-app-z8ex.onrender.com/login/google/authorized"
)

app.register_blueprint(blueprint, url_prefix="/login")


# =========================================================
# CONFIGURACIÓN
# =========================================================

LAT_REF = -16.365188331949714
LON_REF = -71.56534757186213

# Radio permitido en metros
RANGO = 70

# Zona horaria de Perú
PERU_TZ = ZoneInfo("America/Lima")


# =========================================================
# USUARIOS Y ÁREAS
# =========================================================

USUARIOS = {
    "apaccaya@unsa.edu.pe": "Directiva",
    "maquiseti@unsa.edu.pe": "Directiva",

    "jphocco@unsa.edu.pe": "Asesor",

    "achaucha@unsa.edu.pe": "Tecnologías de la Información",
    "jserrano@unsa.edu.pe": "Tecnologías de la Información",
    "pcondorim@unsa.edu.pe": "Tecnologías de la Información",
    "rccahuay@unsa.edu.pe": "Tecnologías de la Información",

    "overaa@unsa.edu.pe": "Proyectos",
    "dparicc@unsa.edu.pe": "Proyectos",
    "mherreraq@unsa.edu.pe": "Proyectos",

    "jleon@unsa.edu.pe": "Talento Humano",
    "dpatinog@unsa.edu.pe": "Talento Humano",
    "mcahuanama@unsa.edu.pe": "Talento Humano",
    "syucara@unsa.edu.pe": "Talento Humano",
    "scondorina@unsa.edu.pe": "Talento Humano",

    "cquispeab@unsa.edu.pe": "Marketing",
    "dlauraqu@unsa.edu.pe": "Marketing",
    "jramosflores@unsa.edu.pe": "Marketing",
    "jtotocayo@unsa.edu.pe": "Marketing",
    "lchuraco@unsa.edu.pe": "Marketing",
    "mchoquechan@unsa.edu.pe": "Marketing",
    "ssullac@unsa.edu.pe": "Marketing",

    "shuaraccalloc@unsa.edu.pe": "Relaciones Públicas",
    "cchane@unsa.edu.pe": "Relaciones Públicas",
    "dvelasquezm@unsa.edu.pe": "Relaciones Públicas",
    "hchavezbe@unsa.edu.pe": "Relaciones Públicas",

    "azegarracas@unsa.edu.pe": "Logística",
    "ehuancco@unsa.edu.pe": "Logística",
    "jhuamani@unsa.edu.pe": "Logística",
    "jmestasi@unsa.edu.pe": "Logística",
    "jsopo@unsa.edu.pe": "Logística",
    "slopeco@unsa.edu.pe": "Logística",

    "lcondoricac@unsa.edu.pe": "Seguridad",
    "mpalominoe@unsa.edu.pe": "Seguridad",
    "mcabanaa@unsa.edu.pe": "Seguridad"
}


# =========================================================
# GOOGLE SHEETS
# =========================================================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

if "GOOGLE_CREDENTIALS" in os.environ:

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        json.loads(os.environ["GOOGLE_CREDENTIALS"]),
        scope
    )

else:

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "credenciales.json",
        scope
    )

client = gspread.authorize(creds)

sheet = client.open("Asistencia").sheet1


# =========================================================
# DISTANCIA GPS
# =========================================================

def distancia(lat1, lon1, lat2, lon2):

    R = 6371000

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        +
        math.cos(phi1)
        * math.cos(phi2)
        * math.sin(dlambda / 2) ** 2
    )

    return 2 * R * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )


# =========================================================
# OBTENER USUARIO ACTUAL
# =========================================================

def obtener_usuario():

    if not google.authorized:
        return None

    try:

        resp = google.get("/oauth2/v2/userinfo")

        if not resp.ok:
            return None

        datos = resp.json()

        email = datos.get("email", "").lower()

        if not email.endswith("@unsa.edu.pe"):
            return None

        if email not in USUARIOS:
            return None

        nombre = datos.get("name", email)

        area = USUARIOS[email]

        return {
            "email": email,
            "nombre": nombre,
            "area": area
        }

    except Exception:
        return None


# =========================================================
# PÁGINA PRINCIPAL
# =========================================================

@app.route("/")
def index():

    if not google.authorized:
        return redirect(url_for("google.login"))

    usuario = obtener_usuario()

    if not usuario:
        return """
        <h2>❌ Acceso no autorizado</h2>
        <p>Debes utilizar un correo institucional autorizado de @unsa.edu.pe.</p>
        """

    return render_template(
        "index.html",
        usuario=usuario
    )


# =========================================================
# ESTADO ACTUAL DEL USUARIO
# =========================================================

@app.route("/estado", methods=["GET"])
def estado():

    usuario = obtener_usuario()

    if not usuario:
        return jsonify({
            "ok": False,
            "mensaje": "Usuario no autorizado"
        }), 401

    registros = sheet.get_all_values()

    ahora = datetime.now(PERU_TZ)

    fecha = ahora.strftime("%d/%m/%Y")

    ultimo = None

    for fila in reversed(registros):

        if (
            len(fila) >= 5
            and fila[0].lower() == usuario["email"]
            and fila[2] == fecha
        ):

            ultimo = fila
            break

    if not ultimo:

        return jsonify({
            "ok": True,
            "estado": "Fuera",
            "tipo": None
        })

    return jsonify({
        "ok": True,
        "estado": "Dentro" if ultimo[4] == "Ingreso" else "Fuera",
        "tipo": ultimo[4],
        "hora": ultimo[3]
    })


# =========================================================
# REGISTRAR INGRESO / SALIDA
# =========================================================

@app.route("/registrar", methods=["POST"])
def registrar():

    usuario = obtener_usuario()

    if not usuario:

        return jsonify({
            "ok": False,
            "mensaje": "❌ Usuario no autorizado"
        }), 401

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "ok": False,
            "mensaje": "❌ No se recibieron datos"
        }), 400

    lat = data.get("lat")
    lon = data.get("lon")
    tipo = data.get("tipo")

    if lat is None or lon is None or not tipo:

        return jsonify({
            "ok": False,
            "mensaje": "❌ Datos incompletos"
        }), 400

    if tipo not in ["Ingreso", "Salida"]:

        return jsonify({
            "ok": False,
            "mensaje": "❌ Tipo de registro inválido"
        }), 400

    try:

        lat = float(lat)
        lon = float(lon)

    except ValueError:

        return jsonify({
            "ok": False,
            "mensaje": "❌ Coordenadas inválidas"
        }), 400


    # =====================================================
    # DISTANCIA
    # =====================================================

    dist = distancia(
        lat,
        lon,
        LAT_REF,
        LON_REF
    )

    estado_ubicacion = (
        "Dentro"
        if dist <= RANGO
        else "Fuera"
    )


    # =====================================================
    # FECHA Y HORA DE PERÚ
    # =====================================================

    ahora = datetime.now(PERU_TZ)

    fecha = ahora.strftime("%d/%m/%Y")
    hora = ahora.strftime("%H:%M:%S")


    # =====================================================
    # REVISAR ÚLTIMO REGISTRO
    # =====================================================

    registros = sheet.get_all_values()

    ultimo = None

    for fila in reversed(registros):

        if (
            len(fila) >= 5
            and fila[0].lower() == usuario["email"]
            and fila[2] == fecha
        ):

            ultimo = fila
            break


    if ultimo:

        ultimo_tipo = ultimo[4]

        # Ya registró ingreso
        if tipo == "Ingreso" and ultimo_tipo == "Ingreso":

            return jsonify({
                "ok": False,
                "mensaje": "⚠️ Ya tienes un ingreso registrado.",
                "tipo": "duplicado"
            }), 400

        # Ya registró salida
        if tipo == "Salida" and ultimo_tipo == "Salida":

            return jsonify({
                "ok": False,
                "mensaje": "⚠️ Ya tienes una salida registrada.",
                "tipo": "duplicado"
            }), 400


    # =====================================================
    # GUARDAR
    # =====================================================

    sheet.append_row([
        usuario["email"],
        usuario["area"],
        fecha,
        hora,
        tipo,
        lat,
        lon,
        round(dist, 2),
        estado_ubicacion
    ])


    mensaje = (
        f"✅ {tipo} registrado correctamente"
    )

    return jsonify({
        "ok": True,
        "mensaje": mensaje,
        "tipo": tipo,
        "hora": hora,
        "ubicacion": estado_ubicacion,
        "distancia": round(dist, 2)
    })


# =========================================================
# CERRAR SESIÓN
# =========================================================

@app.route("/logout")
def logout():

    return redirect(url_for("google.logout"))


# =========================================================
# EJECUCIÓN
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
