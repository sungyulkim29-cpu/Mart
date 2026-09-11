import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="마트 탈출 게임", layout="wide")

st.title("🛒 마트 탈출 3D 서바이벌")
st.caption("괴물을 피해 각 층의 힌트를 찾고 마트를 탈출하세요!")

# Three.js 기반 3D 게임 HTML/JS 코드
game_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <style>
        body { margin: 0; overflow: hidden; background-color: #000; font-family: sans-serif; }
        #canvas-container { width: 100vw; height: 100vh; }
        #ui {
            position: absolute; top: 10px; left: 10px; color: white;
            background: rgba(0,0,0,0.6); padding: 10px; border-radius: 8px;
            pointer-events: none;
        }
        /* 모바일 조이스틱 UI */
        #joystick-zone {
            position: absolute; bottom: 30px; left: 30px;
            width: 120px; height: 120px; background: rgba(255,255,255,0.2);
            border-radius: 50%; display: none; touch-action: none;
        }
        #joystick-knob {
            width: 50px; height: 50px; background: rgba(255,255,255,0.5);
            border-radius: 50%; position: absolute; top: 35px; left: 35px;
        }
    </style>
    <!-- Three.js 라이브러리 불러오기 -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    <div id="ui">
        <div>현재 위치: <span id="floor-ui">1층</span></div>
        <div>힌트 정답 순서: <span style="color:#55f;">○(파랑)</span> <span style="color:#f55;">□(빨강)</span> <span style="color:#fy5;">♤(노랑)</span> <span style="color:#5f5;">♧(초록)</span></div>
        <div id="controls-hint">조작: WASD / 화살표 키</div>
    </div>
    
    <div id="joystick-zone"><div id="joystick-knob"></div></div>
    <div id="canvas-container"></div>

    <script>
        // 모바일 감지
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        if (isMobile) {
            document.getElementById('joystick-zone').style.display = 'block';
            document.getElementById('controls-hint').innerText = '조작: 화면 좌측 하단 조이스틱';
        }

        // Scene, Camera, Renderer 설정
        const scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0x050505, 0.05); // 어두운 마트 분위기 효과

        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        document.getElementById('canvas-container').appendChild(renderer.domElement);

        // 조명
        const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
        scene.add(ambientLight);
        
        const playerLight = new THREE.PointLight(0xffffff, 1, 15);
        scene.add(playerLight);

        // 3층 건물 구조 생성
        const floorHeight = 4;
        for (let i = 0; i < 3; i++) {
            // 바닥
            const floorGeo = new THREE.PlaneGeometry(30, 30);
            const floorMat = new THREE.MeshBasicMaterial({ color: 0x333333, side: THREE.DoubleSide });
            const floor = new THREE.Mesh(floorGeo, floorMat);
            floor.rotation.x = Math.PI / 2;
            floor.position.y = i * floorHeight;
            scene.add(floor);

            // 숨는 공간 (캐비닛)
            const hideGeo = new THREE.BoxGeometry(1.5, 2.5, 1.5);
            const hideMat = new THREE.MeshBasicMaterial({ color: 0x555555 });
            const cabinet = new THREE.Mesh(hideGeo, hideMat);
            cabinet.position.set(-8, i * floorHeight + 1.25, -8);
            scene.add(cabinet);
        }

        // 힌트 오브젝트 생성 (○:파랑, □:빨강, ♤:노랑, ♧:초록)
        const hintColors = [0x0000ff, 0xff0000, 0xffff00, 0x00ff00];
        const shapes = [
            new THREE.SphereGeometry(0.3, 16, 16), // ○
            new THREE.BoxGeometry(0.5, 0.5, 0.5),    // □
            new THREE.ConeGeometry(0.3, 0.6, 4),     // ♤ 대용
            new THREE.TorusGeometry(0.3, 0.1, 8, 16) // ♧ 대용
        ];

        // 각 층에 5개씩 배치
        for (let f = 0; f < 3; f++) {
            for (let h = 0; h < 5; h++) {
                const shapeIdx = h % 4;
                const mat = new THREE.MeshBasicMaterial({ color: hintColors[shapeIdx] });
                const hintMesh = new THREE.Mesh(shapes[shapeIdx], mat);
                
                // 랜덤 위치 배치
                const rx = (Math.random() - 0.5) * 20;
                const rz = (Math.random() - 0.5) * 20;
                hintMesh.position.set(rx, f * floorHeight + 0.5, rz);
                scene.add(hintMesh);
            }
        }

        // 팔다리가 긴 검은색 괴물 (백룸 모티브)
        const monsterGroup = new THREE.Group();
        const blackMat = new THREE.MeshBasicMaterial({ color: 0x050505 });
        
        // 몸통
        const body = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 2.5), blackMat);
        body.position.y = 2;
        monsterGroup.add(body);

        // 머리
        const head = new THREE.Mesh(new THREE.SphereGeometry(0.35), blackMat);
        head.position.y = 3.5;
        monsterGroup.add(head);

        // 긴 팔과 다리
        const legGeo = new THREE.CylinderGeometry(0.08, 0.08, 2.5);
        const leftLeg = new THREE.Mesh(legGeo, blackMat);
        leftLeg.position.set(-0.3, 0.75, 0);
        const rightLeg = new THREE.Mesh(legGeo, blackMat);
        rightLeg.position.set(0.3, 0.75, 0);
        
        const armGeo = new THREE.CylinderGeometry(0.06, 0.06, 3);
        const leftArm = new THREE.Mesh(armGeo, blackMat);
        leftArm.position.set(-0.5, 2.2, 0);
        leftArm.rotation.z = 0.2;
        const rightArm = new THREE.Mesh(armGeo, blackMat);
        rightArm.position.set(0.5, 2.2, 0);
        rightArm.rotation.z = -0.2;

        monsterGroup.add(leftLeg, rightLeg, leftArm, rightArm);
        monsterGroup.position.set(5, 0, 5);
        scene.add(monsterGroup);

        // 플레이어 설정
        const player = {
            position: new THREE.Vector3(0, 1.6, 0),
            moveDir: new THREE.Vector2(0, 0),
            speed: 0.1
        };

        // PC 조작 (WASD)
        const keys = {};
        window.addEventListener('keydown', (e) => keys[e.key.toLowerCase()] = true);
        window.addEventListener('keyup', (e) => keys[e.key.toLowerCase()] = false);

        // 모바일 조이스틱
        const joystickZone = document.getElementById('joystick-zone');
        const joystickKnob = document.getElementById('joystick-knob');
        let touching = false;
        let touchStart = { x: 0, y: 0 };

        joystickZone.addEventListener('touchstart', (e) => {
            touching = true;
            touchStart.x = e.touches[0].clientX;
            touchStart.y = e.touches[0].clientY;
        });

        joystickZone.addEventListener('touchmove', (e) => {
            if (!touching) return;
            const dx = e.touches[0].clientX - touchStart.x;
            const dy = e.touches[0].clientY - touchStart.y;
            const dist = Math.min(Math.hypot(dx, dy), 40);
            const angle = Math.atan2(dy, dx);
            
            const moveX = Math.cos(angle) * (dist / 40);
            const moveY = Math.sin(angle) * (dist / 40);

            joystickKnob.style.transform = `translate(${moveX * 30}px, ${moveY * 30}px)`;
            player.moveDir.set(moveX, -moveY);
        });

        joystickZone.addEventListener('touchend', () => {
            touching = false;
            joystickKnob.style.transform = `translate(0px, 0px)`;
            player.moveDir.set(0, 0);
        });

        // 프레임 업데이트
        function animate() {
            requestAnimationFrame(animate);

            // PC 이동 로직 (점프 기능 없음)
            if (!isMobile) {
                player.moveDir.set(0, 0);
                if (keys['w']) player.moveDir.y += 1;
                if (keys['s']) player.moveDir.y -= 1;
                if (keys['a']) player.moveDir.x -= 1;
                if (keys['d']) player.moveDir.x += 1;
                player.moveDir.normalize();
            }

            // 플레이어 이동
            player.position.x += player.moveDir.x * player.speed;
            player.position.z -= player.moveDir.y * player.speed;

            // 카메라 및 조명 위치 업데이트
            camera.position.copy(player.position);
            playerLight.position.copy(player.position);

            // 층수 표시 업데이트
            const currentFloor = Math.floor(player.position.y / floorHeight) + 1;
            document.getElementById('floor-ui').innerText = `${Math.min(Math.max(currentFloor, 1), 3)}층`;

            // 간단한 괴물 추적 로직
            const distToMonster = player.position.distanceTo(monsterGroup.position);
            if (distToMonster < 15) {
                monsterGroup.position.x += (player.position.x - monsterGroup.position.x) * 0.005;
                monsterGroup.position.z += (player.position.z - monsterGroup.position.z) * 0.005;
            }

            renderer.render(scene, camera);
        }

        animate();

        // 리사이즈 처리
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
    </script>
</body>
</html>
"""

components.html(game_html, height=700)
