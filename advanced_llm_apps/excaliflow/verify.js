const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

const htmlPath = path.join(__dirname, 'index.html');
const html = fs.readFileSync(htmlPath, 'utf8');

const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
assert(scriptMatch, 'Could not find <script> block in index.html');
const scriptCode = scriptMatch[1];

// Instrumented Path2D that records every point added to it
class MockPath2D {
  constructor() {
    this.ops = [];
    this.points = [];
  }
  moveTo(x, y) {
    this.ops.push({ type: 'moveTo', x, y });
    this.points.push({ x, y });
  }
  lineTo(x, y) {
    this.ops.push({ type: 'lineTo', x, y });
    this.points.push({ x, y });
  }
  quadraticCurveTo(cpx, cpy, x, y) {
    this.ops.push({ type: 'quadraticCurveTo', cpx, cpy, x, y });
    this.points.push({ x: cpx, y: cpy }, { x, y });
  }
  bezierCurveTo(cp1x, cp1y, cp2x, cp2y, x, y) {
    this.ops.push({ type: 'bezierCurveTo', cp1x, cp1y, cp2x, cp2y, x, y });
    this.points.push({ x: cp1x, y: cp1y }, { x: cp2x, y: cp2y }, { x, y });
  }
  ellipse(cx, cy, rx, ry, rot, start, end) {
    this.ops.push({ type: 'ellipse', cx, cy, rx, ry, rot, start, end });
  }
  closePath() {
    this.ops.push({ type: 'closePath' });
  }
}

function createMockCtx() {
  const calls = [];
  const fontsUsed = [];
  let currentFont = '';
  return {
    calls,
    fontsUsed,
    get font() { return currentFont; },
    set font(v) { currentFont = v; fontsUsed.push(v); },
    save() { calls.push({ fn: 'save' }); },
    restore() { calls.push({ fn: 'restore' }); },
    beginPath() { calls.push({ fn: 'beginPath' }); },
    closePath() { calls.push({ fn: 'closePath' }); },
    moveTo(x, y) { calls.push({ fn: 'moveTo', x, y }); },
    lineTo(x, y) { calls.push({ fn: 'lineTo', x, y }); },
    quadraticCurveTo(cpx, cpy, x, y) { calls.push({ fn: 'quadraticCurveTo', cpx, cpy, x, y }); },
    bezierCurveTo(a, b, c, d, e, f) { calls.push({ fn: 'bezierCurveTo', a, b, c, d, e, f }); },
    arcTo(x1, y1, x2, y2, r) { calls.push({ fn: 'arcTo', x1, y1, x2, y2, r }); },
    arc(x, y, r, s, e) { calls.push({ fn: 'arc', x, y, r, s, e }); },
    ellipse(x, y, rx, ry) { calls.push({ fn: 'ellipse', x, y, rx, ry }); },
    fill(pathObj) { calls.push({ fn: 'fill', pathObj }); },
    stroke(pathObj) { calls.push({ fn: 'stroke', pathObj }); },
    clip(pathObj) { calls.push({ fn: 'clip', pathObj }); },
    fillRect(x, y, w, h) { calls.push({ fn: 'fillRect', x, y, w, h }); },
    strokeRect(x, y, w, h) { calls.push({ fn: 'strokeRect', x, y, w, h }); },
    clearRect(x, y, w, h) { calls.push({ fn: 'clearRect', x, y, w, h }); },
    setLineDash(d) { calls.push({ fn: 'setLineDash', d }); },
    setTransform() {},
    scale() {},
    translate() {},
    fillText(text, x, y) { calls.push({ fn: 'fillText', text, x, y, font: currentFont }); },
    measureText(text) { return { width: String(text || '').length * 8.5 }; }
  };
}

const mockCanvas = {
  width: 1440,
  height: 900,
  style: {},
  attrs: {},
  setAttribute(k, v) { this.attrs[k] = v; },
  getAttribute(k) { return this.attrs[k]; },
  getContext: () => createMockCtx(),
  addEventListener: () => {}
};

