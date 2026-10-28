/* NOVA — Sci-Fi AI Digital Companion — Frontend controller */
(() => {
  "use strict";

  // ── DOM ────────────────────────────────────────────────
  const $ = (id) => document.getElementById(id);
  const leftEye = $("leftEye"), rightEye = $("rightEye");
  const leftPupil = $("leftPupil"), rightPupil = $("rightPupil");
  const eyesContainer = $("eyesContainer");
  const charScreen = $("characterScreen");
  const mirrorScreen = $("mirrorScreen");
  const videoFeed = $("videoFeed");
  const tlEmotion = $("tlEmotion");
  const tlConf = $("tlConf");
  const tlConfBar = $("tlConfBar");
  const tlGesture = $("tlGesture");
  const tlFps = $("tlFps");
  const statusLine = $("statusLine");
  const audioBtn = $("audioBtn");
  const modeToggleBtn = $("modeToggleBtn");
  const fullscreenBtn = $("fullscreenBtn");

  // ── State ──────────────────────────────────────────────
  const state = {
    mode: "character",
    anim: "neutral",
    audio: true,
    hand: { x: 0.5, y: 0.5, active: false },
    target: { x: 0, y: 0 },
    current: { x: 0, y: 0 },
    lastEmotion: "neutral",
    lastTs: 0,
    frameCounter: { t: performance.now(), n: 0 },
    idleUntil: 0,
    connected: true,
  };

  videoFeed.src = "/video_feed";

  // ── Audio engine ───────────────────────────────────────
  let audioCtx = null;
  const ensureCtx = () => {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === "suspended") audioCtx.resume();
  };

  const playSound = (type) => {
    if (!state.audio) return;
    try { ensureCtx(); } catch { return; }
    const t = audioCtx.currentTime;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain); gain.connect(audioCtx.destination);

    const presets = {
      beep:     { type: "sine",     from: 800,  to: 1200, dur: 0.08, peak: 0.14 },
      chirp:    { type: "sine",     from: 1200, to: 400,  dur: 0.12, peak: 0.10 },
      giggle:   { type: "triangle", from: 600,  to: 1100, dur: 0.20, peak: 0.18 },
      shocked:  { type: "sawtooth", from: 350,  to: 120,  dur: 0.25, peak: 0.22 },
      boot:     { type: "sine",     from: 220,  to: 880,  dur: 0.35, peak: 0.12 },
      error:    { type: "square",   from: 200,  to: 90,   dur: 0.30, peak: 0.18 },
    };
    const p = presets[type] || presets.beep;
    osc.type = p.type;
    osc.frequency.setValueAtTime(p.from, t);
    osc.frequency.exponentialRampToValueAtTime(Math.max(p.to, 20), t + p.dur);
    gain.gain.setValueAtTime(p.peak, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + p.dur);
    osc.start(t); osc.stop(t + p.dur + 0.01);
  };

  // ── Particles ──────────────────────────────────────────
  const canvas = $("particles");
  const ctx = canvas.getContext("2d");
  let particles = [];
  const resize = () => {
    canvas.width = innerWidth; canvas.height = innerHeight;
    const count = Math.min(120, Math.floor((innerWidth * innerHeight) / 22000));
    particles = Array.from({ length: count }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      r: Math.random() * 1.4 + 0.4,
      a: Math.random() * 0.5 + 0.15,
    }));
  };
  addEventListener("resize", resize);
  resize();

  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const drawParticles = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!reducedMotion) {
      for (const p of particles) {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(102,252,241,${p.a})`;
        ctx.fill();
      }
    }
    requestAnimationFrame(drawParticles);
  };
  drawParticles();

  // ── Expression engine ─────────────────────────────────
  const EXPRESSIONS = ["happy", "sad", "angry", "surprised", "curious",
                       "shocked", "sleepy", "love", "wink", "laughing",
                       "disgust", "thinking"];

  const setExpression = (name) => {
    if (state.anim === name) return;
    state.anim = name;

    // Reset both eyes
    leftEye.className = "eye";
    rightEye.className = "eye";
    eyesContainer.classList.remove("giggle");

    switch (name) {
      case "happy":     leftEye.classList.add("happy");     rightEye.classList.add("happy");     playSound("chirp"); break;
      case "sad":       leftEye.classList.add("sad");       rightEye.classList.add("sad");       playSound("chirp"); break;
      case "angry":     leftEye.classList.add("angry");     rightEye.classList.add("angry");     playSound("shocked"); break;
      case "surprised": leftEye.classList.add("surprised"); rightEye.classList.add("surprised"); playSound("chirp"); break;
      case "curious":   leftEye.classList.add("curious");   rightEye.classList.add("curious");   playSound("beep"); break;
      case "shocked":   leftEye.classList.add("shocked");   rightEye.classList.add("shocked");   playSound("shocked"); break;
      case "sleepy":    leftEye.classList.add("sleepy");    rightEye.classList.add("sleepy");    break;
      case "love":      leftEye.classList.add("love");      rightEye.classList.add("love");      playSound("chirp"); break;
      case "laughing":  leftEye.classList.add("laughing");  rightEye.classList.add("laughing");  playSound("giggle"); break;
      case "disgust":   leftEye.classList.add("disgust");   rightEye.classList.add("disgust");   playSound("error"); break;
      case "thinking":  leftEye.classList.add("thinking");  rightEye.classList.add("thinking");  playSound("beep"); break;
      case "wink":      leftEye.classList.add("wink-left"); rightEye.classList.add("happy");     playSound("beep"); break;
      case "giggle":    eyesContainer.classList.add("giggle");
                        leftEye.classList.add("happy");     rightEye.classList.add("happy");
                        playSound("giggle"); break;
      default: break; // neutral
    }

    const labels = {
      happy: "◉ JOY DETECTED", sad: "◉ MELANCHOLY", angry: "◉ HOSTILITY",
      surprised: "◉ SURPRISE", curious: "◉ INTRIGUED", shocked: "◉ ALARM",
      sleepy: "◉ DORMANT", love: "◉ AFFECTION", laughing: "◉ AMUSEMENT",
      disgust: "◉ AVERSION", thinking: "◉ PROCESSING", wink: "◉ SIGNAL",
      giggle: "◉ LEVITY", neutral: "◉ SYSTEM NOMINAL",
    };
    statusLine.textContent = labels[name] || "◉ SYSTEM NOMINAL";
  };

  // ── Blink loop ────────────────────────────────────────
  let blinkTimer = null;
  const scheduleBlink = () => {
    blinkTimer = setTimeout(() => {
      if (state.anim !== "sleepy") {
        leftEye.classList.add("blink");
        rightEye.classList.add("blink");
        setTimeout(() => {
          leftEye.classList.remove("blink");
          rightEye.classList.remove("blink");
        }, 140);
      }
      scheduleBlink();
    }, Math.random() * 2200 + 1400);
  };
  scheduleBlink();

  const forceBlink = () => {
    leftEye.classList.add("blink");
    rightEye.classList.add("blink");
    setTimeout(() => {
      leftEye.classList.remove("blink");
      rightEye.classList.remove("blink");
    }, 140);
  };

  // ── Pupil tracking (lerp) ─────────────────────────────
  const PUPIL_MAX = 55; // px in CSS pixels, bounded by eye size
  const IDLE_SACCADE = () => {
    // random small drift when no hand detected
    state.target.x = (Math.random() - 0.5) * 20;
    state.target.y = (Math.random() - 0.5) * 14;
    state.idleUntil = performance.now() + 900 + Math.random() * 1600;
  };
  IDLE_SACCADE();

  const updatePupils = () => {
    if (state.hand.active) {
      const moveX = (state.hand.x - 0.5) * 85;
      const moveY = (state.hand.y - 0.5) * 85;
      state.target.x = moveX;
      state.target.y = moveY;
    } else if (performance.now() > state.idleUntil) {
      IDLE_SACCADE();
    }

    // lerp
    const k = 0.18;
    state.current.x += (state.target.x - state.current.x) * k;
    state.current.y += (state.target.y - state.current.y) * k;

    const cx = clamp(state.current.x, -PUPIL_MAX, PUPIL_MAX);
    const cy = clamp(state.current.y, -PUPIL_MAX, PUPIL_MAX);
    const t = `translate(${cx}px, ${cy}px)`;
    leftPupil.style.transform = t;
    rightPupil.style.transform = t;

    requestAnimationFrame(updatePupils);
  };
  updatePupils();

  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

  // ── Status polling ────────────────────────────────────
  let pollTimer = null;
  const pollStatus = async () => {
    try {
      const res = await fetch("/get_status", { cache: "no-store" });
      if (!res.ok) throw new Error("bad status");
      const data = await res.json();

      // FPS
      const now = performance.now();
      state.frameCounter.n++;
      if (now - state.frameCounter.t >= 1000) {
        const fps = (state.frameCounter.n * 1000) / (now - state.frameCounter.t);
        tlFps.textContent = fps.toFixed(0);
        state.frameCounter = { t: now, n: 0 };
      }

      // Hand
      const h = data.hand;
      if (h.detected) {
        state.hand = { x: h.norm_x, y: h.norm_y, active: true };
        tlGesture.textContent = h.gesture || "—";
      } else {
        state.hand.active = false;
        tlGesture.textContent = "—";
      }

      // Emotion
      const e = data.emotion;
      tlEmotion.textContent = e.label;
      const confPct = Math.round((e.confidence || 0) * 100);
      tlConf.textContent = confPct + "%";
      tlConfBar.style.width = confPct + "%";

      if (state.mode === "character") {
        if (h.detected) {
          // Hand has priority — but visual expression follows emotion
          applyEmotion(e.label);
        } else {
          applyEmotion(e.label);
          if (e.label === "neutral" && Math.random() < 0.08) {
            setExpression(EXPRESSIONS[Math.floor(Math.random() * EXPRESSIONS.length)]);
            setTimeout(() => setExpression("neutral"), 2400);
          }
        }
      }

      state.connected = true;
    } catch {
      state.connected = false;
      statusLine.textContent = "⚠ LINK LOST · RETRYING";
    }
    pollTimer = setTimeout(pollStatus, 220);
  };

  const applyEmotion = (label) => {
    if (label === state.lastEmotion) return;
    state.lastEmotion = label;
    setExpression(label);
    if (label !== "neutral") {
      setTimeout(() => {
        if (state.lastEmotion === label) {
          state.lastEmotion = "neutral";
          setExpression("neutral");
        }
      }, 2600);
    }
  };

  pollStatus();

  // ── Controls ──────────────────────────────────────────
  audioBtn.addEventListener("click", () => {
    state.audio = !state.audio;
    audioBtn.textContent = state.audio ? "🔊" : "🔇";
    playSound("beep");
  });

  const toggleMode = () => {
    playSound("chirp");
    if (state.mode === "character") {
      state.mode = "mirror";
      charScreen.classList.add("hidden");
      mirrorScreen.classList.add("active");
      modeToggleBtn.textContent = "🤖";
    } else {
      state.mode = "character";
      mirrorScreen.classList.remove("active");
      charScreen.classList.remove("hidden");
      modeToggleBtn.textContent = "🪞";
    }
  };
  modeToggleBtn.addEventListener("click", toggleMode);

  const toggleFullscreen = () => {
    playSound("beep");
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen?.();
    }
  };
  fullscreenBtn.addEventListener("click", toggleFullscreen);

  // ── Keyboard shortcuts ────────────────────────────────
  addEventListener("keydown", (ev) => {
    if (ev.repeat) return;
    const k = ev.key.toLowerCase();
    if (k === "m") toggleMode();
    else if (k === "a") audioBtn.click();
    else if (k === "f") toggleFullscreen();
    else if (k === " ") { ev.preventDefault(); forceBlink(); }
  });

  // ── Boot sequence ─────────────────────────────────────
  statusLine.textContent = "◉ BOOTING NEURAL CORE…";
  playSound("boot");
  setTimeout(() => setExpression("happy"), 400);
  setTimeout(() => setExpression("neutral"), 1600);

  // ── Cleanup ───────────────────────────────────────────
  addEventListener("beforeunload", () => {
    clearTimeout(blinkTimer);
    clearTimeout(pollTimer);
  });
})();