import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
  spring,
} from "remotion";
import { BG, GREEN, BLUE, AMBER, WHITE } from "../helpers/colors";
import { S5_DUR, FPS } from "../helpers/timing";
import { useEnvelope, useTypewriter, clamp } from "../helpers/animations";
import { Vignette } from "../components/Vignette";

const STATS = [
  { value: "10x", label: "Faster", color: GREEN, delay: 6 },
  { value: "30%", label: "More Jobs", color: BLUE, delay: 16 },
  { value: "0", label: "Site Visits", color: AMBER, delay: 26 },
];

export const Scene5ResultsCTA: React.FC = () => {
  const f = useCurrentFrame();
  const env = useEnvelope(S5_DUR);

  // Logo slam
  const logoProg = spring({
    frame: f,
    fps: FPS,
    from: 0,
    to: 1,
    delay: 60,
    durationInFrames: 12,
    config: { damping: 6, stiffness: 200 },
  });

  // CTA button
  const btnProg = spring({
    frame: f,
    fps: FPS,
    from: 0,
    to: 1,
    delay: 78,
    durationInFrames: 14,
    config: { damping: 7, stiffness: 140 },
  });
  const btnBreathe = f > 90 ? interpolate(Math.sin(f * 0.12), [-1, 1], [0.97, 1.04]) : 1;
  const btnGlow = f > 85 ? interpolate(Math.sin(f * 0.08), [-1, 1], [40, 100]) : 0;

  // URL typewriter with "Try it free at" prefix
  const prefixOpacity = interpolate(f, [100, 112], [0, 1], clamp);
  const url = useTypewriter("primehaul.co.uk", 115, 1.2);

  // Bottom glow ambient
  const ambientPulse = interpolate(Math.sin(f * 0.05), [-1, 1], [0.05, 0.15]);

  // Spinning ring behind logo (subtle)
  const ringAngle = f * 2.5;

  return (
    <AbsoluteFill style={{ background: BG, ...env }}>
      {/* Ambient glow at bottom */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse at 50% 85%, ${GREEN}${Math.round(ambientPulse * 255).toString(16).padStart(2, "0")} 0%, transparent 50%)`,
        }}
      />

      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 24,
        }}
      >
        {/* Stats row */}
        <div style={{ display: "flex", gap: 36 }}>
          {STATS.map((stat, i) => {
            const prog = spring({
              frame: f,
              fps: FPS,
              from: 0,
              to: 1,
              delay: stat.delay,
              durationInFrames: 14,
              config: { damping: 6, stiffness: 180 },
            });
            const countUp = interpolate(f, [stat.delay, stat.delay + 18], [0, 1], clamp);
            const glow = interpolate(Math.sin(f * 0.08 + i), [-1, 1], [0.4, 1]);
            // Impact shake on land
            const shake = f > stat.delay && f < stat.delay + 5 ? Math.sin(f * 45) * 3 : 0;

            return (
              <div
                key={i}
                style={{
                  opacity: prog,
                  transform: `scale(${interpolate(prog, [0, 1], [0.2, 1])}) translateY(${shake}px)`,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: 8,
                  padding: "22px 38px",
                  background: `${stat.color}06`,
                  border: `1px solid ${stat.color}20`,
                  borderRadius: 18,
                  minWidth: 210,
                  boxShadow: `0 0 24px ${stat.color}08`,
                }}
              >
                <div
                  style={{
                    fontSize: 68,
                    fontWeight: 900,
                    fontFamily: "monospace",
                    color: stat.color,
                    opacity: countUp,
                    textShadow: `0 0 ${22 * glow}px ${stat.color}50`,
                    letterSpacing: -2,
                  }}
                >
                  {stat.value}
                </div>
                <div
                  style={{
                    fontSize: 19,
                    color: "#bbb",
                    fontFamily: "sans-serif",
                    fontWeight: 600,
                  }}
                >
                  {stat.label}
                </div>
              </div>
            );
          })}
        </div>

        {/* Spinning ring behind logo */}
        <div style={{ position: "relative" }}>
          <div
            style={{
              position: "absolute",
              inset: -30,
              borderRadius: "50%",
              background: `conic-gradient(from ${ringAngle}deg, ${GREEN}20, transparent 25%, ${GREEN}10, transparent 50%, ${GREEN}20, transparent 75%, ${GREEN}20)`,
              opacity: logoProg * 0.4,
              filter: "blur(8px)",
            }}
          />
          {/* Logo */}
          <div
            style={{
              position: "relative",
              fontSize: 68,
              fontWeight: 900,
              fontFamily: "sans-serif",
              color: WHITE,
              letterSpacing: -3,
              opacity: logoProg,
              transform: `scale(${logoProg})`,
              textShadow: `0 0 30px ${GREEN}30, 0 4px 16px rgba(0,0,0,0.5)`,
            }}
          >
            Prime<span style={{ color: GREEN }}>Haul</span>
          </div>
        </div>

        {/* Try Free button with glow */}
        <div style={{ position: "relative", opacity: btnProg }}>
          <div
            style={{
              position: "absolute",
              inset: -24,
              borderRadius: 22,
              background: GREEN,
              filter: `blur(${btnGlow}px)`,
              opacity: 0.12,
            }}
          />
          <div
            style={{
              position: "relative",
              background: GREEN,
              color: "#000",
              fontWeight: 800,
              fontSize: 32,
              fontFamily: "sans-serif",
              padding: "18px 56px",
              borderRadius: 16,
              transform: `scale(${btnBreathe})`,
              boxShadow: `0 0 30px ${GREEN}35, 0 8px 30px rgba(0,0,0,0.5)`,
              letterSpacing: 1,
            }}
          >
            Try It Free
          </div>
        </div>

        {/* "Try it free at primehaul.co.uk" */}
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            gap: 10,
            opacity: prefixOpacity,
          }}
        >
          <div
            style={{
              fontSize: 24,
              fontFamily: "sans-serif",
              color: "#888",
              fontWeight: 500,
            }}
          >
            Try it free at
          </div>
          <div
            style={{
              fontSize: 32,
              fontFamily: "monospace",
              color: WHITE,
              fontWeight: 700,
              letterSpacing: 2,
            }}
          >
            {url}
            {url.length < 15 && (
              <span style={{ opacity: Math.sin(f * 0.3) > 0 ? 1 : 0, color: GREEN }}>|</span>
            )}
          </div>
        </div>
      </AbsoluteFill>

      <Vignette />
    </AbsoluteFill>
  );
};
