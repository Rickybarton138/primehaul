import React from "react";
import { AbsoluteFill, Sequence, Audio, staticFile } from "remotion";
import { BG } from "./helpers/colors";
import {
  S1_START,
  S1_DUR,
  S2_START,
  S2_DUR,
  S3_START,
  S3_DUR,
  S4_START,
  S4_DUR,
  S5_START,
  S5_DUR,
} from "./helpers/timing";
import { Scene1Intro } from "./scenes/Scene1Intro";
import { Scene2Problem } from "./scenes/Scene2Problem";
import { Scene3CustomerFlow } from "./scenes/Scene3CustomerFlow";
import { Scene4BossApprove } from "./scenes/Scene4BossApprove";
import { Scene5ResultsCTA } from "./scenes/Scene5ResultsCTA";

export const PrimeHaulDemo: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: BG }}>
      <Sequence from={S1_START} durationInFrames={S1_DUR} name="1. Hook">
        <Audio src={staticFile("s1.mp3")} volume={0.9} />
        <Scene1Intro />
      </Sequence>

      <Sequence from={S2_START} durationInFrames={S2_DUR} name="2. Problem">
        <Audio src={staticFile("s2.mp3")} volume={0.9} />
        <Scene2Problem />
      </Sequence>

      <Sequence from={S3_START} durationInFrames={S3_DUR} name="3. The Magic">
        <Audio src={staticFile("s3.mp3")} volume={0.9} />
        <Scene3CustomerFlow />
      </Sequence>

      <Sequence from={S4_START} durationInFrames={S4_DUR} name="4. Boss Approve">
        <Audio src={staticFile("s4.mp3")} volume={0.9} />
        <Scene4BossApprove />
      </Sequence>

      <Sequence from={S5_START} durationInFrames={S5_DUR} name="5. Results + CTA">
        <Audio src={staticFile("s5.mp3")} volume={0.9} />
        <Scene5ResultsCTA />
      </Sequence>
    </AbsoluteFill>
  );
};