const sandbox = {
  console,
  Math,
  Number,
  String,
  Boolean,
  Array,
  Object,
  Set,
  Map,
  Float64Array,
  JSON,
   Path2D: MockPath2D,
  performance: { now: () => 1234.5 },
  requestAnimationFrame: () => 1,
  setTimeout: () => 1,
  clearTimeout: () => {},
  setInterval: () => 1,
  clearInterval: () => {},
  window: {
    innerWidth: 1440,
    innerHeight: 900,
    devicePixelRatio: 2,
    addEventListener: () => {},
    localStorage: {
      _store: new Map(),
      getItem(k) { return this._store.has(k) ? this._store.get(k) : null; },
      setItem(k, v) { this._store.set(k, String(v)); },
      removeItem(k) { this._store.delete(k); }
    }
  },
  document: {
    body: { classList: { toggle: () => {} } },
    getElementById: () => ({
      width: 1440,
      height: 900,
      style: {},
      children: [],
      classList: { toggle: () => {}, add: () => {}, remove: () => {}, contains: () => false },
      addEventListener: () => {},
      appendChild: () => {},
      getContext: () => createMockCtx()
    }),
    querySelectorAll: () => [],
    createElement: () => mockCanvas
  }
};

console.log('--- Excaliflow Automated Verification Suite ---');
assert(html.includes('Excaliflow') && !html.includes('AtelierFlow'), 'index.html should use Excaliflow branding everywhere');

// 1. Verify Zero Syntax or Runtime Initialization Errors
vm.createContext(sandbox);
vm.runInContext(scriptCode, sandbox);
sandbox.initStudioDOM();
const app = sandbox.window;
assert(app.state.elements.length > 0, 'Initial template should populate elements');
console.log('[PASS] 1. Zero syntax or runtime initialization errors (initial scene loaded)');

// 2. Verify Zero-Bleed Analytical Hachure & Cross-Hatch Clipping + ctx.clip(paths.fillPath)
for (const fillStyle of ['hachure', 'cross-hatch']) {
  const ellipseEl = app.createElement('ellipse', {
    x: 120,
    y: 160,
    width: 180,
    height: 110,
    fillStyle,
    roughness: 1.75
  });
  const ellipsePaths = app.ShapeCache.generate(ellipseEl);
  assert(ellipsePaths.hachurePath.points.length > 10, `Ellipse ${fillStyle} should generate hatch points`);

  const ecx = ellipseEl.x + ellipseEl.width / 2;
  const ecy = ellipseEl.y + ellipseEl.height / 2;
  const erx = ellipseEl.width / 2;
  const ery = ellipseEl.height / 2;
  for (const pt of ellipsePaths.hachurePath.points) {
    const normDist = ((pt.x - ecx) / erx) ** 2 + ((pt.y - ecy) / ery) ** 2;
    assert(
      normDist <= 1.0001,
      `Ellipse ${fillStyle} point (${pt.x.toFixed(2)}, ${pt.y.toFixed(2)}) bled outside boundary: normDist=${normDist}`
    );
  }

  const diamondEl = app.createElement('diamond', {
    x: 340,
    y: 160,
    width: 190,
    height: 120,
    fillStyle,
    roughness: 1.75
  });
  const diamondPaths = app.ShapeCache.generate(diamondEl);
  assert(diamondPaths.hachurePath.points.length > 10, `Diamond ${fillStyle} should generate hatch points`);

  const dcx = diamondEl.x + diamondEl.width / 2;
  const dcy = diamondEl.y + diamondEl.height / 2;
  const dhw = diamondEl.width / 2;
  const dhh = diamondEl.height / 2;
  for (const pt of diamondPaths.hachurePath.points) {
    const l1Dist = Math.abs(pt.x - dcx) / dhw + Math.abs(pt.y - dcy) / dhh;
    assert(
      l1Dist <= 1.0001,
      `Diamond ${fillStyle} point (${pt.x.toFixed(2)}, ${pt.y.toFixed(2)}) bled outside boundary: l1Dist=${l1Dist}`
    );
  }

  // Verify drawStaticElement calls ctx.clip(paths.fillPath) before stroking hachurePath
  const testCtx = createMockCtx();
  const cached = app.ShapeCache.get(ellipseEl);
  app.drawStaticElement(testCtx, ellipseEl);
  const clipIdx = testCtx.calls.findIndex(c => c.fn === 'clip' && c.pathObj === cached.fillPath);
  const hachureStrokeIdx = testCtx.calls.findIndex(c => c.fn === 'stroke' && c.pathObj === cached.hachurePath);
  assert(clipIdx !== -1, 'drawStaticElement must invoke ctx.clip(paths.fillPath)');
  assert(hachureStrokeIdx > clipIdx, 'hachurePath stroke must occur after ctx.clip(paths.fillPath)');
}
console.log('[PASS] 2. Zero-bleed analytical interior clipping & double-safety ctx.clip(paths.fillPath) verified');

