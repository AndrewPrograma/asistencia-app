from flask import Flask, request, render_template_string
import pandas as pd
from datetime import datetime
import math
import os

app = Flask(__name__)

# 📍 CAMBIA ESTO POR TU UBICACIÓN REAL
LAT_REF = -16.4090
LON_REF = -71.5375
RANGO = 50  # metros

def distancia(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

html = """
<h2>Registro de Asistencia</h2>

<input id="nombre" placeholder="Tu nombre"><br><br>

<button onclick="registrar()">Registrar asistencia</button>

<script>
function registrar(){
    navigator.geolocation.getCurrentPosition(
        function(pos){
            fetch("/", {
                method:"POST",
                headers:{"Content-Type":"application/json"},
                body: JSON.stringify({
                    nombre: document.getElementById("nombre").value,
                    lat: pos.coords.latitude,
                    lon: pos.coords.longitude
                })
            })
            .then(r=>r.text())
            .then(alert)
        },
        function(error){
            alert("Debes permitir la ubicación");
        }
    );
}
</script>
"""

@app.route("/", methods=["GET","POST"])
def home():
    if request.method == "POST":
        data = request.get_json()

        nombre = data["nombre"]
        lat = data["lat"]
        lon = data["lon"]

        dist = distancia(lat, lon, LAT_REF, LON_REF)
        estado = "Dentro" if dist <= RANGO else "Fuera"

        ahora = datetime.now()
        fecha = ahora.strftime("%d/%m/%Y")
        hora = ahora.strftime("%H:%M")

        try:
            df = pd.read_excel("asistencia.xlsx")
        except:
            df = pd.DataFrame(columns=["Nombre","Fecha","Hora","Lat","Lon","Distancia","Estado"])

        # evitar duplicados
        if ((df["Nombre"] == nombre) & (df["Fecha"] == fecha)).any():
            return "⚠ Ya registraste hoy"

        nuevo = pd.DataFrame([[nombre, fecha, hora, lat, lon, round(dist,2), estado]],
                             columns=df.columns)

        df = pd.concat([df, nuevo], ignore_index=True)
        df.to_excel("asistencia.xlsx", index=False)

        return f"✅ {nombre} registrado ({estado})"

    return render_template_string(html)

# 🔥 ESTO ES CLAVE PARA RENDER
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))