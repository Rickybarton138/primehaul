import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
  spring,
} from "remotion";
import { BG, RED, AMBER, GREEN, WHITE } from "../helpers/colors";
import { S2_DUR, FPS } from "../helpers/timing";
import { useEnvelope, clamp } from "../helpers/animations";
import { Vignette } from "../components/Vignette";

const PAIN_POINTS = [
  { icon: "\u{1F47B}", text: "Customers ghost you", color: RED, delay: 4 },
  { icon: "\u26FD", text: "Site visits waste hours", color: AMBER, delay: 7 },
  { icon: "\u{1F4B8}", text: "Competitors win first", color: RED, delay: 10 },
];

export const Scene2Problem: React.FC = () => {
  const f = useCurrentFrame();
  const env = useEnvelope(S2_DUR);

  // Red pulse behind pain cards
  const redPulse = interpolate(Math.sin(f * 0.06), [-1, 1], [0.05, 0.15]);

  // Cards fade out before transition
  const cardsFade = interpolate(f, [85, 100], [1, 0], clamp);

  // Green flash wipe
  const wipeX = interpolate(f, [95, 115], [-20, 120], clamp);
  const wipeOpacity = interpolate(f, [95, 102, 110, 120], [0, 0.9, 0.9, 0], clamp);

  // "There's a better way" text
  const betterProg = spring({
    frame: f,
    fps: FPS,
    from: 0,
    to: 1,
    delay: 108,
    durationInFrames: 14,
    config: { damping: 6, stiffness: 180 },
  });

  // Glow behind "better way" text
  const betterGlow = f > 110 ? interpolate(Math.sin(f * 0.1), [-1, 1], [20, 50]) : 0;

  return (
    <AbsoluteFill style={{ background: BG, ...env }}>
      {/* Subtle red ambient glow */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse at center, ${RED}${Math.round(redPulse * 255).toString(16).padStart(2, "0")} 0%, transparent 70%)`,
          opacity: cardsFade,
        }}
      />

      {/* Pain cards */}
      <AbsoluteFill
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 50,
          opacity: cardsFade,
        }}
      >
        {PAIN_POINTS.map((point, i) => {
          const prog = spring({
            frame: f,
            fps: FPS,
            from: 0,
            to: 1,
            delay: point.delay,
            durationInFrames: 12,
            config: { damping: 6, stiffness: 200 },
          });

          // Subtle shake on card land
          const shake = f > point.delay && f < point.delay + 6
            ? Math.sin(f * 40) * 3
            : 0;

          return (
            <div
              key={i}
              style={{
                opacity: prog,
                transform: `scale(${interpolate(prog, [0, 1], [0.3, 1])}) translateY(${interpolate(prog, [0, 1], [40, 0])}px) translateX(${shake}px)`,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 16,
                width: 300,
                padding: "28px 20px",
                background: `${point.color}06`,
                border: `1px solid ${point.color}20`,
                borderRadius: 20,
                boxShadow: `0 0 30px ${point.color}10`,
              }}
            >
              <div
                style={{
                  width: 90,
                  height: 90,
                  borderRadius: "50%",
                  background: `${point.color}10`,
                  border: `2px solid ${point.color}35`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 40,
                  boxShadow: `0 0 20px ${point.color}15`,
                }}
              >
                {point.icon}
              </div>
              <div
                style={{
                  fontSize: 26,
                  fontFamily: "sans-serif",
                  color: WHITE,
                  textAlign: "center",
                  fontWeight: 700,
                  lineHeight: 1.3,
                }}
              >
                {point.text}
              </div>
            </div>
          );
        })}
      </AbsoluteFill>

      {/* Green flash wipe — sweeps left to right */}
      <AbsoluteFill
        style={{
          background: `linear-gradient(90deg, transparent ${wipeX - 15}%, ${GREEN}80 ${wipeX}%, ${GREEN} ${wipeX + 2}%, ${GREEN}80 ${wipeX + 4}%, transparent ${wipeX + 20}%)`,
          opacity: wipeOpacity,
        }}
      />

      {/* "There's a better way." */}
      <AbsoluteFill
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          opacity: betterProg,
        }}
      >
        <div
          style={{
            fontSize: 60,
            fontFamily: "sans-serif",
            color: GREEN,
            fontWeight: 800,
            transform: `scale(${betterProg})`,
            textShadow: `0 0 ${betterGlow}px ${GREEN}50, 0 4px 20px rgba(0,0,0,0.4)`,
            letterSpacing: 1,
          }}
        >
          There's a better way.
        </div>
      </AbsoluteFill>

      <Vignette />
    </AbsoluteFill>
  );
};