// 3. Verify 1-Click Unselected Arrow Endpoint Grabbing, Perimeter Sliding (focusAngle) & Cross-Shape Rebinding
app.state.elements = [];
app.state.selectedIds.clear();
app.state.zoom = 1;

const boxA = app.createElement('rectangle', { id: 'node_A', x: 100, y: 200, width: 140, height: 80, text: 'Node A' });
const boxB = app.createElement('rectangle', { id: 'node_B', x: 420, y: 200, width: 140, height: 80, text: 'Node B' });
const boxC = app.createElement('ellipse',   { id: 'node_C', x: 420, y: 380, width: 150, height: 90, text: 'Node C' });
const arrowAB = app.createElement('arrow', {
  id: 'arrow_AB',
  x: 240,
  y: 240,
  x2: 420,
  y2: 240,
  startBinding: { elementId: 'node_A', focusAngle: 0, gap: 4 },
  endBinding: { elementId: 'node_B', focusAngle: Math.PI, gap: 4 }
});
app.state.elements.push(boxA, boxB, boxC, arrowAB);

// Ensure arrowAB is NOT selected initially
assert(!app.state.selectedIds.has('arrow_AB'), 'Arrow should start unselected');
const geomAB = app.getArrowGeometry(arrowAB);
const hitEnd = app.hitTestArrowHandle(geomAB.p1.x + 6, geomAB.p1.y - 4);
assert(hitEnd && hitEnd.elementId === 'arrow_AB' && hitEnd.handle === 'end', 'hitTestArrowHandle must grab unselected arrow endpoint');

// Verify computeBindingForShape & getBindingBoundaryPoint slide across top and bottom perimeters
const topPt = { x: boxB.x + boxB.width / 2, y: boxB.y - 2 };
const bindTop = app.computeBindingForShape(boxB, topPt);
assert(Math.abs(bindTop.focusAngle - (-Math.PI / 2)) < 0.05, 'Top perimeter focusAngle should be ~ -PI/2');
const boundTopPt = app.getBindingBoundaryPoint(boxB, bindTop, geomAB.p0, 4);
assert(Math.abs(boundTopPt.y - (boxB.y - 4)) < 1.5, 'Boundary point should lie on top edge of boxB');

const bottomPt = { x: boxB.x + boxB.width / 2, y: boxB.y + boxB.height + 2 };
const bindBottom = app.computeBindingForShape(boxB, bottomPt);
assert(Math.abs(bindBottom.focusAngle - (Math.PI / 2)) < 0.05, 'Bottom perimeter focusAngle should be ~ +PI/2');
const boundBottomPt = app.getBindingBoundaryPoint(boxB, bindBottom, geomAB.p0, 4);
assert(Math.abs(boundBottomPt.y - (boxB.y + boxB.height + 4)) < 1.5, 'Boundary point should lie on bottom edge of boxB');

