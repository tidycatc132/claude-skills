#!/usr/bin/env node
// Render the client-facing WISE audit report PDF from an audit.json.
//
// Usage: node render_report.mjs AUDIT.json OUT.pdf
//
// Serves assets/report/ on a local port, answers /audit-data/audit.json with the
// given file, serves React and Babel from assets/report/vendor/ (so no network is
// needed) and prints the page with headless Chromium. Needs Node 18+ and the
// `playwright` package with a Chromium build (`npm i -g playwright`, then
// `npx playwright install chromium`). Set CHROME_PATH to use an installed Chrome
// or Chromium instead. Exits non-zero unless the PDF has exactly 2 pages.
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..', 'assets', 'report');
const [auditPath, outPath] = process.argv.slice(2);
if (!auditPath || !outPath) {
  console.error('Usage: node render_report.mjs AUDIT.json OUT.pdf');
  process.exit(2);
}
let audit;
try {
  audit = fs.readFileSync(auditPath);
  JSON.parse(audit);
} catch (err) {
  console.error(`Cannot read ${auditPath} as JSON: ${err.message}`);
  process.exit(2);
}

function loadPlaywright() {
  const require = createRequire(import.meta.url);
  try {
    return require('playwright');
  } catch {
    const globalRoot = execSync('npm root -g', { encoding: 'utf8' }).trim();
    return createRequire(path.join(globalRoot, 'x.js'))('playwright');
  }
}

const types = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.ttf': 'font/ttf',
};
const vendor = {
  'react@18.3.1/umd/react.production.min.js': 'react.production.min.js',
  'react-dom@18.3.1/umd/react-dom.production.min.js': 'react-dom.production.min.js',
  '@babel/standalone@7.29.0/babel.min.js': 'babel.min.js',
};

const server = http.createServer((req, res) => {
  const urlPath = decodeURIComponent(req.url.split('?')[0]);
  if (urlPath === '/audit-data/audit.json') {
    res.writeHead(200, { 'content-type': types['.json'] });
    res.end(audit);
    return;
  }
  const file = path.join(root, path.normalize(urlPath));
  if (!file.startsWith(root)) {
    res.writeHead(403);
    res.end();
    return;
  }
  fs.readFile(file, (err, body) => {
    if (err) {
      res.writeHead(404);
      res.end();
      return;
    }
    res.writeHead(200, { 'content-type': types[path.extname(file)] || 'application/octet-stream' });
    res.end(body);
  });
});

server.listen(0, '127.0.0.1', async () => {
  const { chromium } = loadPlaywright();
  const browser = await chromium.launch(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {});
  let code = 0;
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('console', (m) => {
      if (m.type() === 'error') errors.push(m.text());
    });
    await page.route('https://unpkg.com/**', (route) => {
      const key = route.request().url().replace('https://unpkg.com/', '');
      if (!vendor[key]) return route.abort();
      return route.fulfill({ path: path.join(root, 'vendor', vendor[key]), contentType: 'application/javascript' });
    });
    const url = `http://127.0.0.1:${server.address().port}/${encodeURIComponent('WISE Audit Report Template.dc.html')}`;
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForFunction(() => document.querySelectorAll('section.page').length > 0, null, { timeout: 15000 });
    await page.waitForTimeout(1500);
    fs.mkdirSync(path.dirname(path.resolve(outPath)), { recursive: true });
    const pdf = await page.pdf({ path: outPath, format: 'Letter', printBackground: true, preferCSSPageSize: true });
    const pages = (pdf.toString('latin1').match(/\/Type\s*\/Page[^s]/g) || []).length;
    for (const e of errors) console.error(`page error: ${e}`);
    if (pages !== 2) {
      console.error(`Expected 2 pages, got ${pages}: shorten the observations or summaries.`);
      code = 1;
    } else {
      console.log(`Saved ${outPath} (2 pages)`);
    }
  } finally {
    await browser.close();
    server.close();
  }
  process.exit(code);
});
