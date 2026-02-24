export const FPS = 30;
export const TRANS = 5; // Snappy hard cuts

// Scene durations (frames) — matched to ElevenLabs audio + visual buffer
export const S1_DUR = 90;   // Hook (3.0s)           — audio: 2.37s
export const S2_DUR = 165;  // Problem → Flip (5.5s) — audio: 4.23s
export const S3_DUR = 240;  // The Magic (8.0s)      — audio: 4.78s
export const S4_DUR = 180;  // Boss Approve (6.0s)   — audio: 3.81s
export const S5_DUR = 240;  // Results + CTA (8.0s)  — audio: 6.87s

// Scene start frames
export const S1_START = 0;
export const S2_START = S1_DUR;
export const S3_START = S2_START + S2_DUR;
export const S4_START = S3_START + S3_DUR;
export const S5_START = S4_START + S4_DUR;

export const TOTAL_FRAMES = S5_START + S5_DUR; // 915 frames ≈ 30.5s
