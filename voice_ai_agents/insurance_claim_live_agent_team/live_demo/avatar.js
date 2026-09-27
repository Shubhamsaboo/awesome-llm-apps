/* Gemini's MP4 contains both the avatar and its voice. Keep them on one clock. */
(() => {
  const video = document.querySelector('#avatarVideo');
  const stage = document.querySelector('#avatarStage');
  const status = document.querySelector('#avatarStatus');
  const resume = document.querySelector('#resumeAvatar');
  const name = document.querySelector('#avatarName');
  const MediaSourceClass = window.MediaSource || window.ManagedMediaSource;
  const defaultCodec = 'video/mp4; codecs="avc1.42c020, mp4a.40.2"';
  const MAX_BYTES = 16 * 1024 * 1024;
  let supported = Boolean(MediaSourceClass?.isTypeSupported(defaultCodec));
  let enabled = false, failed = false, source, buffer, objectUrl;
  let pending = new Uint8Array(), init = [], fragment = null, queue = [];
  let queuedBytes = 0, codec = defaultCodec, epoch = 0, seekToStart = true, turnFinished = false;

  function label(text, state = 'idle') {
    status.textContent = text;
    stage.dataset.state = state;
  }
  function join(a, b) {
    const result = new Uint8Array(a.length + b.length);
    result.set(a); result.set(b, a.length); return result;
  }
  function dispose() {
    epoch++;
    video.pause();
    video.hidden = true;
    video.removeAttribute('src');
    video.load();
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = null; source = null; buffer = null;
    queue = []; queuedBytes = 0; seekToStart = true;
    resume.hidden = true;
  }
  function fail() {
    dispose(); failed = true;
    label('Video couldn’t play. You can continue with voice.', 'error');
    resume.textContent = 'Continue with voice'; resume.hidden = false;
  }
  function play() {
    const current = epoch;
    video.play().then(() => {
      if (current === epoch) resume.hidden = true;
    }).catch(error => {
      if (current !== epoch || error.name === 'AbortError') return;
      label('Tap to hear and see your assistant', 'paused');
      resume.textContent = 'Play voice and video'; resume.hidden = false;
    });
  }
  function flush() {
    if (!buffer || buffer.updating || source.readyState !== 'open') return;
    try {
      // Retain a short playback window during long conversations.
      if (buffer.buffered.length && video.currentTime - buffer.buffered.start(0) > 30) {
        buffer.remove(0, video.currentTime - 10); return;
      }
      if (queue.length) {
        const data = queue.shift(); queuedBytes -= data.length;
        buffer.appendBuffer(data);
      }
    } catch (_) { fail(); }
  }
  function enqueue(data) {
    queuedBytes += data.length;
    if (queuedBytes > MAX_BYTES) { fail(); return; }
    queue.push(data); flush();
  }
  function open() {
    source = new MediaSourceClass();
    const current = epoch, currentSource = source;
    video.disableRemotePlayback = true;
    objectUrl = URL.createObjectURL(source); video.src = objectUrl;
    source.addEventListener('sourceopen', () => {
      if (current !== epoch) return;
      try {
        buffer = currentSource.addSourceBuffer(codec);
        buffer.addEventListener('error', () => { if (current === epoch) fail(); });
        buffer.addEventListener('updateend', () => {
          if (current !== epoch) return;
          if (seekToStart && buffer.buffered.length) {
            // After barge-in, new fragments retain the session's original timestamps.
            video.currentTime = buffer.buffered.start(0); seekToStart = false;
            play();
          }
          flush();
        });
        flush();
      } catch (_) { fail(); }
    }, { once: true });
    for (const data of init) enqueue(data);
  }
  function consume(box, type) {
    if (type === 'ftyp') {
      dispose(); init = [box]; fragment = null; failed = false;
    } else if (type === 'moov') {
      init.push(box);
      // Read the H.264 profile from the initialization segment, not an assumed model version.
      for (let i = 4; i + 8 < box.length; i++) {
        if (String.fromCharCode(...box.subarray(i, i + 4)) === 'avcC') {
          const profile = [...box.subarray(i + 5, i + 8)].map(n => n.toString(16).padStart(2, '0')).join('');
          codec = `video/mp4; codecs="avc1.${profile}, mp4a.40.2"`; break;
        }
      }
      if (!MediaSourceClass.isTypeSupported(codec)) { fail(); return; }
    } else if (type === 'moof') {
      fragment = box;
    } else if (type === 'mdat' && fragment) {
      const data = join(fragment, box); fragment = null;
      if (!source) {
        if (init.length < 2) { fail(); return; }
        open();
      }
      enqueue(data);
    }
  }
  function append(base64) {
    if (!supported || !enabled || failed) return;
    try {
      turnFinished = false;
      const bytes = Uint8Array.from(atob(base64), c => c.charCodeAt(0));
      pending = join(pending, bytes);
      if (pending.length > MAX_BYTES) { fail(); return; }
      // Transport chunks can split any MP4 box. Never feed half a discarded
      // fragment back into the decoder after an interruption.
      while (pending.length >= 8 && !failed) {
        const size = new DataView(pending.buffer, pending.byteOffset).getUint32(0);
        if (size < 8 || size > MAX_BYTES) { fail(); return; }
        if (pending.length < size) break;
        const box = pending.slice(0, size); pending = pending.slice(size);
        consume(box, String.fromCharCode(...box.subarray(4, 8)));
      }
    } catch (_) { fail(); }
  }
  function reset() {
    dispose(); pending = new Uint8Array(); init = []; fragment = null; failed = false;
    label(enabled ? 'Start a conversation when you’re ready' : 'Voice assistant · ready when you are');
  }
  video.addEventListener('loadeddata', () => { if (source) video.hidden = false; });
  video.addEventListener('playing', () => label('Live avatar · voice and video', 'speaking'));
  video.addEventListener('waiting', () => {
    if (source && turnFinished) label('Ready for your next message', 'listening');
  });
  video.addEventListener('error', () => { if (source) fail(); });
  resume.addEventListener('click', () => {
    if (failed) {
      supported = false; enabled = false; stage.hidden = true; reset();
      window.claimAvatar.onFallback?.();
    } else play();
  });
  window.claimAvatar = {
    get supported() { return supported; },
    append, reset,
    configure(settings) {
      enabled = Boolean(settings?.enabled && supported);
      stage.hidden = !enabled;
      name.textContent = enabled ? `${settings.name} · Claim assistant` : 'Claim assistant';
      label(enabled ? 'Start a conversation when you’re ready' : 'Voice assistant · ready when you are');
    },
    connecting() { label(enabled ? 'Connecting your avatar…' : 'Connecting…', 'connecting'); },
    interrupt() {
      dispose(); pending = new Uint8Array(); fragment = null;
      label('Ready for your next message', 'listening');
    },
    finishTurn() {
      turnFinished = true;
      if (video.readyState < 3) label('Ready for your next message', 'listening');
    },
  };
})();
