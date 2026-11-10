// node bake.js <out.json>   (serves the repo root on :8766 itself)
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '../../..');
const srv = http.createServer((q, s) => { const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0]));
  fs.readFile(f, (e, d) => { if (e) { s.writeHead(404); s.end(); return; } s.writeHead(200, { 'Content-Type': f.endsWith('.js') ? 'text/javascript' : 'text/html' }); s.end(d); }); }).listen(8766);
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage(); p.on('pageerror', e => console.log('pageerror', e.message)); p.on('console', m => console.log('console', m.text()));
  await p.goto('http://localhost:8766/native/tools/envgen/env.html');
  await p.waitForFunction('window.__env', null, { timeout: 120000 });
  fs.writeFileSync(process.argv[2], JSON.stringify(await p.evaluate('window.__env')));
  await b.close(); srv.close();
})();
