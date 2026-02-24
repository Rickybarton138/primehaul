import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
  spring,
} from "remotion";
import { BG, GREEN, BLUE, AMBER, WHITE } from "../helpers/colors";
import { S3_DUR, FPS } from "../helpers/timing";
import { useEnvelope, clamp } from "../helpers/animations";
import { FloatingParticles } from "../components/FloatingParticles";
import { Vignette } from "../components/Vignette";
import { PhoneFrame } from "../components/PhoneFrame";

const ROOMS = [
  { label: "Living Room", icon: "\u{1F6CB}\uFE0F", delay: 12 },
  { label: "Bedroom", icon: "\u{1F6CF}\uFE0F", delay: 18 },
  { label: "Kitchen", icon: "\u{1F373}", delay: 24 },
  { label: "Garage", icon: "\u{1F527}", delay: 30 },
];

const DETECTED_ITEMS = [
  { name: "3-Seater Sofa", vol: "1.80 m\u00B3", delay: 115, y: 6 },
  { name: "Double Wardrobe", vol: "2.14 m\u00B3", delay: 128, y: 30 },
  { name: "Dining Table + 4 Chairs", vol: "1.45 m\u00B3", delay: 141, y: 54 },
  { name: "Moving Boxes x12", vol: "3.60 m\u00B3", delay: 154, y: 78 },
];

