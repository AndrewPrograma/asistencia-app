from flask import Flask, request, render_template, jsonify
from datetime import datetime
import math
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

LAT_REF = -16.365188331949714
LON_REF = -71.56534757186213
RANGO = 50

USUARIOS = {
    "Dennys Patiño Garay": "Talento Humano",
    "Mary Jose Cahuana Mamani": "Talento Humano",
    "Sandra Nicolle Yucra Aquije": "Talento Humano",
    "Stefany Estrella Condori Navarro": "Talento Humano",

    "Joysy Karla Serrano Mendoza": "Tecnologías de la Información",
    "Patricia Alejandra Condori Miranda": "Tecnologías de la Información",
    "Roberto Junior": "Tecnologías de la Información",

    "Diago Andrei Pari Ccolloccollo": "Proyectos",
    "Meliza Briyith Herrera Quispe": "Proyectos",

    "Dariela Ivon Laura Quispe": "Marketing",
    "Juan Jesús Valentino": "Marketing",
    "Junior Gonzalo Totocayo Ccasa": "Marketing",
    "Luz Daniela": "Marketing",
    "Maricielo Choque Chancolla": "Marketing",
    "Sharon Gabriela Sulla Cocoyori": "Marketing",

    "Cayo Fernando Chañe Cruz": "Relaciones Públicas",
    "Dante Cristian Velasquez Mamani": "Relaciones Públicas",
    "Henry David Chavez Belizario": "Relaciones Públicas",

    "Emilia Melani Huanco Mamani": "Logística",
    "Huamani Almanacin Jean Kenji": "Logística",
    "Jamil Alexis Mestas Inquilla": "Logística",
    "Jesus Daniel Sopo Arones": "Logística",
    "Sofía Brushesca Lopez Condori": "Logística",

    "Marco Jhoel Palomino Escobedo": "Seguridad",
    "Miguel Augusto Cabana Aguilar": "Seguridad"
}

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

if "GOOGLE_CREDENTIALS" in os.environ:
    credenciales_json = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credenciales_json, scope)
else:
    creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)

client = gspread.authorize(creds)
sheet = client.open("Asistencia").sheet1


def distancia(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@app.route("/usuarios")
def usuarios():
    return jsonify(USUARIOS)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/", methods=["POST"])
def registrar():
    data = request.get_json()

    nombre = data["nombre"]
    lat = data["lat"]
    lon = data["lon"]

    if nombre not in USUARIOS:
        return "❌ Usuario no válido"

    area = USUARIOS[nombre]

    dist = distancia(lat, lon, LAT_REF, LON_REF)
    estado = "Dentro" if dist <= RANGO else "Fuera"

    ahora = datetime.now()
    fecha = ahora.strftime("%d/%m/%Y")
    hora = ahora.strftime("%H:%M")

    registros = sheet.get_all_values()

    for fila in registros:
        if fila and fila[0] == nombre and fila[2] == fecha:
            return "⚠ Ya registraste hoy"

    sheet.append_row([
        nombre, area, fecha, hora, lat, lon, round(dist,2), estado
    ])

    return f"✅ {nombre} ({area}) registrado ({estado})"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)