fetch("/usuarios")
.then(res => res.json())
.then(data => {
    const select = document.getElementById("nombre")

    Object.keys(data).forEach(nombre => {
        const option = document.createElement("option")
        option.value = nombre
        option.textContent = nombre + " (" + data[nombre] + ")"
        select.appendChild(option)
    })
})

function registrar(){
    let nombre = document.getElementById("nombre").value

    if(nombre === ""){
        alert("Selecciona tu nombre")
        return
    }

    navigator.geolocation.getCurrentPosition(pos=>{
        fetch("/",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({
                nombre:nombre,
                lat:pos.coords.latitude,
                lon:pos.coords.longitude
            })
        })
        .then(r=>r.text())
        .then(msg=>{
            document.getElementById("mensaje").innerText = msg
        })
    })
}