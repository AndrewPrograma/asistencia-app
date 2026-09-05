let procesando = false;


// =====================================================
// REGISTRAR
// =====================================================

function registrar(tipo) {

    if (procesando) {
        return;
    }

    procesando = true;

    const mensaje = document.getElementById("mensaje");

    mensaje.className = "mensaje cargando";

    mensaje.innerText =
        "📍 Obteniendo ubicación...";


    if (!navigator.geolocation) {

        mensaje.className = "mensaje error";

        mensaje.innerText =
            "❌ Tu dispositivo no permite obtener ubicación.";

        procesando = false;

        return;
    }


    navigator.geolocation.getCurrentPosition(

        function(position) {

            const lat = position.coords.latitude;
            const lon = position.coords.longitude;


            mensaje.innerText =
                "⏳ Registrando asistencia...";


            fetch("/registrar", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    lat: lat,
                    lon: lon,
                    tipo: tipo

                })

            })

            .then(response => response.json())

            .then(data => {

                if (data.ok) {

                    mensaje.className =
                        "mensaje exito";

                    mensaje.innerText =
                        data.mensaje;


                    document.getElementById(
                        "horaRegistro"
                    ).innerText =
                        "Hora: " + data.hora;


                    if (data.ubicacion === "Dentro") {

                        mensaje.innerText +=
                            " 📍 Dentro del área permitida.";

                    } else {

                        mensaje.innerText +=
                            " ⚠️ Estás fuera del área permitida.";

                    }

                    actualizarEstado();

                } else {

                    mensaje.className =
                        "mensaje error";

                    mensaje.innerText =
                        data.mensaje;

                }

            })

            .catch(error => {

                console.error(error);

                mensaje.className =
                    "mensaje error";

                mensaje.innerText =
                    "❌ Error al comunicarse con el servidor.";

            })

            .finally(() => {

                procesando = false;

            });

        },


        function(error) {

            mensaje.className =
                "mensaje error";


            if (error.code === 1) {

                mensaje.innerText =
                    "❌ Debes permitir el acceso a tu ubicación.";

            }

            else if (error.code === 2) {

                mensaje.innerText =
                    "❌ No se pudo obtener tu ubicación.";

            }

            else if (error.code === 3) {

                mensaje.innerText =
                    "❌ Se agotó el tiempo para obtener tu ubicación.";

            }

            else {

                mensaje.innerText =
                    "❌ Error obteniendo ubicación.";

            }


            procesando = false;

        },

        {

            enableHighAccuracy: true,

            timeout: 15000,

            maximumAge: 0

        }

    );

}


// =====================================================
// CONSULTAR ESTADO
// =====================================================

function actualizarEstado() {

    fetch("/estado")

        .then(response => response.json())

        .then(data => {

            const estado =
                document.getElementById(
                    "estadoTexto"
                );


            const ingreso =
                document.getElementById(
                    "btnIngreso"
                );

            const salida =
                document.getElementById(
                    "btnSalida"
                );


            if (!data.ok) {

                estado.innerText =
                    "Estado desconocido";

                return;

            }


            if (data.estado === "Dentro") {

                estado.innerText =
                    "🟢 Actualmente estás dentro";

                estado.className =
                    "dentro";


                ingreso.disabled = true;

                salida.disabled = false;

            }

            else {

                estado.innerText =
                    "🔴 Actualmente estás fuera";

                estado.className =
                    "fuera";


                ingreso.disabled = false;

                salida.disabled = true;

            }


            if (data.hora) {

                document.getElementById(
                    "horaRegistro"
                ).innerText =
                    "Última marcación: " + data.hora;

            }

        })

        .catch(error => {

            console.error(
                "Error consultando estado:",
                error
            );

        });

}


// =====================================================
// INICIAR
// =====================================================

document.addEventListener(
    "DOMContentLoaded",
    actualizarEstado
);
