// thinkx-system/citywalk/web-server/tests/ui/ui_legacy.test.js
//
// Screenshot and perceptual-property oracle for fixed-fixture legacy pages.

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {spawn} = require('node:child_process');
const test = require('node:test');
const {JSDOM} = require('jsdom');
const {chromium} = require('playwright-core');

const citywalkRoot = path.resolve(__dirname, '../../..');
const serverRoot = path.join(citywalkRoot, 'web-server');
const legacyScripts = path.join(citywalkRoot, 'legacy/www/server/application/scripts');
const goldenRoot = path.join(serverRoot, 'tests/golden/ui_legacy');
const chromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const origin = 'http://127.0.0.1:4173';
const pages = [
  ['business_top', '/business/top', null],
  ['business_signin', '/business/signin', null],
  ['business_signup', '/business/signup', {activatePage: 1, selector: '#map', pointerCount: 1}],
  ['business_home', '/business/home', null],
  ['business_createguide', '/business/createguide', {selector: '#map', pointerCount: 0}],
  ['business_settings', '/business/settings', null],
  ['index', '/', null],
];
const viewports = [
  ['mobile', {width: 375, height: 812}],
  ['desktop', {width: 1280, height: 900}],
];

function normalizedText(value) {
  return value.replace(/\s+/g, ' ').trim();
}

function sanitizedDiagnostic(value) {
  return value
    .replace(/AIza[0-9A-Za-z_-]{35}/g, '<GCP_KEY>')
    .replace(/([?&]key=)[^&\s]+/g, '$1<GCP_KEY>');
}

function semanticProperties(document) {
  const fields = [...document.querySelectorAll('input, select, textarea')].map(($field) => ({
    name: $field.getAttribute('name') || '',
    placeholder: $field.getAttribute('placeholder') || '',
    type: $field.getAttribute('type') || $field.tagName.toLowerCase(),
  }));
  const buttons = [...document.querySelectorAll('button')].map(($button) => ({
    disabled: $button.disabled,
    text: normalizedText($button.textContent),
  }));
  const links = [...document.querySelectorAll('a')].map(($link) => ({
    href: $link.getAttribute('href') || '',
    text: normalizedText($link.textContent),
  }));
  return {
    buttons,
    fields,
    links,
    text: normalizedText(document.body.textContent),
  };
}

async function waitForServer() {
  for (let attempt = 0; attempt < 50; attempt += 1) {
    try {
      const response = await fetch(`${origin}/healthcheck`);
      if (response.ok) return;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error('legacy UI fixture server did not start');
}

async function verifyGoogleMap(page, mapOracle, pageName) {
  const {pointerCount, selector} = mapOracle;
  await page.waitForFunction((mapSelector) => {
    const $map = document.querySelector(mapSelector);
    return $map && $map.clientWidth > 0 && $map.clientHeight > 0 && $map.querySelector('.gm-style');
  }, selector, {timeout: 30000});
  await page.waitForFunction((mapSelector) => {
    const $map = document.querySelector(mapSelector);
    return [...$map.querySelectorAll('img')].some(($image) => $image.complete && $image.naturalWidth > 0)
      || [...$map.querySelectorAll('canvas')].some(($canvas) => $canvas.width > 0 && $canvas.height > 0);
  }, selector, {timeout: 30000});
  const mapState = await page.evaluate(() => ({
    center: window.map ? window.map.getCenter().toJSON() : null,
    controls: document.querySelectorAll('.gm-control-active').length,
    pointerCount: typeof mapPointer !== 'undefined' && mapPointer ? 1 : 0,
    zoom: window.map ? window.map.getZoom() : null,
  }));
  assert.ok(mapState.center, `${pageName}: map center is missing`);
  assert.ok(mapState.controls > 0, `${pageName}: map controls are missing`);
  assert.equal(mapState.pointerCount, pointerCount);
  const previousZoom = mapState.zoom;
  await page.evaluate(() => window.map.setZoom(window.map.getZoom() + 1));
  await page.waitForFunction((zoom) => window.map.getZoom() === zoom + 1, previousZoom);
}

test('legacy UI perceptual oracle', async (context) => {
  fs.mkdirSync(goldenRoot, {recursive: true});
  const server = spawn(
    path.join(serverRoot, 'venv-legacy/bin/python'),
    [path.join(serverRoot, 'tests/legacy_ui_server.py')],
    {cwd: legacyScripts, stdio: ['ignore', 'pipe', 'pipe']},
  );
  context.after(() => server.kill('SIGTERM'));
  await waitForServer();

  const properties = {};
  for (const [pageName, route] of pages) {
    const dom = await JSDOM.fromURL(`${origin}${route}`);
    properties[pageName] = semanticProperties(dom.window.document);
  }
  const propertiesPath = path.join(goldenRoot, 'perceptual_legacy.json');
  if (process.env.UPDATE_GOLDENS === '1') {
    fs.writeFileSync(propertiesPath, `${JSON.stringify(properties, null, 2)}\n`);
  } else {
    assert.deepEqual(properties, JSON.parse(fs.readFileSync(propertiesPath)));
  }

  const browser = await chromium.launch({executablePath: chromePath, headless: true});
  context.after(() => browser.close());
  for (const [viewportName, viewport] of viewports) {
    const browserContext = await browser.newContext({viewport});
    for (const [pageName, route, mapOracle] of pages) {
      const page = await browserContext.newPage();
      const diagnostics = [];
      page.on('console', (message) => diagnostics.push(`console:${message.type()}:${message.text()}`));
      page.on('requestfailed', (request) => diagnostics.push(`requestfailed:${request.url()}:${request.failure()?.errorText}`));
      page.on('response', (response) => {
        if (response.status() >= 400) diagnostics.push(`response:${response.status()}:${response.url()}`);
      });
      await page.goto(`${origin}${route}`, {waitUntil: 'networkidle'});
      const masks = [];
      if (mapOracle) {
        try {
          if (mapOracle.activatePage !== undefined) {
            await page.evaluate((pageNumber) => {
              const $pages = document.querySelectorAll('.inputPageViewPage');
              $pages.forEach(($page) => {
                $page.style.display = Number($page.dataset.pageIndex) === pageNumber ? 'flex' : 'none';
              });
              google.maps.event.trigger(window.map, 'resize');
            }, mapOracle.activatePage);
          }
          await verifyGoogleMap(page, mapOracle, pageName);
          if (mapOracle.activatePage !== undefined) {
            await page.goto(`${origin}${route}`, {waitUntil: 'networkidle'});
          }
        } catch (error) {
          throw new Error(`${error.message}\n${diagnostics.map(sanitizedDiagnostic).join('\n')}`);
        }
        if (mapOracle.activatePage === undefined) masks.push(page.locator(mapOracle.selector));
      }
      const screenshotPath = path.join(goldenRoot, `${pageName}_${viewportName}.png`);
      if (process.env.UPDATE_GOLDENS === '1') {
        await page.screenshot({path: screenshotPath, fullPage: true, mask: masks});
      } else {
        assert.ok(fs.existsSync(screenshotPath), `${screenshotPath} is missing`);
        const current = await page.screenshot({fullPage: true, mask: masks});
        assert.deepEqual(current, fs.readFileSync(screenshotPath));
      }
      await page.close();
    }
    await browserContext.close();
  }
});
