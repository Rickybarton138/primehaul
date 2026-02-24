import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
  spring,
} from "remotion";
import { BG, GREEN, WHITE } from "../helpers/colors";
import { S1_DUR, FPS } from "../helpers/timing";
import { useEnvelope, clamp } from "../helpers/animations";
import { Vignette } from "../components/Vignette";

export const Scene1Intro: React.FC = () => {
  const f = useCurrentFrame();
  const env = useEnvelope(S1_DUR);

  // Logo slams in hard — zero delay
  const logoScale = spring({
    frame: f,
    fps: FPS,
    from: 0,
    to: 1,
    delay: 1,
    durationInFrames: 10,
    config: { damping: 5, stiffness: 250 },
  });

  // Impact shockwave ring
  const ringScale = interpolate(f, [3, 20], [0, 3], clamp);
  const ringOpacity = interpolate(f, [3, 10, 20], [0, 0.5, 0], clamp);

  // Impact flash
  const flashOpacity = interpolate(f, [1, 5, 12], [0, 0.7, 0], clamp);

  // Subtle logo breathing after landing
  const breathe = f > 14 ? interpolate(Math.sin(f * 0.08), [-1, 1], [0.98, 1.02]) : 1;

  // Green glow pulses behind logo
  const glowSize = f > 10 ? interpolate(Math.sin(f * 0.1), [-1, 1], [80, 160]) : 0;
  const glowOpacity = interpolate(f, [10, 20], [0, 0.3], clamp);

  // Subtitle — "Your AI Surveyor" slides up
  const subProg = spring({
    frame: f,
    fps: FPS,
    from: 0,
    to: 1,
    delay: 22,
    durationInFrames: 14,
    config: { damping: 9, stiffness: 140 },
  });

  // Accent line grows from center
  const lineWidth = interpolate(f, [38, 58], [0, 240], clamp);

  return (
    <AbsoluteFill style={{ background: BG, ...env }}>
      {/* Full-screen flash on impact */}
      <AbsoluteFill
        style={{
          background: WHITE,
          opacity: flashOpacity,
        }}
      />

      {/* Shockwave ring */}
      <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            width: 300,
            height: 300,
            borderRadius: "50%",
            border: `3px solid ${GREEN}`,
            transform: `scale(${ringScale})`,
            opacity: ringOpacity,
          }}
        />
      </AbsoluteFill>

      {/* Green glow behind logo */}
      <AbsoluteFill style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div
          style={{
            width: 500,
            height: 200,
            borderRadius: "50%",
            background: `radial-gradient(circle, ${GREEN}30 0%, transparent 70%)`,
            filter: `blur(${glowSize * 0.3}px)`,
            opacity: glowOpacity,
          }}
        />
      </AbsoluteFill>

      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 20,
        }}
      >
        {/* Logo */}
        <div
          style={{
            fontSize: 150,
            fontWeight: 900,
            fontFamily: "sans-serif",
            color: WHITE,
            letterSpacing: -5,
            transform: `scale(${logoScale * breathe})`,
            textShadow: `0 0 ${glowSize}px ${GREEN}40, 0 4px 20px rgba(0,0,0,0.5)`,
          }}
        >
          Prime<span style={{ color: GREEN }}>Haul</span>
        </div>

        {/* "Your AI Surveyor" */}
        <div
          style={{
            fontSize: 46,
            fontFamily: "sans-serif",
            color: GREEN,
            fontWeight: 700,
            letterSpacing: 6,
            textTransform: "uppercase",
            opacity: subProg,
            transform: `translateY(${interpolate(subProg, [0, 1], [25, 0])}px)`,
            textShadow: `0 0 30px ${GREEN}30`,
          }}
        >
          Your AI Surveyor
        </div>

        {/* Accent underline */}
        <div
          style={{
            width: lineWidth,
            height: 3,
            background: `linear-gradient(90deg, transparent, ${GREEN}, transparent)`,
            borderRadius: 2,
            boxShadow: `0 0 12px ${GREEN}40`,
          }}
        />
      </AbsoluteFill>

      <Vignette />
    </AbsoluteFill>
  );
};
