// Deterministic stream boundaries, cleanup and recovery; no network or devices.
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const source = fs.readFileSync(require('node:path').join(__dirname, '../live_demo/avatar.js'), 'utf8');
function env(supported = true) {
  const elements = new Map(), sources = [], revoked = [];
  class Events {
    constructor() { this.events = {}; }
    addEventListener(name, fn) { (this.events[name] ||= []).push(fn); }
    emit(name) { for (const fn of this.events[name] || []) fn(); }
  }
  class Buffer extends Events {
    constructor() { super(); this.updating = false; this.appended = []; this.buffered = {length: 0}; }
    appendBuffer(data) { this.appended.push([...data]); this.updating = true; }
    finish() { this.updating = false; this.emit('updateend'); }
  }
  class Media extends Events {
    static isTypeSupported() { return supported; }
    constructor() { super(); sources.push(this); this.readyState = 'closed'; }
    addSourceBuffer() { return this.buffer = new Buffer(); }
    open() { this.readyState = 'open'; this.emit('sourceopen'); }
  }
  function element() { const el = new Events(); return Object.assign(el, {hidden:false, dataset:{}, currentTime:0, readyState:0, paused:true, pause(){this.paused=true;}, play(){this.paused=false;return Promise.resolve();}, load(){}, removeAttribute(){this.src='';}}); }
  const context = vm.createContext({window:{MediaSource:Media}, document:{querySelector(id){if(!elements.has(id))elements.set(id,element());return elements.get(id);}}, URL:{createObjectURL:()=>`blob:${sources.length}`,revokeObjectURL:url=>revoked.push(url)}, atob:s=>global.Buffer.from(s,'base64').toString('binary'), console});
  vm.runInContext(source, context);
  const player = context.window.claimAvatar;
  player.configure({enabled:true,name:'Kira'});
  return {player,elements,sources,revoked};
}
function box(type, payload = []) { const b = global.Buffer.alloc(8 + payload.length); b.writeUInt32BE(b.length); b.write(type,4); global.Buffer.from(payload).copy(b,8); return b; }
const init = global.Buffer.concat([box('ftyp'),box('moov',[0,0,0,12,97,118,99,67,1,66,192,32])]);
const frame = global.Buffer.concat([box('moof'),box('mdat',[1,2,3,4])]);
function send(e, bytes) { e.player.append(bytes.toString('base64')); }
function drain(s) { for(let i=0;i<20 && s.buffer.updating;i++)s.buffer.finish(); }
const tests = [];
function test(name,fn) { tests.push([name,fn]); }
test('arbitrarily split MP4 boxes are reassembled in order', () => {
  const e=env(), bytes=global.Buffer.concat([init,frame]);
  for(let i=0;i<bytes.length;i+=3)send(e,bytes.subarray(i,i+3));
  assert.equal(e.sources.length,1);e.sources[0].open();drain(e.sources[0]);
  assert.equal(e.sources[0].buffer.appended.length,3);
  assert.deepEqual(e.sources[0].buffer.appended[2],[...frame]);
});
test('second turn reuses initialization and the same media clock', () => {
  const e=env();send(e,global.Buffer.concat([init,frame]));e.sources[0].open();drain(e.sources[0]);
  e.player.finishTurn();send(e,frame);drain(e.sources[0]);
  assert.equal(e.sources.length,1);assert.equal(e.sources[0].buffer.appended.length,4);
});
test('interruption discards queued speech and reuses initialization for new timestamps', () => {
  const e=env();send(e,global.Buffer.concat([init,frame]));e.sources[0].open();
  e.player.interrupt();assert.equal(e.elements.get('#avatarVideo').paused,true);assert.equal(e.revoked.length,1);
  send(e,frame);e.sources[1].open();drain(e.sources[1]);
  e.sources[0].buffer.finish(); // a stale decoder callback must do nothing
  assert.equal(e.sources[1].buffer.appended.length,3);
  assert.deepEqual(e.sources[1].buffer.appended[2],[...frame]);
});
test('reset forgets previous initialization and releases its object URL', () => {
  const e=env();send(e,global.Buffer.concat([init,frame]));e.player.reset();
  assert.equal(e.revoked.length,1);assert.equal(e.elements.get('#avatarVideo').hidden,true);
  send(e,frame);assert.equal(e.sources.length,1);assert.equal(e.elements.get('#resumeAvatar').textContent,'Continue with voice');
});
test('oversized or malformed media offers voice recovery', () => {
  const e=env();send(e,global.Buffer.from([255,255,255,255,109,100,97,116]));
  let fallback=false;e.player.onFallback=()=>fallback=true;
  e.elements.get('#resumeAvatar').emit('click');
  assert(fallback);assert.equal(e.player.supported,false);
});
test('unsupported browsers select voice mode without a decoder', () => {
  const e=env(false);send(e,global.Buffer.concat([init,frame]));
  assert.equal(e.player.supported,false);assert.equal(e.sources.length,0);
  assert.equal(e.elements.get('#avatarStage').hidden,true);
});
test('voice-only configuration hides the unused avatar frame', () => {
  const e=env();
  assert.equal(e.elements.get('#avatarStage').hidden,false);
  e.player.configure({enabled:false,name:''});
  assert.equal(e.elements.get('#avatarStage').hidden,true);
});
for(const [name,fn]of tests){fn();console.log('PASS '+name);}
console.log(`${tests.length} avatar player tests passed`);
