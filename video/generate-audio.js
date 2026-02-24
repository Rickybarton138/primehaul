const fs = require("fs");
const path = require("path");

const API_KEY = process.env.ELEVENLABS_API_KEY || "sk_37d6b8b433874b0dde1d2305ce31dcd961d6bf2cd8fad32b";
const VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"; // George — British male, turbo v2.5

const scenes = [
  {
    file: "s1.mp3",
    text: "PrimeHaul. Your AI surveyor.",
  },
  {
    file: "s2.mp3",
    text: "Customers ghost you. Site visits waste hours. There's a better way.",
  },
  {
    file: "s3.mp3",
    text: "Your customer snaps photos. AI detects every item instantly.",
  },
  {
    file: "s4.mp3",
    text: "You approve from your phone. Done in thirty seconds.",
  },
  {
    file: "s5.mp3",
    text: "Ten times faster. Thirty percent more jobs. Try it free at primehaul dot co dot UK.",
  },
];

async function generate() {
  const outDir = path.join(__dirname, "public");
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir);

  for (const scene of scenes) {
    console.log(`Generating ${scene.file}...`);
    try {
      const response = await fetch(
        `https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}`,
        {
          method: "POST",
          headers: {
            "xi-api-key": API_KEY,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            text: scene.text,
            model_id: "eleven_turbo_v2_5",
            voice_settings: {
              stability: 0.25,
              similarity_boost: 0.7,
              style: 0.7,
              use_speaker_boost: true,
            },
          }),
        }
      );

      if (!response.ok) {
        const err = await response.text();
        throw new Error(`HTTP ${response.status}: ${err}`);
      }

      const buffer = Buffer.from(await response.arrayBuffer());
      fs.writeFileSync(path.join(outDir, scene.file), buffer);
      console.log(`  Done: ${scene.file} (${buffer.length} bytes)`);
    } catch (err) {
      console.error(`  FAILED: ${scene.file} - ${err.message}`);
    }
  }

  console.log("\nAll done!");
}

generate();