// Drag arrowAB's end handle from boxB across to boxC
app.setTool('select');
app.pointerDownWorld(geomAB.p1.x, geomAB.p1.y);
app.pointerMoveWorld(boxC.x + 8, boxC.y + boxC.height / 2);
app.pointerUpWorld(boxC.x + 8, boxC.y + boxC.height / 2);
assert.strictEqual(arrowAB.endBinding?.elementId, 'node_C', 'Dragging arrow endpoint onto Node C must rebind endBinding.elementId');
console.log('[PASS] 3. 1-click unselected arrow endpoint grabbing, perimeter sliding (focusAngle), and cross-shape rebinding verified');

// 4. Verify Direct Bound-Arrow Middle Drag in Select Mode Updates arrow.curveOffset
arrowAB.curveOffset = 0;
const currentGeom = app.getArrowGeometry(arrowAB);
const midPt = currentGeom.curveHandlePt;
app.state.selectedIds.clear(); // Even without prior selection, clicking & dragging bound arrow shaft in Select mode bends curve
app.pointerDownWorld(midPt.x, midPt.y);
app.pointerMoveWorld(midPt.x - 50, midPt.y + 50);
app.pointerUpWorld(midPt.x - 50, midPt.y + 50);
assert(Math.abs(arrowAB.curveOffset) > 40, `Expected arrow.curveOffset to update when dragging middle shaft, got ${arrowAB.curveOffset}`);

// Verify Straight, Elbow (including L-bend arrowhead angle & 1:1 handle tracking), and Curved switching
app.state.selectedIds.clear();
app.state.selectedIds.add(arrowAB.id);
app.applyStyleProperty('curveType', 'straight');
assert.strictEqual(arrowAB.curveType, 'straight', 'Arrow should switch to straight');
assert.strictEqual(arrowAB.curveOffset, 0, 'Switching to straight must reset curveOffset to 0');

app.applyStyleProperty('curveType', 'elbow');
assert.strictEqual(arrowAB.curveType, 'elbow', 'Arrow should switch to elbow');
assert.strictEqual(arrowAB.curveOffset, 0, 'Switching to elbow must reset curveOffset to 0');

// Drag elbow handle to x = 460 and verify 1:1 horizontal tracking (not inverted)
const elbowGeom0 = app.getArrowGeometry(arrowAB);
app.pointerDownWorld(elbowGeom0.curveHandlePt.x, elbowGeom0.curveHandlePt.y);
app.pointerMoveWorld(460, elbowGeom0.curveHandlePt.y);
app.pointerUpWorld(460, elbowGeom0.curveHandlePt.y);
const elbowGeomDragged = app.getArrowGeometry(arrowAB);
assert(Math.abs(elbowGeomDragged.curveHandlePt.x - 460) < 2, `Elbow handle must track cursor X (460), got ${elbowGeomDragged.curveHandlePt.x}`);

// Drag elbow handle to align with p1.x (forming a 90-degree L-bend going right then straight down)
app.pointerDownWorld(elbowGeomDragged.curveHandlePt.x, elbowGeomDragged.curveHandlePt.y);
app.pointerMoveWorld(elbowGeomDragged.p1.x, elbowGeomDragged.curveHandlePt.y);
app.pointerUpWorld(elbowGeomDragged.p1.x, elbowGeomDragged.curveHandlePt.y);
const lBendGeom = app.getArrowGeometry(arrowAB);
assert.strictEqual(lBendGeom.waypoints.length, 3, 'L-bend elbow should collapse degenerate final segment into 3 waypoints');
assert(Math.abs(lBendGeom.tipAngle - Math.PI / 2) < 0.01, `L-bend vertical shaft must have downward tipAngle (+PI/2), got ${lBendGeom.tipAngle}`);

