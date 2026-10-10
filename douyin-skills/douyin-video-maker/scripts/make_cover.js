#!/usr/bin/env node
/* 合集封面生成:封面模版(合集自定义 > 期目录 > 技能自带) + collection.json 主题变量
   → 填充本期标题/期号 → Chrome 截图 1080x1920 → <期目录>/cover.jpg
   用法:
     node tools/make_cover.js              # 在期目录内运行(或 node tools/make_cover.js <期目录>)
     node tools/make_cover.js --all        # 在合集目录内运行,按期号重出全部封面(改模版后用) */
const puppeteer = require(require("path").join(__dirname, "..", "node_modules", "puppeteer-core"));
const fs = require("fs");
const path = require("path");

function findSkillTemplates() {
  // 候选:环境变量 > 脚本所在技能目录(未复制时) > 从期目录向上逐级找 <工作区>/.zcode/skills/...
  const direct = [
    process.env.DOUYIN_MAKER_SKILL_DIR && path.join(process.env.DOUYIN_MAKER_SKILL_DIR, "templates"),
    path.join(__dirname, "..", "templates"),
  ].filter(Boolean);
  for (const c of direct) {
    if (fs.existsSync(path.join(c, "cover.template.html"))) return c;
  }
  let d = __dirname;
  for (let i = 0; i < 6; i++) {
    d = path.join(d, "..");
    const c = path.join(d, ".zcode", "skills", "douyin-video-maker", "templates");
    if (fs.existsSync(path.join(c, "cover.template.html"))) return c;
  }
  console.error("找不到技能自带封面模版(可设 DOUYIN_MAKER_SKILL_DIR 指向技能安装目录)");
  process.exit(2);
}

function esc(s) {
  return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function renderTemplate(tplHtml, script, col, epCount) {
  const ep = script.episode || 1;
  const vars = {
    COLLECTION: esc((col && col.name) || script.collection || ""),
    EP: String(ep),
    EP02: String(ep).padStart(2, "0"),
    EP_CN: `第${String(ep).padStart(2, "0")}期`,
    TITLE: esc(script.title || script.slug || ""),
    HOOK: esc(script.hook || ""),
    SLUG: esc(script.slug || ""),
    EPISODES: String(epCount),                      // 合集已更期数(含本期)
    PROGRESS: `${Math.min(100, Math.max(4, epCount * 25))}%`,
  };
  return tplHtml.replace(/\{\{(\w+)\}\}/g, (m, k) => (k in vars ? vars[k] : m));
}

async function makeOne(browser, epDir) {
  const sp = path.join(epDir, "script.json");
  if (!fs.existsSync(sp)) { console.error("skip(无 script.json): " + epDir); return false; }
  const script = JSON.parse(fs.readFileSync(sp, "utf8"));
  const colDir = path.resolve(epDir, "..");
  const colPath = path.join(colDir, "collection.json");
  const col = fs.existsSync(colPath) ? JSON.parse(fs.readFileSync(colPath, "utf8")) : {};
  // 模版查找:合集自定义 > 期目录(手工复制) > 技能自带
  const tplPath = [path.join(colDir, "cover.template.html"),
                   path.join(epDir, "cover.template.html"),
                   path.join(findSkillTemplates(), "cover.template.html")]
                  .find(p => fs.existsSync(p));
  // 合集已更期数 = 合集目录下含 script.json 的期目录数
  const epCount = fs.readdirSync(colDir).filter(d =>
    fs.existsSync(path.join(colDir, d, "script.json"))).length || 1;
  const html = renderTemplate(fs.readFileSync(tplPath, "utf8"), script, col, epCount);
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
  await page.setContent(html, { waitUntil: "networkidle0" });
  // 合集主题变量注入 CSS 自定义属性(collection.json 的 cover.palette,如 c-main/c-accent/c-bg)
  const palette = (col.cover && col.cover.palette) || {};
  await page.evaluate(p => {
    for (const [k, v] of Object.entries(p)) document.documentElement.style.setProperty("--" + k, v);
  }, palette);
  const out = path.join(epDir, "cover.jpg");
  await page.screenshot({ type: "jpeg", quality: 92, path: out });
  await page.close();
  console.log(`cover ok: ${out}  (第${String(script.episode || 0).padStart(2, "0")}期 ${script.title || script.slug || ""})`);
  return true;
}

async function main() {
  const arg = process.argv[2];
  const browser = await puppeteer.launch({
    executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    headless: "new",
    args: ["--no-sandbox", "--disable-gpu", "--force-color-profile=srgb",
           "--font-render-hinting=none", "--hide-scrollbars", "--force-device-scale-factor=1"],
  });
  try {
    if (arg === "--all") {
      const colDir = process.cwd();
      const eps = fs.readdirSync(colDir).filter(d =>
        fs.existsSync(path.join(colDir, d, "script.json"))).sort();
      let n = 0;
      for (const d of eps) { if (await makeOne(browser, path.join(colDir, d))) n++; }
      console.log(`--all done: ${n} 张封面`);
    } else {
      await makeOne(browser, arg ? path.resolve(arg) : process.cwd());
    }
  } finally { await browser.close(); }
}
main().catch(e => { console.error(e); process.exit(1); });
