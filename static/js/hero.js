/* MODULE 1 — Cinematic hero.
   A WebGL fragment shader crossfades the four scenes with a liquid,
   noise-driven displacement wipe, slow Ken Burns zoom, water shimmer and
   pointer parallax. If WebGL, the images or motion are unavailable, the CSS
   background layers underneath crossfade instead (same timing, same controls). */
(() => {
  const hero = document.getElementById("hero");
  if (!hero) return;

  const dashes = Array.from(document.querySelectorAll("#hero-dashes .hero__dash"));
  const layers = Array.from(hero.querySelectorAll(".hero__scene-layer"));
  const caption = document.getElementById("hero-scene-caption");
  const countEl = document.getElementById("hero-count");
  const canvas = document.getElementById("hero-canvas");
  if (!dashes.length || !caption) return;

  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const INTERVAL = 6000;
  const TRANSITION = 1700;
  hero.style.setProperty("--hero-interval", `${INTERVAL}ms`);

  const sceneCount = layers.length || dashes.length || 1;
  let active = 0;
  let renderer = null;

  /* ------------------------------------------------------------ scene state */
  const setActive = (i) => {
    if (i === active) return;
    const prev = active;
    active = i;
    dashes.forEach((d, k) => {
      d.classList.toggle("is-active", k === i);
      d.classList.toggle("is-done", k < i);
    });
    layers.forEach((l, k) => l.classList.toggle("is-active", k === i));
    if (caption && dashes[i]) {
      caption.classList.add("is-swapping");
      window.setTimeout(() => {
        caption.textContent = dashes[i].dataset.caption;
        caption.classList.remove("is-swapping");
      }, 350);
    }
    if (countEl) countEl.textContent = String(i + 1).padStart(2, "0");
    if (renderer) renderer.go(prev, i);
  };

  /* ------------------------------------------ timer that can pause & resume */
  let timer = null;
  let startedAt = 0;
  let remaining = INTERVAL;
  let paused = false;
  const schedule = (ms) => {
    window.clearTimeout(timer);
    startedAt = performance.now();
    remaining = ms;
    timer = window.setTimeout(() => {
      setActive((active + 1) % sceneCount);
      schedule(INTERVAL);
    }, ms);
  };
  const pause = () => {
    if (paused || reduce) return;
    paused = true;
    window.clearTimeout(timer);
    remaining = Math.max(0, remaining - (performance.now() - startedAt));
    hero.classList.add("is-paused");
  };
  const resume = () => {
    if (!paused || reduce) return;
    paused = false;
    hero.classList.remove("is-paused");
    schedule(remaining);
  };

  dashes.forEach((dash, i) => {
    dash.addEventListener("click", () => {
      setActive(i);
      paused = false;
      hero.classList.remove("is-paused");
      if (!reduce) schedule(INTERVAL);
    });
  });

  const foot = hero.querySelector(".hero__foot");
  if (foot) {
    foot.addEventListener("pointerenter", pause);
    foot.addEventListener("pointerleave", resume);
  }
  document.addEventListener("visibilitychange", () => (document.hidden ? pause() : resume()));

  if (reduce) {
    hero.classList.add("is-paused");
  } else {
    schedule(INTERVAL);
  }

  const scrollCue = document.getElementById("hero-scroll-cue");
  if (scrollCue) {
    scrollCue.addEventListener("click", () => {
      const next = hero.nextElementSibling;
      if (!next) return;
      if (window.CI && window.CI.scrollTo) window.CI.scrollTo(next);
      else next.scrollIntoView({ behavior: "smooth" });
    });
  }

  /* ---------------------------------------------------------------- WebGL */
  // Video scenes render themselves — the shader crossfade is for photo layers only.
  if (reduce || !canvas || hero.querySelector(".hero__video")) return;

  const VERT = `
    attribute vec2 aPos;
    varying vec2 vUv;
    void main() { vUv = aPos * 0.5 + 0.5; gl_Position = vec4(aPos, 0.0, 1.0); }
  `;

  const FRAG = `
    precision highp float;
    varying vec2 vUv;
    uniform sampler2D uTex0;
    uniform sampler2D uTex1;
    uniform vec2 uSize0;
    uniform vec2 uSize1;
    uniform vec2 uRes;
    uniform vec2 uMouse;
    uniform float uProgress;
    uniform float uTime;
    uniform float uZoom0;
    uniform float uZoom1;

    vec3 permute(vec3 x) { return mod(((x * 34.0) + 1.0) * x, 289.0); }
    float snoise(vec2 v) {
      const vec4 C = vec4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
      vec2 i = floor(v + dot(v, C.yy));
      vec2 x0 = v - i + dot(i, C.xx);
      vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
      vec4 x12 = x0.xyxy + C.xxzz;
      x12.xy -= i1;
      i = mod(i, 289.0);
      vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0)) + i.x + vec3(0.0, i1.x, 1.0));
      vec3 m = max(0.5 - vec3(dot(x0, x0), dot(x12.xy, x12.xy), dot(x12.zw, x12.zw)), 0.0);
      m = m * m; m = m * m;
      vec3 x = 2.0 * fract(p * C.www) - 1.0;
      vec3 h = abs(x) - 0.5;
      vec3 ox = floor(x + 0.5);
      vec3 a0 = x - ox;
      m *= 1.79284291400159 - 0.85373472095314 * (a0 * a0 + h * h);
      vec3 g;
      g.x = a0.x * x0.x + h.x * x0.y;
      g.yz = a0.yz * x12.xz + h.yz * x12.yw;
      return 130.0 * dot(m, g);
    }

    vec2 cover(vec2 uv, vec2 img, float zoom) {
      float sr = uRes.x / uRes.y;
      float ir = img.x / img.y;
      vec2 s = sr > ir ? vec2(1.0, ir / sr) : vec2(sr / ir, 1.0);
      return (uv - 0.5) * s / (1.0 + zoom) + 0.5;
    }

    void main() {
      vec2 uv = vUv;
      float t = uTime;

      // Water shimmer + pointer parallax, applied to both scenes.
      float shimmer = snoise(vec2(uv.x * 4.0, uv.y * 7.0 - t * 0.12));
      vec2 drift = vec2(shimmer * 0.0022, shimmer * 0.0016) + uMouse * vec2(-0.012, 0.008);

      // Transition mask: an organic noise front sweeping bottom-to-top.
      float wave = snoise(uv * vec2(1.8, 2.6) + vec2(t * 0.08, 0.0)) * 0.5 + 0.5;
      float front = wave * 0.55 + (1.0 - uv.y) * 0.45;
      float p = uProgress * 1.5 - 0.25;
      float mask = smoothstep(front - 0.25, front + 0.02, p);

      float swirl = snoise(uv * 3.0 + t * 0.2);
      vec2 push = vec2(swirl * 0.06, 0.14);
      float bell = sin(uProgress * 3.14159265);

      vec2 uv0 = cover(uv + drift + push * mask, uSize0, uZoom0);
      vec2 uv1 = cover(uv + drift - push * (1.0 - mask), uSize1, uZoom1);

      float ca = 0.004 * bell;
      vec3 c0 = vec3(texture2D(uTex0, uv0 + vec2(ca, 0.0)).r, texture2D(uTex0, uv0).g, texture2D(uTex0, uv0 - vec2(ca, 0.0)).b);
      vec3 c1 = vec3(texture2D(uTex1, uv1 - vec2(ca, 0.0)).r, texture2D(uTex1, uv1).g, texture2D(uTex1, uv1 + vec2(ca, 0.0)).b);

      vec3 col = mix(c0, c1, mask);

      // Warm light bloom on the moving front.
      float edge = smoothstep(0.0, 0.5, mask) * (1.0 - smoothstep(0.5, 1.0, mask));
      col += vec3(0.85, 0.66, 0.38) * edge * 0.22 * bell;

      // Subtle filmic grade.
      col = pow(col, vec3(0.96));
      col *= 1.0 - 0.18 * length(uv - 0.5);

      gl_FragColor = vec4(col, 1.0);
    }
  `;

  const createRenderer = (images) => {
    const gl = canvas.getContext("webgl", { antialias: false, alpha: false, premultipliedAlpha: false, powerPreference: "high-performance" });
    if (!gl) return null;

    const compile = (type, src) => {
      const s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
        console.warn("[hero] shader:", gl.getShaderInfoLog(s));
        return null;
      }
      return s;
    };
    const vs = compile(gl.VERTEX_SHADER, VERT);
    const fs = compile(gl.FRAGMENT_SHADER, FRAG);
    if (!vs || !fs) return null;
    const prog = gl.createProgram();
    gl.attachShader(prog, vs);
    gl.attachShader(prog, fs);
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return null;
    gl.useProgram(prog);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    const aPos = gl.getAttribLocation(prog, "aPos");
    gl.enableVertexAttribArray(aPos);
    gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

    const u = {};
    ["uTex0", "uTex1", "uSize0", "uSize1", "uRes", "uMouse", "uProgress", "uTime", "uZoom0", "uZoom1"].forEach((n) => (u[n] = gl.getUniformLocation(prog, n)));

    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
    const textures = images.map((img) => {
      const tex = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, img);
      return { tex, w: img.naturalWidth, h: img.naturalHeight };
    });
    gl.uniform1i(u.uTex0, 0);
    gl.uniform1i(u.uTex1, 1);

    const shownAt = textures.map(() => performance.now());
    let from = active;
    let to = active;
    let progress = 0;
    let transStart = 0;
    let transitioning = false;
    let mouse = { x: 0, y: 0, tx: 0, ty: 0 };
    let running = false;
    let visible = true;
    const t0 = performance.now();

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      const w = Math.round(canvas.clientWidth * dpr);
      const h = Math.round(canvas.clientHeight * dpr);
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
        gl.viewport(0, 0, w, h);
      }
    };

    const zoomFor = (i, now) => Math.min((now - shownAt[i]) / (INTERVAL + TRANSITION * 2), 1) * 0.085;
    const ease = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);

    const frame = (now) => {
      if (!running) return;
      resize();
      if (transitioning) {
        const raw = Math.min((now - transStart) / TRANSITION, 1);
        progress = ease(raw);
        if (raw >= 1) {
          transitioning = false;
          from = to;
          progress = 0;
        }
      }
      mouse.x += (mouse.tx - mouse.x) * 0.05;
      mouse.y += (mouse.ty - mouse.y) * 0.05;

      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, textures[from].tex);
      gl.activeTexture(gl.TEXTURE1);
      gl.bindTexture(gl.TEXTURE_2D, textures[to].tex);
      gl.uniform2f(u.uSize0, textures[from].w, textures[from].h);
      gl.uniform2f(u.uSize1, textures[to].w, textures[to].h);
      gl.uniform2f(u.uRes, canvas.width, canvas.height);
      gl.uniform2f(u.uMouse, mouse.x, mouse.y);
      gl.uniform1f(u.uProgress, progress);
      gl.uniform1f(u.uTime, (now - t0) / 1000);
      gl.uniform1f(u.uZoom0, zoomFor(from, now));
      gl.uniform1f(u.uZoom1, zoomFor(to, now));
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      requestAnimationFrame(frame);
    };

    const start = () => {
      if (running || !visible || document.hidden) return;
      running = true;
      requestAnimationFrame(frame);
    };
    const stop = () => (running = false);

    if ("IntersectionObserver" in window) {
      new IntersectionObserver(([entry]) => {
        visible = entry.isIntersecting;
        visible ? start() : stop();
      }).observe(hero);
    }
    document.addEventListener("visibilitychange", () => (document.hidden ? stop() : start()));
    hero.addEventListener("pointermove", (e) => {
      const r = hero.getBoundingClientRect();
      mouse.tx = ((e.clientX - r.left) / r.width) * 2 - 1;
      mouse.ty = ((e.clientY - r.top) / r.height) * 2 - 1;
    });
    hero.addEventListener("pointerleave", () => (mouse.tx = mouse.ty = 0));
    canvas.addEventListener("webglcontextlost", (e) => {
      e.preventDefault();
      stop();
      hero.classList.remove("is-webgl");
    });

    start();

    return {
      go(prev, next) {
        // If a transition is mid-flight, snap it to its target first.
        from = transitioning ? to : prev;
        to = next;
        shownAt[next] = performance.now();
        transStart = performance.now();
        transitioning = true;
        progress = 0;
      },
    };
  };

  const load = (src) =>
    new Promise((resolve, reject) => {
      const img = new Image();
      img.decoding = "async";
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.src = src;
    });

  Promise.all(layers.map((l) => load(l.dataset.src)))
    .then((images) => {
      renderer = createRenderer(images);
      if (renderer) {
        requestAnimationFrame(() => hero.classList.add("is-webgl"));
      }
    })
    .catch(() => {
      /* keep CSS fallback */
    });
})();