// Verify dragging elbow handle over startShape (User Task Spec scenario) exits bottom instead of cutting backwards through the shape
app.applyStyleProperty('curveType', 'elbow');
const gBefore = app.getArrowGeometry(arrowAB);
app.pointerDownWorld(gBefore.curveHandlePt.x, gBefore.curveHandlePt.y);
app.pointerMoveWorld(boxA.x + boxA.width / 2, gBefore.curveHandlePt.y);
app.pointerUpWorld(boxA.x + boxA.width / 2, gBefore.curveHandlePt.y);
const gOverStart = app.getArrowGeometry(arrowAB);
assert(Math.abs(gOverStart.p0.y - (boxA.y + boxA.height + 4)) < 2, `Elbow arrow dragged over startShape must exit from bottom of startShape, got p0=(${gOverStart.p0.x}, ${gOverStart.p0.y})`);
for (const wp of gOverStart.waypoints) {
  const insideBoxA = wp.x > boxA.x + 2 && wp.x < boxA.x + boxA.width - 2 && wp.y > boxA.y + 2 && wp.y < boxA.y + boxA.height - 2;
  assert(!insideBoxA, `Elbow waypoint (${wp.x}, ${wp.y}) must never cut through interior of startShape`);
}

// Verify Clean (0), Artist (0.85), and Cartoon (1.75) sloppiness produce clearly distinct multi-pass geometry & apply globally when unselected
const cleanRect = app.ShapeCache.generate(app.createElement('rectangle', { x: 0, y: 0, width: 140, height: 70, roughness: 0 }));
const artistRect = app.ShapeCache.generate(app.createElement('rectangle', { x: 0, y: 0, width: 140, height: 70, roughness: 0.85 }));
const cartoonRect = app.ShapeCache.generate(app.createElement('rectangle', { x: 0, y: 0, width: 140, height: 70, roughness: 1.75 }));
assert(cleanRect.strokePath.ops.length < artistRect.strokePath.ops.length, 'Artist rectangle must have more sketch passes than Clean');
assert(artistRect.strokePath.ops.length < cartoonRect.strokePath.ops.length, 'Cartoon rectangle must have more sketch passes than Artist');
app.state.selectedIds.clear();
app.applyStyleProperty('roughness', 1.75);
assert.strictEqual(boxA.roughness, 1.75, 'Clicking Cartoon with no selection must apply roughness=1.75 to existing canvas shapes');

// Switching from elbow (curveOffset=0) to curved should apply a visible curveOffset
app.state.selectedIds.add(arrowAB.id);
app.applyStyleProperty('curveType', 'straight');
app.applyStyleProperty('curveType', 'curved');
assert(Math.abs(arrowAB.curveOffset) >= 20, `Switching to curved from 0 offset should apply default curveOffset, got ${arrowAB.curveOffset}`);
console.log('[PASS] 4. Direct bound-arrow middle shaft drag + Straight, Elbow (no shape-cutting, L-bend & 1:1 handle), Curved, and Clean/Artist/Cartoon verified');

// 5. Verify Excalidraw Font Families (Excalifont/Virgil, Assistant/Nunito, Cascadia), Unbroken Arrows (no text/gaps), Tool Lock (Q), Laser Pointer (K), Number Shortcuts (1-9, 0), and triggerNodePulse
const fontTestCtx = createMockCtx();
for (const [fam, expectedSubstrs] of [
  ['hand', ['Excalifont', 'Virgil', 'Patrick Hand']],
  ['sans', ['Assistant', 'Nunito', 'Geist']],
  ['code', ['Cascadia', 'Geist Mono']]
]) {
  const fNode = app.createElement('rectangle', { x: 50, y: 50, width: 120, height: 60, text: 'Hello', fontFamily: fam });
  app.drawElementText(fontTestCtx, fNode, { forExport: true });
  const lastFont = fontTestCtx.fontsUsed[fontTestCtx.fontsUsed.length - 1];
  for (const sub of expectedSubstrs) {
    assert(lastFont.includes(sub), `Font family '${fam}' should include '${sub}', got '${lastFont}'`);
  }
}

