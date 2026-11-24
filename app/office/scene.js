// Office Bot scene, ported from agent-office (github.com/deveyn-hainey/agent-office) js/scene.js.
// Changes for Agent Team: helpers inlined, local-time clock, live run stats on the TV,
// WASD only while the pointer is over the office, setStats() added.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

export const STATES = {
  working: { label: 'Working', color: '#34c759' },
  finished: { label: 'Finished', color: '#3b82f6' },
  'needs-you': { label: 'Needs you', color: '#f59e0b' },
  stuck: { label: 'Stuck', color: '#ef4444' },
  idle: { label: 'Idle', color: '#a3a3ab' },
};
export const ACTIVE = ['working', 'finished', 'needs-you', 'stuck'];
export function hash(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); }
  return h >>> 0;
}
const truncate = (s, n = 40) => { s = String(s ?? ''); return s.length > n ? s.slice(0, n - 1).trimEnd() + '…' : s; };
const localClock = () => { const d = new Date(); return { h: d.getHours(), m: d.getMinutes(), s: d.getSeconds() }; };

const FH = 6; // floor-to-floor height
const SLAB = 0.5;
const WALL_H = 4.2;
const BASE_H = 10.5; // building base under floor 1 (3 storeys)
const BODY_Y = 1.4; // seated character height
const SP = 4.2; // desk spacing
const RP = 4.6; // desk row pitch
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

const mat = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.65, metalness: 0, ...o });
const M = {
  white: mat('#f6f6f7'),
  floor: mat('#ececee'),
  wall: mat('#f9f9fa'),
  gray: mat('#dedee2'),
  dark: mat('#17171b', { roughness: 0.5 }),
  black: mat('#0e0e11', { roughness: 0.55 }),
  win: mat('#101114', { roughness: 0.3 }),
  glass: new THREE.MeshStandardMaterial({ color: '#cfe3ee', transparent: true, opacity: 0.22, roughness: 0.1, depthWrite: false }),
  green: mat('#8fd18b', { roughness: 0.7 }),
  green2: mat('#76c27a', { roughness: 0.7 }),
  pot: mat('#fdfdfd'),
  facade: mat('#ffffff', { roughness: 0.9, emissive: '#ffffff', emissiveIntensity: 0.32 }),
};

function add(parent, geo, material, x = 0, y = 0, z = 0, cast = true, receive = true) {
  const m = new THREE.Mesh(geo, material);
  m.position.set(x, y, z);
  m.castShadow = cast;
  m.receiveShadow = receive;
  parent.add(m);
  return m;
}
const box = (p, w, h, d, material, x, y, z, cast = true) => add(p, new THREE.BoxGeometry(w, h, d), material, x, y, z, cast);
const rbox = (p, w, h, d, r, material, x, y, z) => add(p, new RoundedBoxGeometry(w, h, d, 5, r), material, x, y, z);

function canvasTex(w, h, draw) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 4;
  return t;
}

/* ---------- decor ---------- */
function plant(p, x, z, s = 1) {
  const g = new THREE.Group();
  add(g, new THREE.CylinderGeometry(0.45, 0.35, 0.7, 20), M.pot, 0, 0.35, 0);
  add(g, new THREE.SphereGeometry(0.62, 20, 16), M.green, 0, 1.25, 0);
  add(g, new THREE.SphereGeometry(0.5, 20, 16), M.green2, 0.12, 1.85, 0.05);
  add(g, new THREE.SphereGeometry(0.34, 16, 12), M.green, -0.1, 2.3, 0);
  g.position.set(x, 0, z);
  g.scale.setScalar(s);
  p.add(g);
}

function sofa(p, x, z, rotY, len = 3) {
  const g = new THREE.Group();
  rbox(g, len, 0.55, 1.2, 0.18, M.gray, 0, 0.45, 0);
  rbox(g, len, 0.9, 0.35, 0.16, M.gray, 0, 0.85, -0.5);
  rbox(g, 0.32, 0.75, 1.2, 0.14, M.gray, -len / 2 + 0.1, 0.75, 0);
  rbox(g, 0.32, 0.75, 1.2, 0.14, M.gray, len / 2 - 0.1, 0.75, 0);
  g.position.set(x, 0, z);
  g.rotation.y = rotY;
  p.add(g);
}

