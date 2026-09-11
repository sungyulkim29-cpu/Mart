import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="3D 마트 탈출 서바이벌", layout="wide")

# Streamlit 기본 여백 제거 CSS
st.markdown("""
    <style>
    .main .block-container { padding: 0rem; }
    iframe { border: none; }
    </style>
""", unsafe_allow_html=True)

game_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <style>
        * { touch-action: none; user-select: none; }
        body, html { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: #000; font-family: sans-serif; }
        #canvas-container { width: 100vw; height: 100vh; }
        #ui {
            position: absolute; top: 15px; left: 15px; color: #fff;
            background: rgba(0,0,0,0.7); padding: 12px; border-radius: 8px;
            z-index: 10; pointer-events: none; font-size: 14px;
        }
        #focus-overlay {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.5); color: white; display: flex;
            justify-content: center; align-items: center; z-index: 100;
            font-size: 20px; font-weight: bold; cursor: pointer;
        }
        /* 모바일 조이스틱 */
        #joystick-zone {
            position: absolute; bottom: 40px; left: 40px;
            width: 120px; height: 120px; background: rgba(255,255,255,0.15);
            border: 2px solid rgba(255,255,255,0.3); border-radius: 50%;
            display: none; z-index: 20;
        }
        #joystick-knob {
            width: 50px; height: 50px; background: rgba(255,255,255,0.6);
            border-radius: 50%; position: absolute; top: 35px; left: 35px;
        }
    </style>
    <!-- Three.js 및 GLTFLoader 불러오기 -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
