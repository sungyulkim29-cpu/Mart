import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="마트에서 살아남기", page_icon="🛒", layout="wide")

GAME_HTML = r"""
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>마트에서 살아남기</title>
<style>
html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#050505;font-family:Arial,sans-serif}
#game{position:fixed;inset:0}
#hud{position:fixed;left:12px;top:10px;color:#fff;z-index:5;text-shadow:0 2px 4px #000;font-size:14px;line-height:1.5}
#message{position:fixed;left:50%;bottom:10%;transform:translateX(-50%);z-index:6;color:white;background:#000b;padding:10px 16px;border-radius:10px;display:none;text-align:center}
#crosshair{position:fixed;left:50%;top:50%;width:8px;height:8px;margin:-4px;border:1px solid #fff;border-radius:50%;z-index:4;opacity:.8}
#joystick{display:none;position:fixed;left:22px;bottom:24px;width:120px;height:120px;border-radius:50%;background:#ffffff22;border:2px solid #ffffff55;z-index:10;touch-action:none}
#stick{position:absolute;left:35px;top:35px;width:50px;height:50px;border-radius:50%;background:#ffffff66}
#look{display:none;position:fixed;right:0;top:0;width:62%;height:100%;z-index:2;touch-action:none}
#interact{display:none;position:fixed;right:22px;bottom:34px;width:78px;height:78px;border-radius:50%;border:2px solid #fff8;background:#111b;color:#fff;z-index:10}
#start{position:fixed;inset:0;background:#070707ee;color:#fff;z-index:20;display:flex;align-items:center;justify-content:center;text-align:center;padding:25px}
#start button{font-size:18px;padding:13px 25px;border:0;border-radius:10px;cursor:pointer}
.small{opacity:.75;font-size:12px}
</style>
</head>
<body>
<div id="game"></div>
<div id="hud">
<b>🛒 마트에서 살아남기</b><br>
층: <span id="floor">1</span> / 3　|　힌트: <span id="hints">0</span> / 5<br>
목표: 각 층의 5개 힌트를 찾고 비밀번호를 입력하세요.
</div>
<div id="crosshair"></div>
<div id="message"></div>
<div id="joystick"><div id="stick"></div></div>
<div id="look"></div>
<button id="interact">확인</button>
<div id="start">
<div>
<h1>마트에서 살아남기</h1>
<p>3층짜리 폐마트에서 괴물을 피해 탈출하세요.</p>
<p>PC: <b>WASD</b> 이동 · 마우스 시점<br>모바일: <b>왼쪽 조이스틱</b> 이동 · 오른쪽 화면 드래그로 시점</p>
<p>점프는 없습니다. 괴물에게 들키면 가까운 <b>숨을 공간</b>으로 도망가세요.</p>
<button id="startBtn">게임 시작</button>
<p class="small">브라우저에서 실행되는 Three.js 3D 프로토타입</p>
</div>
</div>

<script type="module">
import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js";

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x090b0d);
scene.fog = new THREE.Fog(0x090b0d, 12, 65);

const camera = new THREE.PerspectiveCamera(72, innerWidth/innerHeight, .05, 100);
camera.position.set(0,1.7,7);

const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(innerWidth,innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.shadowMap.enabled=true;
document.getElementById("game").appendChild(renderer.domElement);

scene.add(new THREE.HemisphereLight(0x8899aa,0x111111,1.1));
const light = new THREE.DirectionalLight(0xffffff,1.1);
light.position.set(8,12,5); light.castShadow=true; scene.add(light);

const floors=[];
const floorGroups=[];
let currentFloor=0;
let collected=0;
const password=[["○","□","♤","♧"],["○","□","♤","♧"],["○","□","♤","♧"]];
const symbols=[
  {s:"○",c:0x2878ff,n:"파랑"},
  {s:"□",c:0xe33b3b,n:"빨강"},
  {s:"♤",c:0xffd21f,n:"노랑"},
  {s:"♧",c:0x31c96b,n:"초록"}
];

function mat(c,rough=.8){return new THREE.MeshStandardMaterial({color:c,roughness:rough});}
function box(x,y,z,sx,sy,sz,c=0x555555){
 const m=new THREE.Mesh(new THREE.BoxGeometry(sx,sy,sz),mat(c));
 m.position.set(x,y,z); m.castShadow=true; m.receiveShadow=true; return m;
}
function textSprite(text,color="#fff"){
 const can=document.createElement("canvas"); can.width=256; can.height=128;
 const ctx=can.getContext("2d"); ctx.fillStyle="rgba(0,0,0,.78)"; ctx.fillRect(0,0,256,128);
 ctx.fillStyle=color; ctx.font="bold 70px Arial"; ctx.textAlign="center"; ctx.textBaseline="middle"; ctx.fillText(text,128,64);
 const tex=new THREE.CanvasTexture(can);
 const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:tex,transparent:true}));
 sp.scale.set(1.8,.9,1); return sp;
}

const hints=[];
const hides=[];
const stairs=[];

function buildFloor(fi){
 const g=new THREE.Group(); g.visible=(fi===0); scene.add(g); floorGroups.push(g);
 // floor
 g.add(box(0,-.15,0,36,.3,36,0x3a3a3a));
 // walls
 g.add(box(0,2,-18,36,4,.3,0x22252a));
 g.add(box(0,2,18,36,4,.3,0x22252a));
 g.add(box(-18,2,0,.3,4,36,0x22252a));
 g.add(box(18,2,0,.3,4,36,0x22252a));
 // ceiling beams
 for(let x=-15;x<=15;x+=6) g.add(box(x,4.2,0,.35,.35,34,0x15171a));
 // shelves/aisles
 for(let x=-12;x<=12;x+=6){
   for(let z=-12;z<=12;z+=6){
     if(Math.abs(x)<2 && Math.abs(z)<3) continue;
     g.add(box(x,1.2,z,2.5,2.4,1.0,0x5a4637));
     g.add(box(x,2.1,z,2.5,.15,1.0,0x8a6c4c));
   }
 }
 // lights
 for(let x=-12;x<=12;x+=6) for(let z=-12;z<=12;z+=8){
   const pl=new THREE.PointLight(0xfff1cc,1.3,9); pl.position.set(x,3.5,z); g.add(pl);
 }
 // 5 hints, visible objects with labels
 const spots=[[-15,-14],[-9,10],[5,-10],[13,8],[12,-2]];
 spots.forEach((p,i)=>{
   const sym=symbols[i%4];
   const h=box(p[0],.75,p[1],.8,1.5,.8,sym.c);
   h.userData={type:"hint",floor:fi,index:i,symbol:sym.s,color:sym.c};
   g.add(h); hints.push(h);
   const t=textSprite(sym.s,"#ffffff"); t.position.set(p[0],2.2,p[1]); g.add(t);
 });
 // hide spots: boxes with dark interior
 const hs=[[-15,5],[15,12],[-3,-15]];
 hs.forEach((p,i)=>{
   const h=box(p[0],1.3,p[1],2.5,2.6,1.5,0x111318);
   h.userData={type:"hide",floor:fi}; g.add(h); hides.push(h);
   const sign=textSprite("숨기", "#9ad8ff"); sign.position.set(p[0],2.9,p[1]); g.add(sign);
 });
 // staircase / elevator marker
 const st=box(0,1,15,3,2,2,0x6d6d6d); st.userData={type:"stairs",floor:fi}; g.add(st); stairs.push(st);
 const label=textSprite(fi<2?"다음 층":"출구","#fff"); label.position.set(0,2.5,15); g.add(label);
}
for(let i=0;i<3;i++) buildFloor(i);

function makeMonster(){
 const m=new THREE.Group();
 const black=mat(0x030303);
 const body=new THREE.Mesh(new THREE.CapsuleGeometry(.65,1.5,8,16),black);
 body.position.y=1.7; body.scale.set(.75,1.2,.75); body.castShadow=true; m.add(body);
 const head=new THREE.Mesh(new THREE.SphereGeometry(.62,16,12),black); head.position.y=3.15; head.scale.set(.8,1.1,.7); m.add(head);
 // extremely long limbs
 for(const side of [-1,1]){
   const arm=new THREE.Mesh(new THREE.CapsuleGeometry(.18,2.5,6,10),black);
   arm.position.set(side*.9,1.7,0); arm.rotation.z=side*.35; m.add(arm);
   const leg=new THREE.Mesh(new THREE.CapsuleGeometry(.22,3.0,6,10),black);
   leg.position.set(side*.42,-.05,0); leg.rotation.z=side*.08; m.add(leg);
 }
 const eyeMat=mat(0xff2222);
 for(const x of [-.22,.22]){const e=new THREE.Mesh(new THREE.SphereGeometry(.07,8,8),eyeMat);e.position.set(x,3.2,-.55);m.add(e)}
 m.position.set(10,0,10); m.visible=true; scene.add(m); return m;
}
const monster=makeMonster();

const player={pos:new THREE.Vector3(0,1.7,7), yaw:0, pitch:0, speed:4.2, hiding:false};
let monsterState="patrol", alert=0, alive=true;
const keys={};
addEventListener("keydown",e=>keys[e.key.toLowerCase()]=true);
addEventListener("keyup",e=>keys[e.key.toLowerCase()]=false);

let joyX=0,joyY=0;
const joy=document.getElementById("joystick"),stick=document.getElementById("stick"),look=document.getElementById("look");
const mobile=("ontouchstart" in window)||navigator.maxTouchPoints>0;
if(mobile){joy.style.display="block";look.style.display="block";document.getElementById("interact").style.display="block";}

joy.addEventListener("pointerdown",e=>{joy.setPointerCapture(e.pointerId); moveJoy(e)});
joy.addEventListener("pointermove",e=>{if(e.buttons)moveJoy(e)});
joy.addEventListener("pointerup",()=>{joyX=joyY=0;stick.style.left="35px";stick.style.top="35px"});
function moveJoy(e){
 const r=joy.getBoundingClientRect(), dx=e.clientX-(r.left+r.width/2),dy=e.clientY-(r.top+r.height/2);
 const len=Math.min(48,Math.hypot(dx,dy)), a=Math.atan2(dy,dx);
 joyX=Math.cos(a)*len/48; joyY=Math.sin(a)*len/48;
 stick.style.left=(35+joyX*48)+"px";stick.style.top=(35+joyY*48)+"px";
}
let lookDown=false,lastX=0,lastY=0;
look.addEventListener("pointerdown",e=>{look.setPointerCapture(e.pointerId);lookDown=true;lastX=e.clientX;lastY=e.clientY});
look.addEventListener("pointermove",e=>{
 if(!lookDown)return;
 player.yaw-=(e.clientX-lastX)*.004; player.pitch-=(e.clientY-lastY)*.003;
 player.pitch=Math.max(-1.1,Math.min(1.1,player.pitch)); lastX=e.clientX;lastY=e.clientY;
});
look.addEventListener("pointerup",()=>lookDown=false);

document.getElementById("startBtn").onclick=()=>document.getElementById("start").style.display="none";
document.getElementById("interact").onclick=interact;

function msg(t,ms=2200){const el=document.getElementById("message");el.textContent=t;el.style.display="block";clearTimeout(msg.t);msg.t=setTimeout(()=>el.style.display="none",ms)}
function dist(a,b){return a.distanceTo(b)}
function interact(){
 if(!alive)return;
 const pp=new THREE.Vector3(player.pos.x,0,player.pos.z);
 // hints
 for(const h of hints){
   if(!h.visible||h.userData.floor!==currentFloor)continue;
   if(dist(pp,new THREE.Vector3(h.position.x,0,h.position.z))<2.2){
     h.visible=false; collected++; document.getElementById("hints").textContent=collected%5;
     const n=h.userData.index+1;
     msg(`힌트 ${n}: ${h.userData.symbol} (${symbols.find(s=>s.s===h.userData.symbol).n})`);
     return;
   }
 }
 for(const h of hides){
   if(h.userData.floor===currentFloor&&dist(pp,new THREE.Vector3(h.position.x,0,h.position.z))<2.8){
     player.hiding=!player.hiding; msg(player.hiding?"숨었습니다.":"숨는 곳에서 나왔습니다."); return;
   }
 }
 for(const s of stairs){
   if(s.userData.floor===currentFloor&&dist(pp,new THREE.Vector3(s.position.x,0,s.position.z))<3){
     if(currentFloor<2 && collected%5===0 && collected>0){changeFloor(currentFloor+1);return}
     if(currentFloor===2 && collected%5===0 && collected>0){msg("출구가 열렸습니다! 생존 성공!",6000);alive=false;return}
     msg("이 층의 힌트 5개를 먼저 찾아야 합니다.");return;
   }
 }
}
addEventListener("keydown",e=>{if(e.key.toLowerCase()==="e")interact()});
renderer.domElement.addEventListener("click",()=>{
 if(!mobile && document.getElementById("start").style.display==="none") renderer.domElement.requestPointerLock?.();
});
document.addEventListener("mousemove",e=>{
 if(document.pointerLockElement===renderer.domElement){
   player.yaw-=e.movementX*.0025;player.pitch-=e.movementY*.002;
   player.pitch=Math.max(-1.1,Math.min(1.1,player.pitch));
 }
});

function changeFloor(f){
 currentFloor=f;
 floorGroups.forEach((g,i)=>g.visible=i===f);
 player.pos.set(0,1.7,7);
 monster.position.set(10,0,10);
 alert=0;monsterState="patrol";player.hiding=false;
 document.getElementById("floor").textContent=f+1;
 document.getElementById("hints").textContent=0;
 msg(`${f+1}층으로 올라왔습니다. 힌트 5개를 찾으세요.`,3000);
}

function clampPlayer(){
 player.pos.x=Math.max(-16,Math.min(16,player.pos.x));
 player.pos.z=Math.max(-16,Math.min(16,player.pos.z));
}

function move(dt){
 let x=(keys["d"]?1:0)-(keys["a"]?1:0);
 let z=(keys["s"]?1:0)-(keys["w"]?1:0);
 if(mobile){x+=joyX;z+=joyY}
 const l=Math.hypot(x,z); if(l>1){x/=l;z/=l}
 const fwd=new THREE.Vector3(Math.sin(player.yaw),0,-Math.cos(player.yaw));
 const right=new THREE.Vector3(Math.cos(player.yaw),0,Math.sin(player.yaw));
 player.pos.addScaledVector(right,x*player.speed*dt);
 player.pos.addScaledVector(fwd,-z*player.speed*dt);
 clampPlayer();
}

function monsterAI(dt){
 if(!monster.visible)return;
 const mp=monster.position, target=new THREE.Vector3(player.pos.x,0,player.pos.z);
 const d=mp.distanceTo(target);
 if(player.hiding){alert=Math.max(0,alert-dt*1.5);if(d<3) { // monster searches briefly
   monsterState="search"; alert=.8;
 }} else if(d<10){alert+=dt*.9;monsterState="chase"} else {alert=Math.max(0,alert-dt*.2);monsterState="patrol"}
 if(monsterState==="chase"&&!player.hiding){
   const dir=target.clone().sub(mp);dir.y=0;dir.normalize();
   mp.addScaledVector(dir,dt*(2.0+Math.min(alert,2)));
   if(d<1.35){alive=false;msg("괴물에게 붙잡혔습니다. 새로고침해서 다시 도전하세요.",99999);}
 } else if(monsterState==="patrol"){
   const t=performance.now()*.00025+currentFloor*4;
   mp.x=10+Math.cos(t)*6;mp.z=10+Math.sin(t)*6;
 }
}

function animate(){
 requestAnimationFrame(animate);
 const dt=Math.min(.035,clock.getDelta());
 if(alive){move(dt);monsterAI(dt)}
 camera.position.copy(player.pos);
 const lookAt=new THREE.Vector3(
   player.pos.x+Math.sin(player.yaw)*Math.cos(player.pitch),
   player.pos.y+Math.sin(player.pitch),
   player.pos.z-Math.cos(player.yaw)*Math.cos(player.pitch)
 );
 camera.lookAt(lookAt);
 renderer.render(scene,camera);
}
const clock=new THREE.Clock();
animate();

addEventListener("resize",()=>{
 camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);
});
</script>
</body>
</html>
"""

components.html(GAME_HTML, height=760, scrolling=False)