function ottoman(p, x, z, rot = 0, c = M.black) {
  const m = rbox(p, 1.0, 0.55, 1.0, 0.2, c, x, 0.3, z);
  m.rotation.y = rot;
}

function clock(p, x, y) {
  const g = new THREE.Group();
  const face = canvasTex(256, 256, (c) => {
    c.fillStyle = '#fff'; c.beginPath(); c.arc(128, 128, 124, 0, 7); c.fill();
    c.strokeStyle = '#17171b'; c.lineWidth = 8; c.stroke();
    c.fillStyle = '#17171b';
    for (let i = 0; i < 12; i++) {
      const a = (i / 12) * Math.PI * 2;
      c.fillRect(128 + Math.sin(a) * 100 - 3, 128 - Math.cos(a) * 100 - 3, 6, 6);
    }
  });
  add(g, new THREE.CylinderGeometry(0.72, 0.72, 0.12, 40), M.white, 0, 0, 0).rotation.x = Math.PI / 2;
  const f = new THREE.Mesh(new THREE.CircleGeometry(0.68, 40), new THREE.MeshBasicMaterial({ map: face }));
  f.position.z = 0.07;
  g.add(f);
  const hand = (len, w, mat_) => {
    const pivot = new THREE.Group();
    pivot.position.z = 0.09;
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, len, 0.02), mat_);
    m.position.y = len / 2 - 0.05;
    pivot.add(m);
    g.add(pivot);
    return pivot;
  };
  const hh = hand(0.38, 0.05, M.black), mh = hand(0.55, 0.035, M.black);
  const sh = hand(0.6, 0.015, mat('#ef4444'));
  g.position.set(x, y, 0);
  p.add(g);
  g.userData.tick = () => {
    const t = localClock();
    sh.rotation.z = -(t.s / 60) * Math.PI * 2;
    mh.rotation.z = -((t.m + t.s / 60) / 60) * Math.PI * 2;
    hh.rotation.z = -(((t.h % 12) + t.m / 60) / 12) * Math.PI * 2;
  };
  g.userData.tick();
  return g;
}