export const Scene3CustomerFlow: React.FC = () => {
  const f = useCurrentFrame();
  const env = useEnvelope(S3_DUR);

  // Phase 1: Photo grid (frames 0-85)
  // Phase 2: Scan + detect (frames 85-240)
  const isScanning = f > 85;

  // Smooth crossfade between phases
  const phase2Opacity = interpolate(f, [82, 92], [0, 1], clamp);
  const phase1Opacity = interpolate(f, [78, 88], [1, 0], clamp);

  // Scan line sweeps vertically down the phone
  const scanY = interpolate(f, [90, 160], [-5, 105], clamp);
  const scanOpacity = interpolate(f, [90, 98, 155, 168], [0, 1, 1, 0], clamp);

  // Title
  const titleProg = spring({
    frame: f,
    fps: FPS,
    from: 0,
    to: 1,
    delay: 3,
    durationInFrames: 12,
    config: { damping: 8 },
  });

  // Title text swap
  const title2Prog = spring({
    frame: f,
    fps: FPS,
    from: 0,
    to: 1,
    delay: 88,
    durationInFrames: 10,
    config: { damping: 8 },
  });

  // Side stats
  const statsFade = interpolate(f, [125, 140], [0, 1], clamp);

  // Totals counter
  const totalCBM = interpolate(f, [140, 185], [0, 8.99], clamp);
  const totalItems = interpolate(f, [140, 185], [0, 24], clamp);

  return (
    <AbsoluteFill style={{ background: BG, ...env }}>
      <FloatingParticles />

      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 22,
        }}
      >
        {/* Animated title */}
        <div style={{ position: "relative", height: 40 }}>
          <div
            style={{
              fontSize: 28,
              fontFamily: "monospace",
              color: GREEN,
              letterSpacing: 6,
              textTransform: "uppercase",
              fontWeight: 700,
              opacity: titleProg * phase1Opacity,
              transform: `translateY(${interpolate(titleProg, [0, 1], [15, 0])}px)`,
              position: "absolute",
              whiteSpace: "nowrap",
              left: "50%",
              transform: `translateX(-50%) translateY(${interpolate(titleProg, [0, 1], [15, 0])}px)`,
            }}
          >
            Customer Snaps Photos
          </div>
          <div
            style={{
              fontSize: 28,
              fontFamily: "monospace",
              color: BLUE,
              letterSpacing: 6,
              textTransform: "uppercase",
              fontWeight: 700,
              opacity: title2Prog * phase2Opacity,
              transform: `translateX(-50%) translateY(${interpolate(title2Prog, [0, 1], [15, 0])}px)`,
              position: "absolute",
              whiteSpace: "nowrap",
              left: "50%",
            }}
          >
            AI Detects Everything
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 36 }}>
          {/* Phone */}
          <PhoneFrame color={isScanning ? BLUE : GREEN} width={280} height={530}>
            {/* Phase 1: Photo grid */}
            <div
              style={{
                position: "absolute",
                inset: 0,
                padding: 8,
                display: "flex",
                flexDirection: "column",
                gap: 6,
                opacity: phase1Opacity,
              }}
            >
              <div style={{ fontSize: 11, color: GREEN, fontFamily: "monospace", fontWeight: 700, paddingTop: 16 }}>
                ROOM-BY-ROOM PHOTOS
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, flex: 1 }}>
                {ROOMS.map((room, i) => {
                  const prog = spring({
                    frame: f,
                    fps: FPS,
                    from: 0,
                    to: 1,
                    delay: room.delay,
                    durationInFrames: 10,
                    config: { damping: 6, stiffness: 200 },
                  });
                  // Camera flash effect
                  const flash = f === room.delay + 2 || f === room.delay + 3 ? 0.6 : 0;
                  return (
                    <div
                      key={i}
                      style={{
                        background: `${GREEN}08`,
                        border: `1px solid ${GREEN}20`,
                        borderRadius: 8,
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: 4,
                        opacity: prog,
                        transform: `scale(${interpolate(prog, [0, 1], [0.4, 1])})`,
                        boxShadow: flash > 0 ? `inset 0 0 20px ${WHITE}${Math.round(flash * 255).toString(16).padStart(2, "0")}` : "none",
                        position: "relative",
                      }}
                    >
                      <div style={{ fontSize: 26 }}>{room.icon}</div>
                      <div style={{ fontSize: 9, color: "#aaa", fontFamily: "monospace" }}>{room.label}</div>
                      <div style={{ fontSize: 7, color: GREEN, fontFamily: "monospace" }}>4 photos</div>
                      {/* Check mark after snap */}
                      {f > room.delay + 8 && (
                        <div style={{ position: "absolute", top: 4, right: 4, fontSize: 10, opacity: interpolate(f, [room.delay + 8, room.delay + 12], [0, 1], clamp) }}>
                          ✅
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Phase 2: Scan + detection */}
            <div
              style={{
                position: "absolute",
                inset: 0,
                padding: 8,
                opacity: phase2Opacity,
                overflow: "hidden",
              }}
            >
              {/* Grid background */}
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  backgroundImage: `linear-gradient(${BLUE}08 1px, transparent 1px), linear-gradient(90deg, ${BLUE}08 1px, transparent 1px)`,
                  backgroundSize: "20px 20px",
                }}
              />

              {/* Scan line — horizontal sweep */}
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  right: 0,
                  top: `${scanY}%`,
                  height: 3,
                  background: `linear-gradient(90deg, transparent 5%, ${GREEN} 20%, ${GREEN} 80%, transparent 95%)`,
                  boxShadow: `0 0 24px ${GREEN}70, 0 -15px 30px ${GREEN}15, 0 15px 30px ${GREEN}15`,
                  opacity: scanOpacity,
                  zIndex: 10,
                }}
              />

              {/* Detected item rows */}
              {DETECTED_ITEMS.map((item, i) => {
                const prog = spring({
                  frame: f,
                  fps: FPS,
                  from: 0,
                  to: 1,
                  delay: item.delay,
                  durationInFrames: 10,
                  config: { damping: 6, stiffness: 200 },
                });
                return (
                  <div
                    key={i}
                    style={{
                      position: "absolute",
                      left: 10,
                      right: 10,
                      top: `${item.y}%`,
                      opacity: prog,
                      transform: `scale(${interpolate(prog, [0, 1], [0.7, 1])})`,
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      background: `${GREEN}12`,
                      border: `1px solid ${GREEN}30`,
                      borderRadius: 6,
                      padding: "7px 10px",
                      boxShadow: `0 0 12px ${GREEN}10`,
                    }}
                  >
                    <div style={{ fontSize: 10, fontFamily: "monospace", color: WHITE, fontWeight: 700 }}>
                      {item.name}
                    </div>
                    <div style={{ fontSize: 9, fontFamily: "monospace", color: BLUE, background: `${BLUE}20`, padding: "2px 6px", borderRadius: 4, fontWeight: 700 }}>
                      {item.vol}
                    </div>
                  </div>
                );
              })}
            </div>
          </PhoneFrame>

          {/* Side panel — stats during scan phase */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 14,
              opacity: statsFade,
              transform: `translateX(${interpolate(statsFade, [0, 1], [20, 0])}px)`,
            }}
          >
            {[
              { label: "Total Volume", value: `${totalCBM.toFixed(1)} m\u00B3`, color: BLUE, icon: "\u{1F4E6}" },
              { label: "Items Found", value: `${Math.floor(totalItems)}`, color: GREEN, icon: "\u{1F50D}" },
              { label: "Accuracy", value: "99.2%", color: AMBER, icon: "\u{1F3AF}" },
            ].map((stat, i) => (
              <div
                key={i}
                style={{
                  background: `${stat.color}08`,
                  border: `1px solid ${stat.color}25`,
                  borderRadius: 14,
                  padding: "14px 28px",
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  boxShadow: `0 0 20px ${stat.color}08`,
                }}
              >
                <div style={{ fontSize: 24 }}>{stat.icon}</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                  <div style={{ fontSize: 11, fontFamily: "monospace", color: "#888", textTransform: "uppercase", letterSpacing: 1 }}>
                    {stat.label}
                  </div>
                  <div style={{ fontSize: 30, fontWeight: 900, fontFamily: "monospace", color: stat.color, textShadow: `0 0 12px ${stat.color}30` }}>
                    {stat.value}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </AbsoluteFill>

      <Vignette />
    </AbsoluteFill>
  );
};
