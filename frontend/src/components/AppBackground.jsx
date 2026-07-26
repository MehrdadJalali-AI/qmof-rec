import { useEffect, useRef } from "react";

const NODE_COUNT_DESKTOP = 130;
const NODE_COUNT_MOBILE = 55;
const LINK_DISTANCE = 190;
const SPEED = 0.3;

function readCssVar(name, fallback) {
  if (typeof window === "undefined") return fallback;
  const value = getComputedStyle(document.documentElement).getPropertyValue(
    name,
  );
  return value?.trim() || fallback;
}

export default function AppBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    let width = 0;
    let height = 0;
    let nodes = [];
    let animationFrame = null;
    let mouse = { x: null, y: null };

    function resize() {
      width = canvas.offsetWidth;
      height = canvas.offsetHeight;
      canvas.width = width * window.devicePixelRatio;
      canvas.height = height * window.devicePixelRatio;
      ctx.setTransform(
        window.devicePixelRatio,
        0,
        0,
        window.devicePixelRatio,
        0,
        0,
      );

      const count = width < 720 ? NODE_COUNT_MOBILE : NODE_COUNT_DESKTOP;
      nodes = Array.from({ length: count }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * SPEED,
        vy: (Math.random() - 0.5) * SPEED,
        r: Math.random() * 2.2 + 1.4,
      }));
    }

    function draw() {
      ctx.clearRect(0, 0, width, height);

      const dotColor = readCssVar("--accent-strong", "#d99b85");
      const lineColorA = readCssVar("--accent", "#cc785c");

      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];

        a.x += a.vx;
        a.y += a.vy;

        if (a.x < 0 || a.x > width) a.vx *= -1;
        if (a.y < 0 || a.y > height) a.vy *= -1;

        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < LINK_DISTANCE) {
            const opacity = (1 - dist / LINK_DISTANCE) * 0.38;
            ctx.strokeStyle = lineColorA;
            ctx.globalAlpha = opacity;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }

        if (mouse.x !== null) {
          const dx = a.x - mouse.x;
          const dy = a.y - mouse.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < LINK_DISTANCE * 1.3) {
            ctx.strokeStyle = dotColor;
            ctx.globalAlpha = (1 - dist / (LINK_DISTANCE * 1.3)) * 0.28;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(mouse.x, mouse.y);
            ctx.stroke();
          }
        }
      }

      ctx.globalAlpha = 0.85;
      ctx.fillStyle = dotColor;
      for (const n of nodes) {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;

      animationFrame = requestAnimationFrame(draw);
    }

    function handlePointerMove(e) {
      const rect = canvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    }

    function handlePointerLeave() {
      mouse.x = null;
      mouse.y = null;
    }

    resize();
    window.addEventListener("resize", resize);
    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerleave", handlePointerLeave);

    if (prefersReducedMotion) {
      draw();
      cancelAnimationFrame(animationFrame);
    } else {
      draw();
    }

    return () => {
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerleave", handlePointerLeave);
      if (animationFrame) cancelAnimationFrame(animationFrame);
    };
  }, []);

  return (
    <div className="app-background" aria-hidden="true">
      <div className="app-background-orb app-background-orb-a" />
      <div className="app-background-orb app-background-orb-b" />
      <div className="app-background-orb app-background-orb-c" />
      <canvas ref={canvasRef} className="app-background-canvas" />
    </div>
  );
}
