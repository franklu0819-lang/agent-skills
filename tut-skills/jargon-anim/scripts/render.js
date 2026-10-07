#!/usr/bin/env node
/* 逐帧渲染动画:确定性渲染 frame → Chrome 截图 → ffmpeg image2pipe 合成无声视频。
   用法:
     node render.js sample 300,600,900   # 抽帧存 build/preview/
     node render.js                      # 全量渲染 build/silent.mp4 */
const puppeteer = require(require("path").join(__dirname, "..", "node_modules", "puppeteer-core"));
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");

const BASE = path.resolve(__dirname, "..");
const tl = JSON.parse(fs.readFileSync(path.join(BASE, "timeline.json"), "utf8"));

// 构造场景边界(id 如 s1 → start=该场景首个 beat 的 start, end=末 beat 的 end)
const scenes = [];
for (const b of tl.beats) {
  const id = b.scene;
  let sc = scenes.find(s => s.id === id);
  if (!sc) { sc = { id, start: b.start, end: b.end }; scenes.push(sc); }
  sc.end = b.end;
}

async function main() {
  const mode = process.argv[2];
  const browser = await puppeteer.launch({
    executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    headless: "new",
    args: ["--no-sandbox", "--disable-gpu", "--force-color-profile=srgb",
           "--font-render-hinting=none", "--hide-scrollbars", "--force-device-scale-factor=1"],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: tl.resolution[0], height: tl.resolution[1], deviceScaleFactor: 1 });
  await page.goto("file://" + path.join(BASE, "anim", "index.html"));
  const beatsMap = {};
  for (const b of tl.beats) beatsMap[b.id] = b.start;
  await page.evaluate((sc, bm) => { window.__initScenes(sc, bm); }, scenes, beatsMap);
  await page.evaluate(() => window.renderFrame(0));

  if (mode === "sample") {
    if (!process.argv[3] || !/^\d+(,\d+)*$/.test(process.argv[3])) {
      console.error("用法: node tools/render.js sample 帧号[,帧号...]  如 sample 300,600,900");
      await browser.close(); process.exit(2);
    }
    const frames = process.argv[3].split(",").map(Number);
    fs.mkdirSync(path.join(BASE, "build", "preview"), { recursive: true });
    for (const f of frames) {
      await page.evaluate(fr => window.renderFrame(fr), f);
      await page.screenshot({ path: path.join(BASE, "build", "preview", `f${String(f).padStart(4, "0")}.png`) });
      console.log("sample", f, (f / tl.fps).toFixed(2) + "s");
    }
  } else {
    const out = path.join(BASE, "build", "silent.mp4");
    const ff = spawn("ffmpeg", ["-y", "-f", "image2pipe", "-framerate", String(tl.fps), "-i", "-",
      "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", out],
      { stdio: ["pipe", "inherit", "inherit"] });
    const t0 = Date.now();
    for (let f = 0; f < tl.frames; f++) {
      await page.evaluate(fr => window.renderFrame(fr), f);
      const buf = await page.screenshot({ type: "jpeg", quality: 92 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
      if (f % 300 === 0) console.log(`frame ${f}/${tl.frames} (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
    }
    ff.stdin.end();
    await new Promise(r => ff.on("close", r));
    console.log("silent.mp4 done in", ((Date.now() - t0) / 1000).toFixed(0) + "s");
  }
  await browser.close();
}
main().catch(e => { console.error(e); process.exit(1); });