// Verify arrows never render text or create gaps in between arrows
const arrowWithText = app.createElement('arrow', { x: 100, y: 100, x2: 300, y2: 100, text: 'ShouldNotRender' });
const arrowGeomCheck = app.getArrowGeometry(arrowWithText);
assert.strictEqual(arrowGeomCheck.labelBox, null, 'Arrows must not have labelBox');
assert.strictEqual(arrowGeomCheck.gapStartDist, -1, 'Arrows must not cut gaps in between shafts');
const arrowTextCtx = createMockCtx();
app.drawElementText(arrowTextCtx, arrowWithText, { forExport: true });
assert.strictEqual(arrowTextCtx.calls.filter(c => c.fn === 'fillText').length, 0, 'drawElementText must never write text on arrows');

// Tool Lock ('Q')
assert.strictEqual(app.state.toolLocked, false, 'Tool lock starts false');
app.handleKeyDown({ key: 'q' });
assert.strictEqual(app.state.toolLocked, true, 'Pressing Q should enable toolLock');
app.handleKeyDown({ key: 'q' });
assert.strictEqual(app.state.toolLocked, false, 'Pressing Q again should disable toolLock');

// Laser Pointer ('K')
app.handleKeyDown({ key: 'k' });
assert.strictEqual(app.state.activeTool, 'laser', 'Pressing K should select laser tool');
app.pointerDownWorld(200, 200);
app.pointerMoveWorld(240, 220);
app.pointerUpWorld(240, 220);
assert(app.state.laserPoints.length >= 2, 'Laser tool drag should record glowing trail points');

// Number shortcuts (1-9, 0)
const expectedNumberTools = {
  '1': 'select',
  '2': 'rectangle',
  '3': 'diamond',
  '4': 'ellipse',
  '5': 'arrow',
  '6': 'arrow',
  '7': 'freedraw',
  '8': 'text',
  '9': 'sticky',
  '0': 'eraser'
};
for (const [numKey, expectedTool] of Object.entries(expectedNumberTools)) {
  app.handleKeyDown({ key: numKey });
  assert.strictEqual(app.state.activeTool, expectedTool, `Shortcut '${numKey}' should activate '${expectedTool}'`);
}

// triggerNodePulse
const prevPulseCount = app.state.activePulses.length;
const spawned = app.triggerNodePulse('node_A');
assert(spawned > 0 && app.state.activePulses.length > prevPulseCount, 'triggerNodePulse should spawn active burst packets along outgoing arrows');
assert(html.includes('<span>Excaliflow</span>') && !html.includes('AtelierFlow'), 'Brand name must be Excaliflow everywhere');
console.log('[PASS] 5. Font families (Hand/Sans/Code), Tool Lock (Q), Laser Pointer (K), shortcuts (1-9, 0), and triggerNodePulse verified');

// 6. Verify Port-Wire Drag to Empty Canvas, Undo Stack Click Integrity & Subgraph Cloning
app.setTool('select');
app.state.selectedIds.clear();
app.state.selectedIds.add('node_A');
app.state.history.undoStack = [];
const undoCountBeforeClick = app.state.history.undoStack.length;
// Click on node_A without moving it
app.pointerDownWorld(boxA.x + 20, boxA.y + 20);
app.pointerUpWorld(boxA.x + 20, boxA.y + 20);
assert.strictEqual(app.state.history.undoStack.length, undoCountBeforeClick, 'Clicking a node without moving must not leave a no-op snapshot on undoStack');

// Drag from node_A right quick-connect port onto empty canvas (800, 500)
const rightPortX = boxA.x + boxA.width + 18;
const rightPortY = boxA.y + boxA.height / 2;
const elemCountBeforeWire = app.state.elements.length;
app.pointerDownWorld(rightPortX, rightPortY);
app.pointerMoveWorld(800, 500);
app.pointerUpWorld(800, 500);
assert.strictEqual(app.state.elements.length, elemCountBeforeWire + 2, 'Dragging port-wire onto empty canvas must create a connected node + arrow');