let tvStats = { runs: 0, label: 'runs today', bars: [] };
function drawTv(c, w, h) {
  c.fillStyle = '#16181d'; c.fillRect(0, 0, w, h);
  c.fillStyle = '#fff'; c.font = '700 34px sans-serif'; c.fillText(String(tvStats.runs.toLocaleString()), 28, 56);
  c.fillStyle = '#7a7f8a'; c.font = '16px sans-serif'; c.fillText(tvStats.label, 30, 80);
  const pts = tvStats.bars.length ? tvStats.bars : [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
  const mx = Math.max(1, ...pts);
  c.strokeStyle = '#3ddc84'; c.lineWidth = 4; c.beginPath();
  pts.forEach((v, i) => { const x = 28 + (i / (pts.length - 1)) * 300, yy = 255 - (v / mx) * 140; i ? c.lineTo(x, yy) : c.moveTo(x, yy); });
  c.stroke();
  c.fillStyle = '#3b82f6';
  pts.slice(-9).forEach((v, i) => { const bh = 6 + (v / mx) * 90; c.fillRect(350 + i * 16, 260 - bh, 10, bh); });
}
const tvs = new Set();
function tv(p, y) {
  const g = new THREE.Group();
  box(g, 3.2, 1.8, 0.1, M.black, 0, 0, 0);
  const tex = canvasTex(512, 288, drawTv);
  tvs.add(tex);
  const s = new THREE.Mesh(new THREE.PlaneGeometry(3.0, 1.6), new THREE.MeshBasicMaterial({ map: tex }));
  s.position.z = 0.06;
  g.add(s);
  g.position.set(0, y, 0);
  p.add(g);
  return g;
}

function letterTex(name, sub) {
  return canvasTex(1024, 256, (c, w, h) => {
    c.clearRect(0, 0, w, h);
    c.fillStyle = '#26262b';
    let size = 150;
    c.font = `800 ${size}px Inter, system-ui, sans-serif`;
    while (c.measureText(name).width > w - 40 && size > 40) { size -= 6; c.font = `800 ${size}px Inter, system-ui, sans-serif`; }
    c.fillText(name, 10, 160);
    c.fillStyle = '#b4b4bb'; c.font = '600 40px Inter, system-ui, sans-serif';
    c.fillText(sub, 14, 225);
  });
}

function railing(len) {
  const g = new THREE.Group();
  box(g, len, 0.95, 0.05, M.glass, 0, 0.95, 0, false);
  box(g, len, 0.07, 0.12, M.white, 0, 1.45, 0);
  box(g, len, 0.12, 0.1, M.white, 0, 0.45, 0);
  const n = Math.round(len / 2.2);
  for (let i = 0; i <= n; i++) box(g, 0.08, 1.05, 0.08, M.white, -len / 2 + (i / n) * len, 0.95, 0);
  return g;
}

/* ---------- agents ---------- */
function bodyGeo(kind) {
  switch (kind) {
    case 0: { const g = new THREE.SphereGeometry(0.5, 32, 24); g.scale(1, 0.95, 1); return { g, face: 0.47 }; }
    case 1: return { g: new THREE.CapsuleGeometry(0.34, 0.45, 8, 20), face: 0.33 };
    case 2: return { g: new RoundedBoxGeometry(0.85, 0.85, 0.85, 6, 0.2), face: 0.43 };
    case 3: {
      const s = new THREE.Shape();
      for (let i = 0; i < 10; i++) {
        const r = i % 2 ? 0.3 : 0.65, a = (i / 10) * Math.PI * 2 + Math.PI / 2;
        i ? s.lineTo(Math.cos(a) * r, Math.sin(a) * r) : s.moveTo(Math.cos(a) * r, Math.sin(a) * r);
      }
      s.closePath();
      const g = new THREE.ExtrudeGeometry(s, { depth: 0.22, bevelEnabled: true, bevelSize: 0.1, bevelThickness: 0.1, bevelSegments: 5 });
      g.center();
      return { g, face: 0.22 };
    }
    default: {
      const pts = [[0, -0.5], [0.3, -0.46], [0.5, -0.25], [0.44, 0.05], [0.28, 0.33], [0.12, 0.52], [0, 0.56]].map(([x, y]) => new THREE.Vector2(x, y));
      return { g: new THREE.LatheGeometry(pts, 32), face: 0.34 };
    }
  }
}

const ICONS = {
  working: '<svg viewBox="0 0 24 24"><circle cx="6" cy="12" r="2" fill="#fff"/><circle cx="12" cy="12" r="2" fill="#fff"/><circle cx="18" cy="12" r="2" fill="#fff"/></svg>',
  finished: '<svg viewBox="0 0 24 24"><path d="M6 12.5l4 4 8-9" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  'needs-you': '<svg viewBox="0 0 24 24"><path d="M12 5v8" stroke="#fff" stroke-width="3.2" stroke-linecap="round"/><circle cx="12" cy="18" r="1.9" fill="#fff"/></svg>',
  stuck: '<svg viewBox="0 0 24 24"><path d="M7 7l10 10M17 7L7 17" stroke="#fff" stroke-width="3.2" stroke-linecap="round"/></svg>',
  idle: '',
};

function makeAgent(a, hooks) {
  const root = new THREE.Group();
  root.userData.agentId = a.id;
  // chair
  const chair = new THREE.Group();
  add(chair, new THREE.CylinderGeometry(0.07, 0.07, 0.4, 10), M.black, 0, 0.25, 0);
  add(chair, new THREE.CylinderGeometry(0.42, 0.42, 0.14, 24), M.dark, 0, 0.55, 0);
  rbox(chair, 0.8, 0.8, 0.14, 0.06, M.dark, 0, 1.0, 0.45).rotation.x = -0.1;
  for (let i = 0; i < 3; i++) {
    const arm = box(chair, 0.9, 0.05, 0.08, M.black, 0, 0.1, 0);
    arm.rotation.y = (i * Math.PI) / 3;
  }
  chair.scale.setScalar(1.15);
  root.add(chair);

  const body = new THREE.Group();
  const { g, face } = bodyGeo(hash(a.id) % 5);
  const bm = mat(a.colorHex, { roughness: 0.45 });
  const mesh = add(body, g, bm, 0, 0, 0);
  for (const sx of [-1, 1]) add(body, new THREE.SphereGeometry(0.055, 12, 10), M.black, sx * 0.16, 0.1, -face, false);
  body.scale.setScalar(1.3);
  body.position.y = BODY_Y;
  root.add(body);

  // bubble
  const el = document.createElement('div');
  el.className = 'ab';
  el.innerHTML = '<div class="ab-pill"></div><div class="ab-ic"></div>';
  el.addEventListener('click', (e) => { e.stopPropagation(); hooks.onSelect?.(a.id); });
  const label = new CSS2DObject(el);
  label.position.set(0, 2.85, 0);
  root.add(label);

  const phase = (hash(a.id + 'p') % 628) / 100;
  const o = { id: a.id, root, body, mesh, label, el, state: 'idle', phase };
  o.set = (st, task) => {
    o.state = st;
    el.className = 'ab s-' + st;
    el.querySelector('.ab-ic').innerHTML = ICONS[st] || '';
    el.querySelector('.ab-ic').style.background = STATES[st].color;
    const pill = el.querySelector('.ab-pill');
    pill.textContent = ACTIVE.includes(st) ? truncate(task, 40) : '';
    pill.style.display = ACTIVE.includes(st) && task ? '' : 'none';
    el.title = a.name;
  };
  return o;
}

function desk(p, x, z, a) {
  box(p, 2.5, 0.1, 1.1, M.white, x, 1.05, z);
  box(p, 0.08, 1.0, 0.9, M.white, x - 1.1, 0.5, z);
  box(p, 0.08, 1.0, 0.9, M.white, x + 1.1, 0.5, z);
  box(p, 2.3, 0.6, 0.06, M.gray, x, 0.7, z - 0.4);
  // monitor facing +z
  const mg = new THREE.Group();
  box(mg, 0.4, 0.04, 0.25, M.black, 0, 0, 0);
  box(mg, 0.06, 0.3, 0.06, M.black, 0, 0.17, 0);
  box(mg, 1.0, 0.62, 0.06, M.black, 0, 0.6, 0);
  const sm = new THREE.MeshStandardMaterial({ color: '#23262e', roughness: 0.3, emissive: '#000' });
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.52), sm);
  scr.position.set(0, 0.6, 0.035);
  mg.add(scr);
  mg.position.set(x, 1.1, z - 0.15);
  mg.rotation.y = (hash(a.id) % 7 - 3) * 0.03;
  p.add(mg);
  // keyboard + mug
  box(p, 0.7, 0.03, 0.22, M.gray, x, 1.12, z + 0.25, false);
  return sm;
}


