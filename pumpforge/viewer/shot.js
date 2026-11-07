// usage: node viewer/shot.js <model> <out.png> [query] [w] [h] [dpr]
const { chromium } = require('playwright');
(async () => {
  const [model, out, q = '', w = 1200, h = 900, dpr = 1] = process.argv.slice(2);
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: +dpr });
  p.on('console', m => { if (m.type() === 'error') console.log('console:', m.text()); });
  p.on('pageerror', e => console.log('pageerror:', e.message));
  await p.goto(`http://localhost:8765/viewer/index.html?shot=1&model=${model}&${q}`);
  await p.waitForFunction('window.__ready === true', null, { timeout: 120000 });
  await p.waitForTimeout(3000);
  await p.screenshot({ path: out });
  await b.close();
})();