// Clone subgraph and verify internal bindings remap
const cloned = app.cloneElementsWithBindings([boxA, boxC, arrowAB], 40, 40);
assert.strictEqual(cloned.length, 3, 'Should clone 3 elements');
const clonedArrow = cloned.find(c => c.type === 'arrow');
assert(clonedArrow.startBinding.elementId !== 'node_A' && clonedArrow.endBinding.elementId !== 'node_C', 'Cloned arrow bindings must remap to cloned node IDs');
console.log('[PASS] 6. Port-wire drag to empty canvas, no-op click undo guard, and subgraph binding clone verified');

// 7. Verify Untrusted JSON Import Validation, Excalidraw points[] Arrow Import, and server.js Security Guards
const importedOk = app.importExcalidrawJson(JSON.stringify({
  elements: [
    { id: 'imp_box', type: 'rectangle', x: 100, y: 100, width: 140, height: 70, text: 'Valid' },
    { id: 'imp_bad', type: 'script_injection', x: 0, y: 0, width: 50, height: 50 },
    { id: 'imp_arr', type: 'arrow', x: 300, y: 200, points: [[0, 0], [-120, 60]] }
  ],
  appState: {
    flowMode: 'invalid_mode_xyz',
    flowSpeed: 9999
  }
}));
assert.strictEqual(importedOk, true, 'importExcalidrawJson should succeed on valid JSON payload');
assert.strictEqual(app.state.elements.length, 2, 'Untrusted element types must be filtered out on import');
const impArr = app.state.elements.find(e => e.id === 'imp_arr');
assert.strictEqual(impArr.x2, 180, 'Excalidraw arrow points[[0,0],[-120,60]] must resolve x2 = x - 120');
assert.strictEqual(impArr.y2, 260, 'Excalidraw arrow points[[0,0],[-120,60]] must resolve y2 = y + 60');
assert.notStrictEqual(app.state.flowMode, 'invalid_mode_xyz', 'Invalid flowMode must be rejected');
assert.strictEqual(app.state.flowSpeed, 5, 'Out-of-bounds flowSpeed must be clamped to <= 5.0');

// Test server.js request handling & security guards in-memory
const server = require('./server.js');
function runMockReq(method, url) {
  let statusCode = 200;
  let headers = {};
  let body = '';
  const req = { method, url };
  const res = {
    writeHead(code, hdrs) { statusCode = code; headers = hdrs || {}; },
    end(chunk) { if (chunk) body += Buffer.isBuffer(chunk) ? chunk.toString('utf8') : String(chunk); }
  };
  server.emit('request', req, res);
  return new Promise(resolve => setTimeout(() => resolve({ statusCode, headers, body }), 25));
}