/* white block with dark vertical window strips on all four faces; origin at the bottom */
function facade(parent, W, D, h, storeys) {
  box(parent, W, h, D, M.facade, 0, h / 2, 0);
  const sh = h / storeys, stripH = storeys > 1 ? sh - 1.4 : h - 2;
  const n = Math.floor(W / 1.05), nd = Math.floor(D / 1.05);
  const inst = new THREE.InstancedMesh(new THREE.BoxGeometry(0.55, stripH, 0.06), M.win, (n + nd) * 2 * storeys);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), one = new THREE.Vector3(1, 1, 1), yAxis = new THREE.Vector3(0, 1, 0);
  let k = 0;
  for (let st = 0; st < storeys; st++) {
    const cy = st * sh + sh / 2;
    for (const [len, cnt, fixed, rot] of [[W, n, D / 2, 0], [W, n, -D / 2, 0], [D, nd, W / 2, Math.PI / 2], [D, nd, -W / 2, Math.PI / 2]]) {
      q.setFromAxisAngle(yAxis, rot);
      const sign = fixed > 0 ? 1 : -1;
      for (let j = 0; j < cnt; j++) {
        const u = -len / 2 + (j + 0.5) * (len / cnt);
        const pos = rot ? new THREE.Vector3(fixed + sign * 0.01, cy, u) : new THREE.Vector3(u, cy, fixed + sign * 0.01);
        inst.setMatrixAt(k++, m4.compose(pos, q, one));
      }
    }
  }
  inst.count = k;
  parent.add(inst);
}