</head>
<body>
    <div id="focus-overlay">화면을 클릭하면 조작이 시작됩니다!</div>
    <div id="ui">
        <div style="font-size: 16px; font-weight:bold; margin-bottom: 5px;">🛒 마트 탈출 3D</div>
        <div>위치: <span id="floor-ui" style="color: #ff0;">1층</span></div>
        <div>힌트 순서: 
            <span style="color:#4d88ff;">○(파랑)</span> 
            <span style="color:#ff4d4d;">□(빨강)</span> 
            <span style="color:#ffff4d;">♤(노랑)</span> 
            <span style="color:#4dff4d;">♧(초록)</span>
        </div>
        <div id="controls-hint" style="margin-top:5px; color:#aaa;">조작: WASD / 이동</div>
    </div>
    
    <div id="joystick-zone"><div id="joystick-knob"></div></div>
    <div id="canvas-container"></div>

    <script>
        // 1. 포커스 설정 (조작 안되는 문제 해결)
        const overlay = document.getElementById('focus-overlay');
        overlay.addEventListener('click', () => {
            overlay.style.display = 'none';
            window.focus();
        });

        // 2. 모바일 감지 및 터치 스크롤 방지
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        if (isMobile) {
            document.getElementById('joystick-zone').style.display = 'block';
            document.getElementById('controls-hint').innerText = '조작: 하단 조이스틱';
        }
        document.addEventListener('touchmove', (e) => e.preventDefault(), { passive: false });

        // 3. Three.js 기본 씬 생성
        const scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0x0a0a0a, 0.06);

        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        document.getElementById('canvas-container').appendChild(renderer.domElement);

        // 조명 설정
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);
        const playerLight = new THREE.PointLight(0xffffff, 1.2, 18);
        scene.add(playerLight);

        // 4. 3D GLTF 모델 로더 (맵 & 괴물 로드)
        const loader = new THREE.GLTFLoader();
        let monsterModel = null;

        /* 
           실제 custom .gltf 파일이 static 폴더에 있을 때 아래 주석을 해제하여 사용합니다.
           loader.load('/app/static/map.gltf', (gltf) => { scene.add(gltf.scene); });
           loader.load('/app/static/monster.gltf', (gltf) => { monsterModel = gltf.scene; scene.add(monsterModel); });
        */

        // 파일이 없을 경우를 대비한 기본 3층 구조 및 백룸 괴물 형상 생성 (더미)
        const floorHeight = 5;
        for (let i = 0; i < 3; i++) {
            const floorGeo = new THREE.PlaneGeometry(40, 40);
            const floorMat = new THREE.MeshStandardMaterial({ color: 0x222222 });
            const floor = new THREE.Mesh(floorGeo, floorMat);
            floor.rotation.x = -Math.PI / 2;
            floor.position.y = i * floorHeight;
            scene.add(floor);

            // 각 층 숨기 공간 (캐비넷)
            const box = new THREE.Mesh(
                new THREE.BoxGeometry(2, 3.5, 2),
                new THREE.MeshStandardMaterial({ color: 0x444444 })
            );
            box.position.set(-12, i * floorHeight + 1.75, -12);
            scene.add(box);
        }

        // 백룸 팔다리 긴 검은 괴물 (더미 객체)
        const monsterGroup = new THREE.Group();
        const matBlack = new THREE.MeshBasicMaterial({ color: 0x000000 });
        const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.15, 3), matBlack);
        torso.position.y = 2.5;
        const head = new THREE.Mesh(new THREE.SphereGeometry(0.3), matBlack);
        head.position.y = 4.2;
        const armL = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 3.5), matBlack);
        armL.position.set(-0.5, 2.5, 0);
        const armR = armL.clone();
        armR.position.x = 0.5;
        monsterGroup.add(torso, head, armL, armR);
        monsterGroup.position.set(8, 0, 8);
        scene.add(monsterGroup);

        // 5. 플레이어 및 이동 조작
        const player = { pos: new THREE.Vector3(0, 1.7, 0), dir: new THREE.Vector2(), speed: 0.12 };
        const keys = {};

        window.addEventListener('keydown', (e) => keys[e.key.toLowerCase()] = true);
        window.addEventListener('keyup', (e) => keys[e.key.toLowerCase()] = false);

        // 조이스틱 이벤트
        const jZone = document.getElementById('joystick-zone');
        const jKnob = document.getElementById('joystick-knob');
        let jTouch = false, jStart = { x: 0, y: 0 };

        jZone.addEventListener('touchstart', (e) => {
            jTouch = true;
            jStart = { x: e.touches[0].clientX, y: e.touches[0].clientY };
        });
        jZone.addEventListener('touchmove', (e) => {
            if (!jTouch) return;
            const dx = e.touches[0].clientX - jStart.x;
            const dy = e.touches[0].clientY - jStart.y;
            const dist = Math.min(Math.hypot(dx, dy), 40);
            const angle = Math.atan2(dy, dx);
            const mx = Math.cos(angle) * (dist / 40);
            const my = Math.sin(angle) * (dist / 40);

            jKnob.style.transform = `translate(${mx * 30}px, ${my * 30}px)`;
            player.dir.set(mx, -my);
        });
        jZone.addEventListener('touchend', () => {
            jTouch = false;
            jKnob.style.transform = `translate(0px, 0px)`;
            player.dir.set(0, 0);
        });

        // 6. 메인 루프
        function animate() {
            requestAnimationFrame(animate);

            if (!isMobile) {
                player.dir.set(0, 0);
                if (keys['w']) player.dir.y += 1;
                if (keys['s']) player.dir.y -= 1;
                if (keys['a']) player.dir.x -= 1;
                if (keys['d']) player.dir.x += 1;
                player.dir.normalize();
            }

            // 플레이어 이동 (점프 없음)
            player.pos.x += player.dir.x * player.speed;
            player.pos.z -= player.dir.y * player.speed;

            camera.position.copy(player.pos);
            playerLight.position.copy(player.pos);

            // 층수 계산
            const curFloor = Math.floor(player.pos.y / floorHeight) + 1;
            document.getElementById('floor-ui').innerText = `${Math.min(Math.max(curFloor, 1), 3)}층`;

            renderer.render(scene, camera);
        }
        animate();

        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
    </script>
</body>
</html>
"""

components.html(game_html, height=800, scrolling=False)
