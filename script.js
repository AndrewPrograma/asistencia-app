import * as THREE from "https://cdn.skypack.dev/three@0.132.2";
import { OrbitControls } from "https://cdn.skypack.dev/three@0.132.2/examples/jsm/controls/OrbitControls.js";

// GALAXIA (igual que tu código)
const canvas = document.querySelector('canvas.webgl')
const scene = new THREE.Scene()

const parameters = {
    count: 60000,
    size: 0.015,
    radius: 2,
    branches: 3,
    spin: 2,
    randomness: 2,
    randomnessPower: 3,
    insideColor: '#60a5fa',
    outsideColor: '#1e3a8a'
}

let geometry = new THREE.BufferGeometry()
let material = new THREE.PointsMaterial({
    size: parameters.size,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    vertexColors: true
})

const positions = new Float32Array(parameters.count * 3)
const colors = new Float32Array(parameters.count * 3)

const colorInside = new THREE.Color(parameters.insideColor)
const colorOutside = new THREE.Color(parameters.outsideColor)

for(let i=0;i<parameters.count;i++){
    const i3=i*3
    const radius=Math.random()*parameters.radius
    const spinAngle=radius*parameters.spin
    const branchAngle=((i%parameters.branches)/parameters.branches)*Math.PI*2

    positions[i3]=Math.cos(branchAngle+spinAngle)*radius
    positions[i3+2]=Math.sin(branchAngle+spinAngle)*radius

    const mixedColor=colorInside.clone()
    mixedColor.lerp(colorOutside,radius/parameters.radius)

    colors[i3]=mixedColor.r
    colors[i3+1]=mixedColor.g
    colors[i3+2]=mixedColor.b
}

geometry.setAttribute('position',new THREE.BufferAttribute(positions,3))
geometry.setAttribute('color',new THREE.BufferAttribute(colors,3))

const points=new THREE.Points(geometry,material)
scene.add(points)

const camera=new THREE.PerspectiveCamera(75,window.innerWidth/window.innerHeight,0.1,100)
camera.position.z=3
scene.add(camera)

const renderer=new THREE.WebGLRenderer({canvas:canvas})
renderer.setSize(window.innerWidth,window.innerHeight)

const controls=new OrbitControls(camera,canvas)

function animate(){
    requestAnimationFrame(animate)
    controls.update()
    renderer.render(scene,camera)
}
animate()

// 🔥 REGISTRO
window.registrar = function(){
    let nombre = document.getElementById("nombre").value
    let token = document.getElementById("token").value

    navigator.geolocation.getCurrentPosition(pos=>{
        fetch("/",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({
                nombre:nombre,
                token:token,
                lat:pos.coords.latitude,
                lon:pos.coords.longitude
            })
        })
        .then(r=>r.text())
        .then(msg=>{
            document.getElementById("mensaje").innerText = msg

            document.getElementById("nombre").value=""
            document.getElementById("token").value=""
        })
    })
}