/* ---------- main ---------- */
export function createScene(container, hooks = {}) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setClearColor('#ffffff');
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.domElement.style.touchAction = 'none';
  container.appendChild(renderer.domElement);

  const labelR = new CSS2DRenderer();
  Object.assign(labelR.domElement.style, { position: 'absolute', inset: '0', pointerEvents: 'none', overflow: 'hidden' });
  container.appendChild(labelR.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#ffffff');
  scene.add(new THREE.HemisphereLight('#ffffff', '#d9dce3', 1.05));
  const sun = new THREE.DirectionalLight('#ffffff', 1.6);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  const sc = sun.shadow.camera;
  sc.left = -34; sc.right = 34; sc.top = 34; sc.bottom = -34; sc.near = 1; sc.far = 120;
  sun.shadow.radius = 5;
  sun.shadow.bias = -0.0004;
  sun.shadow.normalBias = 0.03;
  scene.add(sun, sun.target);

  const ground = new THREE.Mesh(new THREE.PlaneGeometry(300, 300), new THREE.ShadowMaterial({ opacity: 0.12 }));
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -SLAB - BASE_H - 0.02;
  ground.receiveShadow = true;
  scene.add(ground);

  const camera = new THREE.OrthographicCamera(-10, 10, 10, -10, -200, 400);
  const dir = new THREE.Vector3(1, 1, 1).normalize();
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.minZoom = 0.2;
  controls.maxZoom = 3.2;
  controls.minPolarAngle = 0.25;
  controls.maxPolar = 1.4;
  controls.maxPolarAngle = 1.4;
  controls.zoomSpeed = 0.9;
  controls.rotateSpeed = 0.7;
  controls.target.set(0, 1.5, 0);
  camera.position.copy(controls.target).addScaledVector(dir, 80);
  camera.zoom = 0.95;

  const isMobile = () => container.clientWidth < 768;
  let fitW = 0, fitH = 0;
  function fitZoom(force) {
    const w = container.clientWidth || 1, h = container.clientHeight || 1;
    if (!force && w === fitW && h === fitH) return;
    fitW = w; fitH = h;
    const asp = w / h, hh = Math.max(11, 15 / asp);
    const mob = isMobile();
    const spanX = (W + D) * 0.707, spanY = (W + D) * 0.408 + 6;
    const z = Math.min((mob ? 0.9 : 0.78) * 2 * hh * asp / spanX, (mob ? 0.7 : 0.8) * 2 * hh / spanY);
    camera.zoom = THREE.MathUtils.clamp(z, controls.minZoom, mob ? controls.maxZoom : 1.25);
    camera.updateProjectionMatrix();
  }

  function resize() {
    const w = container.clientWidth || 1, h = container.clientHeight || 1;
    renderer.setSize(w, h);
    labelR.setSize(w, h);
    const asp = w / h, hh = Math.max(11, 15 / asp);
    camera.left = -hh * asp; camera.right = hh * asp; camera.top = hh; camera.bottom = -hh;
    camera.updateProjectionMatrix();
    fitZoom();
  }
  let floorsData = [], agentsData = [], sig = '', W = 18, D = 12, cols = 2;
  let built = []; // per floor
  let baseGroup = null;
  let active = 0;
  let tween = null;
  let tour = false;
  const agentObjs = new Map();
  new ResizeObserver(resize).observe(container);
  resize();

  function clearBuilt() {
    tvs.clear();
    for (const f of built) {
      scene.remove(f.group);
      f.group.traverse((o) => { if (o.geometry && !o.userData.shared) o.geometry.dispose(); });
    }
    for (const o of agentObjs.values()) o.el.remove();
    built = [];
    if (baseGroup) { scene.remove(baseGroup); baseGroup.traverse((o) => o.geometry?.dispose()); baseGroup = null; }
    agentObjs.clear();
  }

  function buildFloor(i, floor, list) {
    const group = new THREE.Group();
    group.position.y = i * FH;
    scene.add(group);
    // slab + closed body
    const slab = box(group, W, SLAB, D, M.facade, 0, -SLAB / 2, 0);
    const body = new THREE.Group();
    facade(body, W, D, FH - SLAB, 1);
    group.add(body);

    // open floor
    const open = new THREE.Group();
    group.add(open);
    const sides = {};
    const defs = {
      nz: { n: [0, -1], len: W, pos: [0, -D / 2], rot: 0 },
      pz: { n: [0, 1], len: W, pos: [0, D / 2], rot: 0 },
      nx: { n: [-1, 0], len: D, pos: [-W / 2, 0], rot: Math.PI / 2 },
      px: { n: [1, 0], len: D, pos: [W / 2, 0], rot: Math.PI / 2 },
    };
    for (const [key, d] of Object.entries(defs)) {
      const wall = new THREE.Group();
      const rail = railing(d.len);
      const inset = 0.14;
      const wx = d.pos[0] - d.n[0] * (0.15), wz = d.pos[1] - d.n[1] * 0.15;
      const w = box(wall, d.rot ? 0.3 : d.len, WALL_H, d.rot ? d.len : 0.3, M.wall, wx, WALL_H / 2, wz);
      w.receiveShadow = true;
      rail.position.set(d.pos[0] - d.n[0] * inset, 0, d.pos[1] - d.n[1] * inset);
      rail.rotation.y = d.rot;
      open.add(wall, rail);
      sides[key] = { n: d.n, wall, rail };
    }
    // wall decor
    const innerZ = -D / 2 + 0.3, innerX = -W / 2 + 0.3;
    const letters = new THREE.Mesh(new THREE.PlaneGeometry(7, 1.75), new THREE.MeshBasicMaterial({ map: letterTex(floorsData.length === 1 ? 'Office Bot' : floor.name, floorsData.length === 1 ? floor.name : 'Floor ' + (i + 1)), transparent: true }));
    letters.position.set(W / 2 - 5, 2.9, innerZ + 0.02);
    sides.nz.wall.add(letters);
    const clk = clock(sides.nz.wall, -4, 2.9);
    clk.position.z = innerZ + 0.05;
    const t = tv(sides.nx.wall, 2.7);
    t.position.x = innerX + 0.06; t.position.z = -0.5;
    t.rotation.y = Math.PI / 2;
    // counter + shelf
    box(open, 6.2, 0.95, 1.0, M.white, -4, 0.475, innerZ + 0.7);
    box(open, 6.2, 0.04, 1.04, M.gray, -4, 0.96, innerZ + 0.7, false);
    rbox(open, 0.7, 1.0, 0.7, 0.1, M.black, -2.4, 1.5, innerZ + 0.7);
    for (const [cx, c] of [[-6, '#f2994a'], [-5.6, '#4c8dff'], [-5.2, '#f2c94c']]) rbox(open, 0.22, 0.28, 0.22, 0.05, mat(c), cx, 1.12, innerZ + 0.6);
    box(open, 2.6, 0.06, 0.4, M.white, 1.6, 2.2, innerZ + 0.2);
    // plants, sofas
    plant(open, -W / 2 + 1.1, -D / 2 + 1.5, 1.1);
    plant(open, W / 2 - 1.2, -D / 2 + 1.4, 0.9);
    plant(open, W / 2 - 1.2, D / 2 - 1.4, 1.0);
    plant(open, -W / 2 + 1.1, D / 2 - 1.4, 0.8);
    sofa(open, W / 2 - 2.2, -0.5, Math.PI / 2 + Math.PI, 3.2);
    ottoman(open, W / 2 - 4.2, -1.6, 0.3);
    ottoman(open, W / 2 - 4.2, 0.8, -0.2);
    rbox(open, 1.2, 0.04, 1.2, 0.02, M.gray, W / 2 - 4.2, 0.62, -0.4).rotation.y = 0.3;

    // agents
    const objs = [];
    list.forEach((a, idx) => {
      const col = idx % cols, row = Math.floor(idx / cols);
      const x = -W / 2 + 3.8 + col * SP;
      const dz = -D / 2 + 4.0 + row * RP;
      const sm = desk(open, x, dz, a);
      const o = makeAgent(a, hooks);
      o.root.position.set(x, 0, dz + 1.25);
      o.screen = sm;
      open.add(o.root);
      objs.push(o);
      agentObjs.set(a.id, o);
    });
    const fl = { group, slab, body, open, sides, objs, clock: clk, y: i * FH };
    built.push(fl);
    return fl;
  }

  function rebuild() {
    clearBuilt();
    const by = floorsData.map(() => []);
    for (const a of agentsData) by[a.floor]?.push(a);
    const n = Math.max(1, ...by.map((l) => l.length));
    cols = Math.max(2, Math.min(8, Math.ceil(Math.sqrt(n * 1.4))));
    const rows = Math.ceil(n / cols);
    W = Math.max(18, cols * SP + 9);
    D = Math.max(12, 8.1 + (rows - 1) * RP);
    const half = Math.max(W, D) * 0.75 + 8;
    sc.left = -half; sc.right = half; sc.top = half; sc.bottom = -half; sc.far = 220;
    sc.updateProjectionMatrix();
    baseGroup = new THREE.Group();
    baseGroup.position.y = -SLAB - BASE_H;
    facade(baseGroup, W, D, BASE_H, 3);
    scene.add(baseGroup);
    floorsData.forEach((f, i) => buildFloor(i, f, by[i]));
    fitZoom(true);
    applyVisibility();
  }

  function applyVisibility() {
    built.forEach((f, i) => {
      f.group.visible = i <= active;
      f.body.visible = i < active;
      f.open.visible = i === active;
      for (const o of f.objs) o.label.visible = i === active;
    });
  }

  function updateStates() {
    for (const a of agentsData) {
      const o = agentObjs.get(a.id);
      if (!o) continue;
      o.set(a.state, a.task);
      o.screen.emissive.set(a.state === 'working' ? '#1d4a30' : a.state === 'idle' ? '#000000' : '#233a55');
    }
  }

  function setData(floors, agents) {
    floorsData = floors;
    agentsData = agents;
    const s = floors.map((f) => f.id).join(',') + '|' + agents.map((a) => a.id + ':' + a.floor + ':' + a.colorHex).join(',');
    if (s !== sig) { sig = s; rebuild(); }
    updateStates();
    if (active >= floors.length) setFloor(floors.length - 1, false);
  }

  function setFloor(i, animate = true) {
    active = Math.max(0, i);
    applyVisibility();
    const ty = active * FH + 1.5;
    sun.position.set(-12, active * FH + 26, 10);
    sun.target.position.set(0, active * FH, 0);
    const total = ty - controls.target.y;
    if (!animate || reduced || Math.abs(total) < 0.01) {
      camera.position.y += total; controls.target.y += total; tween = null;
    } else {
      tween = { t0: performance.now(), total, done: 0, dur: 900 };
    }
  }

  /* picking */
  const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
  let down = null;
  renderer.domElement.addEventListener('pointerdown', (e) => { down = { x: e.clientX, y: e.clientY }; });
  renderer.domElement.addEventListener('pointerup', (e) => {
    if (!down || Math.hypot(e.clientX - down.x, e.clientY - down.y) > 5) return;
    const r = renderer.domElement.getBoundingClientRect();
    ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ndc, camera);
    const f = built[active];
    if (!f) return;
    const hit = ray.intersectObjects(f.objs.map((o) => o.root), true)[0];
    if (hit) {
      let p = hit.object;
      while (p && !p.userData.agentId) p = p.parent;
      if (p) hooks.onSelect?.(p.userData.agentId);
    }
  });
  renderer.domElement.addEventListener('pointermove', (e) => {
    if (e.buttons || e.pointerType === 'touch') return;
    const r = renderer.domElement.getBoundingClientRect();
    ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ndc, camera);
    const f = built[active];
    renderer.domElement.style.cursor = f && ray.intersectObjects(f.objs.map((o) => o.root), true).length ? 'pointer' : '';
  });

  /* WASD */
  const keys = new Set();
  addEventListener('keydown', (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey || /input|textarea|select/i.test(e.target.tagName) || !container.matches(':hover')) return;
    const k = e.key.toLowerCase();
    if ('wasd'.includes(k) && k.length === 1) keys.add(k);
  });
  addEventListener('keyup', (e) => keys.delete(e.key.toLowerCase()));
  addEventListener('blur', () => keys.clear());


  /* screen-space collision avoidance: nudge task pills upward so they never cover each other or other agents' status icons */
  const wp = new THREE.Vector3();
  function avoidPills(f) {
    const w = container.clientWidth, h = container.clientHeight;
    const items = [];
    for (const o of f.objs) {
      o.label.getWorldPosition(wp).project(camera);
      const sx = ((wp.x + 1) / 2) * w, sy = ((1 - wp.y) / 2) * h;
      const pill = o.el.firstChild;
      const pw = pill.style.display !== 'none' ? pill.offsetWidth : 0;
      items.push({ o, pill, sx, sy, pw, ph: pill.offsetHeight || 28 });
    }
    const icons = items.map((it) => ({ x0: it.sx - 13, x1: it.sx + 13, y0: it.sy - 13, y1: it.sy + 13, it }));
    const placed = [];
    items.sort((a, b) => b.sy - a.sy);
    for (const it of items) {
      if (!it.pw) { it.pill.style.transform = ''; it.o.el.style.setProperty('--lead', '0px'); continue; }
      const half = it.pw / 2;
      const base = it.sy - 18; // default: just above the icon
      let bottom = base;
      for (let n = 0; n < 40; n++) {
        const r = { x0: it.sx - half - 3, x1: it.sx + half + 3, y0: bottom - it.ph - 3, y1: bottom + 3 };
        const hit = placed.find((p) => r.x0 < p.x1 && r.x1 > p.x0 && r.y0 < p.y1 && r.y1 > p.y0)
          || icons.find((c) => c.it !== it && r.x0 < c.x1 && r.x1 > c.x0 && r.y0 < c.y1 && r.y1 > c.y0);
        if (!hit) break;
        bottom = hit.y0 - 3;
      }
      placed.push({ x0: it.sx - half - 3, x1: it.sx + half + 3, y0: bottom - it.ph - 3, y1: bottom + 3 });
      const dy = bottom - base;
      it.pill.style.transform = `translate(-50%, ${dy}px)`;
      it.o.el.style.setProperty('--lead', dy < -2 ? `${-dy + 6}px` : '0px');
    }
  }

  const fwd = new THREE.Vector3(), right = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0);
  const clockT = new THREE.Clock();
  let lastTick = 0;

  function frame() {
    const dt = Math.min(clockT.getDelta(), 0.1), t = clockT.elapsedTime;
    if (keys.size) {
      fwd.subVectors(controls.target, camera.position).setY(0).normalize();
      right.crossVectors(fwd, up);
      const sp = (14 / camera.zoom) * dt;
      const mv = new THREE.Vector3();
      if (keys.has('w')) mv.add(fwd);
      if (keys.has('s')) mv.sub(fwd);
      if (keys.has('d')) mv.add(right);
      if (keys.has('a')) mv.sub(right);
      mv.multiplyScalar(sp);
      camera.position.add(mv); controls.target.add(mv);
    }
    if (tween) {
      const p = Math.min(1, (performance.now() - tween.t0) / tween.dur);
      const e = p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
      const d = e * tween.total - tween.done;
      tween.done += d;
      camera.position.y += d; controls.target.y += d;
      if (p >= 1) tween = null;
    }
    controls.target.x = THREE.MathUtils.clamp(controls.target.x, -W, W);
    controls.target.z = THREE.MathUtils.clamp(controls.target.z, -D, D);
    controls.autoRotate = tour;
    controls.autoRotateSpeed = 1.2;
    controls.update();

    const f = built[active];
    if (f) {
      // hide walls facing the camera, show railings instead
      const vx = camera.position.x - controls.target.x, vz = camera.position.z - controls.target.z;
      for (const s of Object.values(f.sides)) {
        const facing = s.n[0] * vx + s.n[1] * vz > 0;
        s.wall.visible = !facing;
        s.rail.visible = facing;
      }
      const amp = reduced ? 0.15 : 1;
      for (const o of f.objs) {
        const s = o.state, ph = o.phase;
        let y = 0, rz = 0, rx = 0, px = 0;
        if (s === 'working') { y = Math.abs(Math.sin(t * 7 + ph)) * 0.05; rz = Math.sin(t * 13 + ph) * 0.03; }
        else if (s === 'finished') { y = Math.abs(Math.sin(t * 2.4 + ph)) * 0.06; }
        else if (s === 'needs-you') { rz = Math.sin(t * 7 + ph) * 0.1; y = Math.abs(Math.sin(t * 3.5 + ph)) * 0.04; }
        else if (s === 'stuck') { px = Math.sin(t * 30 + ph) * 0.012; }
        else { y = (Math.sin(t * 1.4 + ph) + 1) * 0.012; }
        o.body.position.set(px * amp, BODY_Y + y * amp, 0);
        o.body.rotation.z = rz * amp;
        o.body.rotation.x = rx;
      }
      if (t - lastTick > 0.5) { lastTick = t; f.clock.userData.tick?.(); }
    }
    renderer.render(scene, camera);
    labelR.render(scene, camera);
    if (f) avoidPills(f);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  return {
    setStats(st) {
      tvStats = { ...tvStats, ...st };
      for (const t of tvs) { const c = t.image; drawTv(c.getContext('2d'), c.width, c.height); t.needsUpdate = true; }
    },
    resize,
    setData,
    setFloor,
    setTour(v) { tour = !!v; },
    zoomBy(k) {
      camera.zoom = THREE.MathUtils.clamp(camera.zoom * k, controls.minZoom, controls.maxZoom);
      camera.updateProjectionMatrix();
    },
  };
}
