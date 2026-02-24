import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
  spring,
} from "remotion";
import { BG, GREEN, BLUE, AMBER, WHITE, GRAY } from "../helpers/colors";
import { S4_DUR, FPS } from "../helpers/timing";
import { useEnvelope, clamp } from "../helpers/animations";
import { FloatingParticles } from "../components/FloatingParticles";
import { Vignette } from "../components/Vignette";

export const Scene4BossApprove: React.FC = () => {
  const f = useCurrentFrame();
  const env = useEnvelope(S4_DUR);

  // Title
  const titleProg = spring({
    frame: f,
    fps: FPS,
    from: 0,
    to: 1,
    delay: 3,
    durationInFrames: 10,
    config: { damping: 8 },
  });

  // Notification banner — vibrates in
  const notifProg = spring({
    frame: f,
    fps: FPS,
    from: 0,
    to: 1,
    delay: 8,
    durationInFrames: 10,
    config: { damping: 5, stiffness: 220 },
  });
  const notifShake = f > 8 && f < 15 ? Math.sin(f * 55) * 5 : 0;

  // Green dot pulse
  const dotPulse = interpolate(Math.sin(f * 0.15), [-1, 1], [0.6, 1]);

  // Price card slides up
  const priceProg = spring({
    frame: f,
    fps: FPS,
    from: 0,
    to: 1,
    delay: 32,
    durationInFrames: 14,
    config: { damping: 7, stiffness: 160 },
  });

  // Price glow effect
  const priceGlow = f > 40 ? interpolate(Math.sin(f * 0.1), [-1, 1], [10, 30]) : 0;

  // Approve button
  const btnProg = spring({
    frame: f,
    fps: FPS,
    from: 0,
    to: 1,
    delay: 65,
    durationInFrames: 12,
    config: { damping: 6, stiffness: 200 },
  });
  const btnBreathe = f > 70 && f < 90 ? interpolate(Math.sin(f * 0.15), [-1, 1], [0.97, 1.04]) : 1;
  const btnPressed = f > 90;

  // "Quote Sent" — big confirmation
  const sentProg = spring({
    frame: f,
    fps: FPS,
    from: 0,
    to: 1,
    delay: 93,
    durationInFrames: 14,
    config: { damping: 5, stiffness: 200 },
  });

  // Success flash
  const successFlash = interpolate(f, [90, 95, 105], [0, 0.3, 0], clamp);

  return (
    <AbsoluteFill style={{ background: BG, ...env }}>
      <FloatingParticles />

      {/* Success flash overlay */}
      <AbsoluteFill style={{ background: GREEN, opacity: successFlash }} />

      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 18,
        }}
      >
        {/* Title */}
        <div
          style={{
            fontSize: 28,
            fontFamily: "monospace",
            color: AMBER,
            letterSpacing: 6,
            textTransform: "uppercase",
            fontWeight: 700,
            opacity: titleProg,
            transform: `translateY(${interpolate(titleProg, [0, 1], [12, 0])}px)`,
          }}
        >
          Approve in Seconds
        </div>

        {/* Dashboard card */}
        <div
          style={{
            width: 760,
            background: "#0e0e14",
            borderRadius: 20,
            border: `1px solid ${BLUE}18`,
            padding: 22,
            display: "flex",
            flexDirection: "column",
            gap: 14,
            boxShadow: `0 20px 60px rgba(0,0,0,0.6), 0 0 40px ${BLUE}06`,
          }}
        >
          {/* Notification */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              opacity: notifProg,
              transform: `translateY(${interpolate(notifProg, [0, 1], [-20, 0])}px) translateX(${notifShake}px)`,
              background: `${GREEN}06`,
              border: `1px solid ${GREEN}18`,
              borderRadius: 10,
              padding: "10px 14px",
            }}
          >
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: "50%",
                background: GREEN,
                boxShadow: `0 0 ${12 * dotPulse}px ${GREEN}80`,
              }}
            />
            <div style={{ fontSize: 16, fontFamily: "monospace", color: GREEN, fontWeight: 600 }}>
              New survey — Sarah M.
            </div>
            <div style={{ fontSize: 13, fontFamily: "monospace", color: "#666", marginLeft: "auto" }}>
              London → Manchester
            </div>
            <div style={{ fontSize: 12, fontFamily: "monospace", color: GRAY }}>Just now</div>
          </div>

          {/* Price card */}
          <div
            style={{
              opacity: priceProg,
              transform: `translateY(${interpolate(priceProg, [0, 1], [20, 0])}px)`,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              background: `${BLUE}06`,
              border: `1px solid ${BLUE}20`,
              borderRadius: 14,
              padding: "16px 22px",
            }}
          >
            <div>
              <div style={{ fontSize: 22, fontWeight: 700, color: WHITE, fontFamily: "sans-serif" }}>
                2 Bed Flat Move
              </div>
              <div style={{ fontSize: 14, color: "#777", fontFamily: "monospace", marginTop: 4, display: "flex", gap: 12 }}>
                <span>24 items</span>
                <span style={{ color: BLUE }}>8.99 m³</span>
                <span>229 kg</span>
              </div>
            </div>
            <div
              style={{
                fontSize: 50,
                fontWeight: 900,
                fontFamily: "monospace",
                color: GREEN,
                textShadow: `0 0 ${priceGlow}px ${GREEN}50`,
              }}
            >
              £925
            </div>
          </div>

          {/* Approve / Sent */}
          <div style={{ alignSelf: "center", minHeight: 56 }}>
            {!btnPressed ? (
              <div
                style={{
                  opacity: btnProg,
                  background: GREEN,
                  color: "#000",
                  fontWeight: 800,
                  fontSize: 20,
                  fontFamily: "sans-serif",
                  padding: "14px 40px",
                  borderRadius: 14,
                  boxShadow: `0 0 24px ${GREEN}35, 0 6px 20px rgba(0,0,0,0.4)`,
                  transform: `scale(${btnBreathe})`,
                  letterSpacing: 0.5,
                }}
              >
                Approve & Send Quote ✓
              </div>
            ) : (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  transform: `scale(${sentProg})`,
                }}
              >
                <div style={{ fontSize: 40, filter: `drop-shadow(0 0 12px ${GREEN}90)` }}>
                  ✅
                </div>
                <div style={{ fontSize: 26, fontFamily: "sans-serif", color: GREEN, fontWeight: 800, letterSpacing: 2 }}>
                  QUOTE SENT
                </div>
              </div>
            )}
          </div>
        </div>
      </AbsoluteFill>

      <Vignette />
    </AbsoluteFill>
  );
};