(async () => {
  const postRes = await runMockReq('POST', '/index.html');
  assert.strictEqual(postRes.statusCode, 405, 'POST requests must be rejected with 405');

  const badUriRes = await runMockReq('GET', '/%E0%A4%A');
  assert.strictEqual(badUriRes.statusCode, 400, 'Malformed URI encoding must return 400');

  const travRes = await runMockReq('GET', '/../package.json');
  assert.strictEqual(travRes.statusCode, 403, 'Path traversal outside ROOT must return 403');

  const headRes = await runMockReq('HEAD', '/');
  assert.strictEqual(headRes.statusCode, 200, 'HEAD / must return 200');
  assert.strictEqual(headRes.body, '', 'HEAD / response must have empty body');
  assert(Number(headRes.headers['Content-Length']) > 1000, 'HEAD / must include Content-Length');

  console.log('[PASS] 7. Untrusted JSON import validation, Excalidraw arrow points[] import, and server.js security verified');

  // 8. Verify Multi-Canvas Tabs, Fork/Duplicate, Shortcuts, LocalStorage Auto-Save & Multi-Tab JSON
  assert(app.state.tabs.length >= 1, 'Workspace should initialize with at least 1 tab');
  const firstTabId = app.state.activeTabId;
  app.renameCanvasTab(firstTabId, 'System Overview');
  assert.strictEqual(app.state.tabs[0].name, 'System Overview', 'renameCanvasTab should update tab name');
  const firstTabElemCount = app.state.elements.length;

  // Create a second blank tab and add a node in dark mode
  const secondTab = app.createCanvasTab({ name: 'Worker Subflow', canvasBg: '#000000' });
  assert.strictEqual(app.state.tabs.length, 2, 'createCanvasTab should add a second tab');
  assert.strictEqual(app.state.activeTabId, secondTab.id, 'New tab should become active');
  assert.strictEqual(app.state.elements.length, 0, 'New blank tab should start with 0 elements');
  assert.strictEqual(app.state.canvasBg, '#000000', 'New tab should apply its canvasBg');
  app.quickAddShape('diamond');
  assert.strictEqual(app.state.elements.length, 1, 'Adding a shape on Tab 2 should populate Tab 2');

  // Duplicate / Fork Tab 2 -> Tab 3
  const forkedTab = app.duplicateCanvasTab(secondTab.id);
  assert.strictEqual(app.state.tabs.length, 3, 'duplicateCanvasTab should create a third tab');
  assert.strictEqual(app.state.activeTabId, forkedTab.id, 'Forked tab should become active');
  assert.strictEqual(app.state.elements.length, 1, 'Forked tab should have cloned element');
  assert.notStrictEqual(app.state.elements[0].id, secondTab.elements[0].id, 'Forked tab elements must have distinct IDs');

  // Mutate forked tab and verify Tab 2 and Tab 1 are untouched
  app.quickAddShape('rectangle');
  assert.strictEqual(app.state.elements.length, 2, 'Forked tab now has 2 elements');

  // Switch back to Tab 1 via Alt+1 shortcut
  app.handleKeyDown({ key: '1', altKey: true });
  assert.strictEqual(app.state.activeTabId, firstTabId, 'Alt+1 should switch back to Tab 1');
  assert.strictEqual(app.state.elements.length, firstTabElemCount, 'Tab 1 should retain its original elements');

  // Switch to Tab 2 and verify it still has 1 element and dark background
  app.switchCanvasTab(secondTab.id);
  assert.strictEqual(app.state.elements.length, 1, 'Tab 2 must remain isolated from Tab 3 edits');
  assert.strictEqual(app.state.canvasBg, '#000000', 'Tab 2 should restore its dark canvas background');

  // Step forward and backward between canvases via stepCanvasTab / Alt+] / Alt+[
  app.handleKeyDown({ key: ']', altKey: true });
  assert.strictEqual(app.state.activeTabId, forkedTab.id, 'Alt+] should step forward to Tab 3');
  app.handleKeyDown({ key: '[', altKey: true });
  assert.strictEqual(app.state.activeTabId, secondTab.id, 'Alt+[ should step back to Tab 2');

  // Verify localStorage persistence & reload
  app.saveWorkspaceToStorage();
  const savedRaw = sandbox.window.localStorage.getItem(app.WORKSPACE_STORAGE_KEY);
  assert(savedRaw && savedRaw.includes('Worker Subflow'), 'localStorage should persist multi-tab workspace JSON');

  // Close Tab 3 and then restore from savedRaw via importExcalidrawJson
  app.closeCanvasTab(forkedTab.id);
  assert.strictEqual(app.state.tabs.length, 2, 'closeCanvasTab should remove Tab 3');
  const restoredOk = app.importExcalidrawJson(savedRaw);
  assert.strictEqual(restoredOk, true, 'importExcalidrawJson should restore multi-tab workspace JSON');
  assert.strictEqual(app.state.tabs.length, 3, 'Restoring workspace JSON should bring back all 3 tabs');
  console.log('[PASS] 8. Multi-canvas tabs (create, switch, fork/duplicate, rename, close, Alt+1..9, localStorage & multi-tab JSON) verified');

  console.log('\nALL EXCALIFLOW VERIFICATION CHECKS PASSED SUCCESSFULLY!');
})().catch(err => {
  console.error(err);
  process.exit(1);
});
