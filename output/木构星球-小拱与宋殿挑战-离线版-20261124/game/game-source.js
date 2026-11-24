// 宋殿拼搭：120秒、20组；前5组立柱自由排序，后续按结构阶段推进。
(() => {
  (() => {
    const SOUND = /* @__PURE__ */ (() => {
      class Soundscape2 {
        constructor() {
          this.ctx = null;
          this.muted = false;
          this.last = -1;
        }
        async unlock() {
          this.ctx ??= new (window.AudioContext || window.webkitAudioContext)();
          await this.ctx.resume();
        }
        tone(freq, time = 0, duration = 0.16, type = "sine", gain = 0.1) {
          if (!this.ctx || this.muted || this.ctx.state !== "running") return;
          const t = this.ctx.currentTime + time, o = this.ctx.createOscillator(), v = this.ctx.createGain();
          o.type = type;
          o.frequency.setValueAtTime(freq, t);
          v.gain.setValueAtTime(0, t);
          v.gain.linearRampToValueAtTime(gain, t + 8e-3);
          v.gain.exponentialRampToValueAtTime(1e-4, t + duration);
          o.connect(v);
          v.connect(this.ctx.destination);
          o.start(t);
          o.stop(t + duration + 0.02);
        }
        select() {
          this.tone(440, 0, 0.09, "sine", 0.045);
        }
        place(step) {
          this.tone(180 + step * 5, 0, 0.15, "triangle", 0.15);
          this.tone(680 + step * 18, 0.045, 0.24, "sine", 0.065);
        }
        reject() {
          this.tone(140, 0, 0.13, "triangle", 0.08);
        }
        tick(seconds) {
          if (seconds === this.last) return;
          this.last = seconds;
          if (seconds <= 30 && seconds > 0) {
            this.tone(seconds <= 10 ? 880 : 540, 0, 0.065, "sine", seconds <= 10 ? 0.07 : 0.04);
            if (seconds <= 5) this.tone(880, 0.15, 0.065, "sine", 0.055);
          }
        }
        win() {
          [523, 659, 784, 1046].forEach((n, i) => this.tone(n, i * 0.15, 0.5, "sine", 0.12));
        }
        lose() {
          [330, 277, 220, 165].forEach((n, i) => this.tone(n, i * 0.23, 0.4, "triangle", 0.1));
        }
      }
      return { Soundscape: Soundscape2 };
    })();
    const INPUT = /* @__PURE__ */ (() => {
      function shuffle2(items, random = Math.random) {
        const a = [...items];
        for (let i = a.length - 1; i > 0; i--) {
          const j = Math.floor(random() * (i + 1));
          [a[i], a[j]] = [a[j], a[i]];
        }
        return a;
      }
      function acceptDrop({ playing, selected: selected2, expected, moved, hit }) {
        return playing && selected2 === expected && moved && hit;
      }
      const STAGES = [[0, 1, 2, 3, 4], [5], [6, 7, 8, 9, 10], [11, 12, 13], [14, 15, 16, 17, 18], [19]];
      const STAGE_NAMES2 = ["立柱：各组柱子可任意先后", "联系枋", "檐下铺作：同层自由拼装", "梁架与平棊", "屋架：同层自由拼装", "佛坛与屏风"];
      class StageChallenge2 {
        constructor(total = 20, duration = 120000) {
          this.total = total;
          this.duration = duration;
          this.reset();
        }
        reset() {
          this.status = "ready";
          this.completed = /* @__PURE__ */ new Set();
          this.placed = 0;
          this.remaining = this.duration;
          this.deadline = 0;
        }
        start(now) {
          this.reset();
          this.status = "playing";
          this.deadline = now + this.duration;
        }
        tick(now) {
          if (this.status === "playing") {
            this.remaining = Math.max(0, this.deadline - now);
            if (!this.remaining) this.status = "lost";
          }
          return this.status;
        }
        get stage() {
          return STAGES.findIndex((ids) => ids.some((i) => !this.completed.has(i)));
        }
        canPlace(i) {
          return this.status === "playing" && !this.completed.has(i) && !!STAGES[this.stage]?.includes(i);
        }
        place(i, now) {
          this.tick(now);
          if (!this.canPlace(i)) return false;
          this.completed.add(i);
          this.placed = this.completed.size;
          if (this.placed === this.total) this.status = "won";
          return true;
        }
      }
      return { shuffle: shuffle2, acceptDrop, StageChallenge: StageChallenge2, STAGES, STAGE_NAMES: STAGE_NAMES2 };
    })();
    const { OrbitControls } = ORBIT;
    const { GLTFLoader } = GLTF;
      const { Soundscape } = SOUND;
    const { shuffle, StageChallenge, STAGE_NAMES } = INPUT;
    const $ = (q) => document.querySelector(q);
    const host = $("#scene");
    const game = new StageChallenge(20);
    const sound = new Soundscape();
    const groups = [];
    const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    let selected = -1;
    let loaded = false;
    let finished = false;
    let flights = [];
    let drag = null;
    let preview = null;
    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    const dragPoint = new THREE.Vector3();
    const dragPlane = new THREE.Plane();
    const avatar = document.createElement("div");
    avatar.className = "drag-avatar";
    avatar.hidden = true;
    document.body.append(avatar);
    const guide = document.createElement("div");
    guide.id = "drop-guide";
    guide.hidden = true;
    host.parentElement.append(guide);
    const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(Math.min(devicePixelRatio, 1.7));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.25;
    host.append(renderer.domElement);
    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#e5dfd1");
    const camera = new THREE.PerspectiveCamera(39, 1, 0.1, 200);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.minDistance = 16;
    controls.maxDistance = 65;
    controls.maxPolarAngle = Math.PI * 0.48;
    function reset() {
      controls.target.set(0, 4.5, 0);
      camera.position.set(24, 18, 29).sub(controls.target).multiplyScalar(Math.max(1, 1.15 / camera.aspect)).add(controls.target);
      controls.update();
    }
    reset();
    scene.add(new THREE.HemisphereLight(16774108, 6444615, 2));
    const key = new THREE.DirectionalLight(16770755, 3.1);
    key.position.set(-12, 25, 14);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    Object.assign(key.shadow.camera, { left: -20, right: 20, top: 20, bottom: -20, near: 1, far: 70 });
    key.shadow.normalBias = 0.025;
    scene.add(key);
    const fill = new THREE.DirectionalLight(16777215, 1);
    fill.position.set(16, 10, -12);
    scene.add(fill);
    const plane = new THREE.Mesh(new THREE.PlaneGeometry(150, 150), new THREE.MeshStandardMaterial({ color: 14209215, roughness: 1 }));
    plane.rotation.x = -Math.PI / 2;
    plane.position.y = -0.65;
    plane.receiveShadow = true;
    scene.add(plane);
    const observer = new ResizeObserver(() => {
      const { width: w, height: h } = host.getBoundingClientRect();
      renderer.setSize(w, h);
      const before = Math.max(1, 1.15 / camera.aspect);
      camera.aspect = w / h;
      camera.position.sub(controls.target).multiplyScalar(Math.max(1, 1.15 / camera.aspect) / before).add(controls.target);
      camera.updateProjectionMatrix();
    });
    observer.observe(host);
    $("#track").innerHTML = "<i></i>".repeat(20);
    function status(s) {
      $("#feedback").textContent = s;
    }
    function update() {
      document.body.dataset.gameStatus = game.status;
      notifyParent("progress", { placed: game.placed, status: game.status });
      const remaining = Math.ceil(game.remaining / 1e3);
      $("#seconds").textContent = String(remaining).padStart(3, "0");
      $(".clock").classList.toggle("urgent", game.status === "playing" && remaining <= 15);
      $("#progress").textContent = `${String(game.placed).padStart(2, "0")} / 20`;
      $("#count").textContent = `${20 - game.placed} 组待归位`;
      $("#track").setAttribute("aria-valuenow", game.placed);
      [...$("#track").children].forEach((e, i) => e.classList.toggle("done", game.completed.has(i)));
      groups.forEach((g, i) => {
        g.button.disabled = game.status !== "playing" || game.completed.has(i);
        g.button.classList.toggle("placed", game.completed.has(i));
        g.button.classList.toggle("selected", i === selected);
        g.button.setAttribute("aria-pressed", String(i === selected));
        g.ghost.visible = game.status === "playing" && game.canPlace(i) && (selected < 0 || i === selected);
      });
      $("#step").textContent = game.status === "playing" ? STAGE_NAMES[game.stage] : "立柱 · 联系 · 铺作 · 梁架 · 屋架";
    }
    function choose(i) {
      if (game.tick(performance.now()) !== "playing") {
        end();
        return;
      }
      if (game.completed.has(i)) return;
      selected = i;
      sound.select();
      status(game.canPlace(i) ? i < 5 ? "各组柱子无需排序，拖到左侧柱网区域即可。" : "拖到左侧提示区域，松手即可吸附。" : "先完成当前阶段：" + STAGE_NAMES[game.stage] + "。");
      update();
    }
    function place(i) {
      if (!game.place(i, performance.now())) {
        end();
        return;
      }
      const g = groups[i];
      g.root.visible = true;
      const y = g.root.position.y;
      if (!reduced) {
        g.root.position.y = y + 1;
        flights.push({ root: g.root, y, t: performance.now() });
      }
      sound.place(i);
      selected = -1;
      host.classList.add("accepted");
      setTimeout(() => host.classList.remove("accepted"), 500);
      status(`${g.label}，落榫成功。`);
      update();
      if (game.status === "won") end();
    }
    function castAt(x, y) {
      const r = host.getBoundingClientRect();
      pointer.set((x - r.left) / r.width * 2 - 1, -(y - r.top) / r.height * 2 + 1);
      raycaster.setFromCamera(pointer, camera);
      return x >= r.left && x <= r.right && y >= r.top && y <= r.bottom;
    }
    function dropBounds(i) {
      const r = host.getBoundingClientRect();
      const targets = i < 5 ? groups.slice(0, 5) : [groups[i]];
      let left = Infinity, top = Infinity, right = -Infinity, bottom = -Infinity;
      const v = new THREE.Vector3();
      for (const g of targets) for (const a of g.anchors) {
        v.copy(a).project(camera);
        if (v.z < -1 || v.z > 1) continue;
        const x = r.left + (v.x + 1) * r.width / 2, y = r.top + (1 - v.y) * r.height / 2;
        left = Math.min(left, x);
        right = Math.max(right, x);
        top = Math.min(top, y);
        bottom = Math.max(bottom, y);
      }
      const padding = Math.max(40, Math.min(65, r.width * 0.07));
      return { left: Math.max(r.left + 8, left - padding), right: Math.min(r.right - 8, right + padding), top: Math.max(r.top + 8, top - padding), bottom: Math.min(r.bottom - 8, bottom + padding) };
    }
    function nearTarget(x, y, i) {
      if (!game.canPlace(i) || !castAt(x, y)) return false;
      const b = dropBounds(i);
      return x >= b.left && x <= b.right && y >= b.top && y <= b.bottom;
    }
    function showGuide(i) {
      if (!game.canPlace(i)) {
        guide.hidden = true;
        return;
      }
      const b = dropBounds(i), r = host.getBoundingClientRect();
      guide.hidden = false;
      Object.assign(guide.style, { left: b.left - r.left + "px", top: b.top - r.top + "px", width: Math.max(0, b.right - b.left) + "px", height: Math.max(0, b.bottom - b.top) + "px" });
      guide.textContent = i < 5 ? "柱网区域 · 拖入即可吸附" : "拖入此区域即可吸附";
    }
    function cancelDrag(animate = false) {
      const d = drag;
      drag = null;
      if (preview) {
        scene.remove(preview);
        preview.traverse((o) => {
          if (o.isMesh) o.material.dispose();
        });
        preview = null;
      }
      controls.enabled = true;
      guide.hidden = true;
      host.classList.remove("drop-ready");
      if (d) {
        d.button.classList.remove("dragging");
        if (d.button.hasPointerCapture?.(d.id)) d.button.releasePointerCapture(d.id);
      }
      if (animate && d && !reduced) {
        const r = d.button.getBoundingClientRect();
        avatar.style.transition = "left 220ms,top 220ms,opacity 220ms";
        avatar.style.left = r.left + r.width / 2 + "px";
        avatar.style.top = r.top + r.height / 2 + "px";
        avatar.style.opacity = "0";
        setTimeout(() => {
          if (!drag) avatar.hidden = true;
        }, 230);
      } else avatar.hidden = true;
    }
    function beginDrag(e, i) {
      if (drag || e.button !== 0 || game.status !== "playing" || game.completed.has(i)) return;
      e.preventDefault();
      choose(i);
      if (game.status !== "playing") return;
      const button = groups[i].button;
      drag = { id: e.pointerId, i, x: e.clientX, y: e.clientY, button, type: e.pointerType, moved: false };
      button.setPointerCapture(e.pointerId);
      button.classList.add("dragging");
      controls.enabled = false;
      avatar.innerHTML = button.innerHTML;
      avatar.hidden = false;
      avatar.style.transition = "none";
      avatar.style.opacity = "1";
      avatar.style.left = e.clientX + "px";
      avatar.style.top = e.clientY - 24 + "px";
      preview = groups[i].root.clone(true);
      preview.visible = false;
      preview.traverse((o) => {
        if (o.isMesh) {
          o.material = o.material.clone();
          o.material.transparent = true;
          o.material.opacity = 0.62;
          o.material.depthWrite = false;
          o.castShadow = false;
        }
      });
      scene.add(preview);
      camera.getWorldDirection(dragPoint);
      dragPlane.setFromNormalAndCoplanarPoint(dragPoint, groups[i].center);
      showGuide(i);
    }
    window.addEventListener("pointermove", (e) => {
      if (!drag || e.pointerId !== drag.id) return;
      e.preventDefault();
      drag.moved ||= Math.hypot(e.clientX - drag.x, e.clientY - drag.y) > 10;
      avatar.style.left = e.clientX + "px";
      avatar.style.top = e.clientY - 24 + "px";
      const inside = castAt(e.clientX, e.clientY);
      avatar.classList.toggle("over-scene", inside);
      preview.visible = inside;
      if (inside && raycaster.ray.intersectPlane(dragPlane, dragPoint)) {
        preview.position.copy(groups[drag.i].root.position).add(dragPoint).sub(groups[drag.i].center);
      }
      host.classList.toggle("drop-ready", nearTarget(e.clientX, e.clientY, drag.i));
    }, { passive: false });
    window.addEventListener("pointerup", (e) => {
      if (!drag || e.pointerId !== drag.id) return;
      const d = drag;
      const valid = game.tick(performance.now()) === "playing" && d.moved && nearTarget(e.clientX, e.clientY, d.i);
      cancelDrag(!valid);
      if (valid) place(d.i);
      else {
        selected = -1;
        if (game.status === "lost") end();
        else {
          sound.reject();
          status(!game.canPlace(d.i) ? "先完成当前阶段：" + STAGE_NAMES[game.stage] + "。" : d.moved ? "再靠近提示区域一点，木件已退回。" : "按住木件拖入提示区域即可。");
          update();
        }
      }
    });
    window.addEventListener("pointercancel", () => {
      cancelDrag();
      selected = -1;
      update();
    });
    window.addEventListener("blur", () => {
      cancelDrag();
      selected = -1;
      update();
    });
    function start() {
      if (!loaded) return;
      notifyParent("started");
      cancelDrag();
      shuffle(groups.map((g) => g.button)).forEach((b) => $("#parts").append(b));
      $("#parts").scrollTop = 0;
      sound.unlock().catch(() => status("浏览器未能启用音效，仍可继续挑战。"));
      sound.last = -1;
      game.start(performance.now());
      finished = false;
      selected = -1;
      flights.forEach((f) => f.root.position.y = f.y);
      flights = [];
      groups.forEach((g) => g.root.visible = false);
      $("#result").hidden = true;
      $("#start").textContent = "重新开始";
      $("#phase").textContent = "120 秒 · 立柱起殿";
      status("先立柱：任意一组柱子，拖到左侧柱网区域即可。");
      reset();
      update();
    }
    function end() {
      if (finished || !["won", "lost"].includes(game.status)) return;
      finished = true;
      cancelDrag();
      selected = -1;
      groups.forEach((g) => g.ghost.visible = false);
      const won = game.status === "won";
      won ? sound.win() : sound.lose();
      $("#result-kicker").textContent = won ? "营造完成" : "时间到";
      $("#result-title").textContent = won ? "一殿，已然成形。" : "再试一次，从容落榫。";
      $("#result-copy").textContent = won ? `用时 ${Math.ceil((game.duration - game.remaining) / 1e3)} 秒 · 二十组木构全部归位` : `已完成 ${game.placed} / 20 组`;
      $("#result").hidden = false;
      update();
    }
    async function load() {
      try {
        const manifest = JSON.parse(document.getElementById("manifest-data").textContent);
        const gltf = await new GLTFLoader().parseAsync((() => {
          const bytes = Uint8Array.from(atob(window.__HALL_B64), (c) => c.charCodeAt(0));
          window.__HALL_B64 = null;
          return bytes.buffer;
        })(), "");
        scene.add(gltf.scene);
        gltf.scene.updateMatrixWorld(true);
        gltf.scene.traverse((o) => {
          if (o.isMesh) {
            o.castShadow = true;
            o.receiveShadow = true;
            if (o.material) o.material.roughness = 0.57;
          }
        });
        for (const [i, kit] of manifest.kits.entries()) {
          const root = gltf.scene.getObjectByName(kit.root_node) || gltf.scene.children.find((o) => o.userData.kit_id === kit.id);
          if (!root) throw Error(`缺少组合件 ${kit.id}`);
          const ghost = root.clone(true);
          ghost.traverse((o) => {
            if (o.isMesh) {
              o.material = new THREE.MeshBasicMaterial({ color: 9530181, transparent: true, opacity: 0.1, wireframe: false, depthWrite: false });
              o.castShadow = false;
            }
          });
          root.parent.add(ghost);
          ghost.visible = false;
          const button = document.createElement("button");
          button.className = "piece";
          button.innerHTML = `<img alt="" draggable="false"><span>${kit.label}</span>`;
          button.addEventListener("pointerdown", (e) => beginDrag(e, i));
          button.addEventListener("lostpointercapture", () => {
            if (drag?.i === i) {
              cancelDrag();
              selected = -1;
              update();
            }
          });
          $("#parts").append(button);
          const anchors = [];
          root.traverse((o) => {
            if (!o.isMesh) return;
            const pos = o.geometry.attributes.position, step = Math.max(1, Math.floor(pos.count / 1800));
            for (let j = 0; j < pos.count; j += step) anchors.push(new THREE.Vector3().fromBufferAttribute(pos, j).applyMatrix4(o.matrixWorld));
          });
          groups.push({ root, ghost, button, anchors, label: kit.label, center: new THREE.Box3().setFromObject(root).getCenter(new THREE.Vector3()) });
        }
        renderer.render(scene, camera);
        const ref = renderer.domElement.toDataURL("image/png");
        $("#reference-img").src = ref;
        $("#large-reference").src = ref;
        const oldRatio = renderer.getPixelRatio();
        renderer.setPixelRatio(1);
        renderer.setSize(256, 180, false);
        camera.aspect = 256 / 180;
        camera.updateProjectionMatrix();
        const fixed = gltf.scene.getObjectByName("FIXED_mesh");
        if (fixed) fixed.visible = false;
        for (const g of groups) {
          groups.forEach((x) => x.root.visible = x === g);
          const bounds = new THREE.Box3().setFromObject(g.root), size = bounds.getSize(new THREE.Vector3()), center = bounds.getCenter(new THREE.Vector3()), distance = Math.max(size.x, size.y, size.z) * 2.1;
          camera.position.copy(center).add(new THREE.Vector3(1, 0.75, 1).normalize().multiplyScalar(Math.max(distance, 4)));
          camera.lookAt(center);
          renderer.render(scene, camera);
          g.button.querySelector("img").src = renderer.domElement.toDataURL("image/png");
        }
        if (fixed) fixed.visible = true;
        groups.forEach((g) => g.root.visible = true);
        renderer.setPixelRatio(oldRatio);
        renderer.setSize(host.clientWidth, host.clientHeight);
        camera.aspect = host.clientWidth / host.clientHeight;
        camera.updateProjectionMatrix();
        reset();
        shuffle(groups.map((g) => g.button)).forEach((b) => $("#parts").append(b));
        loaded = true;
        document.body.dataset.gameReady = "true";
        notifyParent("ready");
        $("#loading").hidden = true;
        $("#start").disabled = false;
        $("#start").textContent = "开始 120 秒挑战 ↗";
        update();
        if (window.parent !== window) start();
      } catch (e) {
        $("#loading").textContent = "模型未能加载，请刷新重试。";
        status(e.message);
        notifyParent("error", { message: e.message });
        console.error(e);
      }
    }
    $("#start").onclick = start;
    $("#again").onclick = start;
    $("#reset").onclick = reset;
    $("#plus").onclick = () => {
      camera.position.sub(controls.target).multiplyScalar(0.85).add(controls.target);
      controls.update();
    };
    $("#minus").onclick = () => {
      camera.position.sub(controls.target).multiplyScalar(1.15).add(controls.target);
      controls.update();
    };
    $("#sound").onclick = () => {
      sound.muted = !sound.muted;
      $("#sound").textContent = sound.muted ? "声音 关" : "声音 开";
      $("#sound").setAttribute("aria-pressed", String(sound.muted));
      if (!sound.muted) sound.unlock().catch(() => {
      });
    };
    $("#full").onclick = () => {
      if (document.fullscreenElement) document.exitFullscreen();
      else document.documentElement.requestFullscreen?.().catch(() => status("当前浏览器不支持全屏。"));
    };
    $("#reference").onclick = () => $("#reference-dialog").showModal();
    $("#close-reference").onclick = () => $("#reference-dialog").close();
    function frame(now) {
      requestAnimationFrame(frame);
      if (game.status === "playing") {
        game.tick(now);
        if (game.status === "playing") sound.tick(Math.ceil(game.remaining / 1e3));
        if (game.status === "lost") end();
        $("#seconds").textContent = String(Math.ceil(game.remaining / 1e3)).padStart(3, "0");
        $(".clock").classList.toggle("urgent", game.remaining <= 15e3);
      }
      flights = flights.filter((f) => {
        const t = Math.min(1, (now - f.t) / 340);
        f.root.position.y = f.y + 1 * (1 - t * t);
        return t < 1;
      });
      controls.update();
      renderer.render(scene, camera);
    }
    requestAnimationFrame(frame);
    load();
    $("#parts-up").onclick = () => $("#parts").scrollBy({ top: -220, behavior: "smooth" });
    $("#parts-down").onclick = () => $("#parts").scrollBy({ top: 220, behavior: "smooth" });
    function notifyParent(action, payload = {}) {
      if (window.parent !== window) window.parent.postMessage({ channel: "wood-hall-v1", action, ...payload }, "*");
    }
    document.addEventListener("pointerdown", () => {
      notifyParent("outside-pointer");
      if (game.status === "playing") sound.unlock().catch(() => {
      });
    }, { capture: true });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !document.querySelector("dialog[open]")) {
        e.preventDefault();
        notifyParent("exit");
      }
    });
    window.addEventListener("message", (e) => {
      if (e.source !== window.parent || e.data?.channel !== "wood-hall-v1") return;
      if (e.data.action === "mute") {
        sound.muted = true;
        sound.ctx?.suspend();
      }
      if (e.data.action === "toggle-sound") {
        sound.muted = !sound.muted;
        if (!sound.muted) sound.unlock().catch(() => {
        });
        notifyParent("sound", { muted: sound.muted });
      }
    });
  })();
})();
