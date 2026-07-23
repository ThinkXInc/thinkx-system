const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {spawn} = require('node:child_process');
const {chromium} = require('playwright-core');

const citywalkRoot = path.resolve(__dirname, '../../..');
const serverRoot = path.join(citywalkRoot, 'web-server');
const legacyScripts = path.join(citywalkRoot, 'legacy/www/server/application/scripts');
const outputRoot = process.env.CITYWALK_MOTION_OUTPUT
  ? path.resolve(process.env.CITYWALK_MOTION_OUTPUT)
  : path.join(serverRoot, 'tests/golden/ui_legacy/motion');
const origin = 'http://127.0.0.1:4173';
const chromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

async function waitForServer(serverLog) {
  for (let attempt = 0; attempt < 50; attempt += 1) {
    try {
      const response = await fetch(`${origin}/healthcheck`);
      if (response.ok) return;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`legacy UI server did not start\n${serverLog.join('')}`);
}

async function startSampling(page, flowId, selectors) {
  await page.evaluate(({id, observedSelectors}) => {
    window.__citywalkMotion ??= {};
    const startedAt = performance.now();
    const samples = [];
    window.__citywalkMotion[id] = {done: false, samples, startedAt};

    function sample(timestamp) {
      const elements = Object.fromEntries(observedSelectors.map((selector) => {
        const element = document.querySelector(selector);
        if (!element) return [selector, null];
        const rect = element.getBoundingClientRect();
        const style = getComputedStyle(element);
        return [selector, {
          display: style.display,
          opacity: Number(style.opacity),
          transform: style.transform,
          x: rect.x,
          y: rect.y,
          width: rect.width,
          height: rect.height,
          text: element.textContent.replace(/\s+/g, ' ').trim(),
        }];
      }));
      const center = window.map?.getCenter?.();
      const translationList = document.querySelector('#translateResultsTableView .listContainer');
      samples.push({
        elapsed_ms: Number((timestamp - startedAt).toFixed(3)),
        elements,
        map: center ? {center: center.toJSON(), zoom: window.map.getZoom()} : null,
        translation: translationList ? {
          count: translationList.children.length,
          scroll_height: translationList.scrollHeight,
          scroll_top: translationList.scrollTop,
        } : null,
      });
      if (!window.__citywalkMotion[id].done) requestAnimationFrame(sample);
    }
    requestAnimationFrame(sample);
  }, {id: flowId, observedSelectors: selectors});
}

async function finishSampling(page, flowId) {
  return page.evaluate((id) => {
    window.__citywalkMotion[id].done = true;
    return window.__citywalkMotion[id].samples;
  }, flowId);
}

async function startScreencast(cdp, flowId) {
  assert.match(flowId, /^[a-z0-9]+(?:-[a-z0-9]+)*$/, `${flowId}: invalid flow ID`);
  const frameRoot = path.join(outputRoot, flowId);
  fs.rmSync(frameRoot, {recursive: true, force: true});
  fs.mkdirSync(frameRoot, {recursive: true});
  const frames = [];
  let frameNumber = 0;
  let resolveFirstFrame;
  const firstFrame = new Promise((resolve) => {
    resolveFirstFrame = resolve;
  });
  const onFrame = async (event) => {
    const filename = `frame-${String(frameNumber).padStart(5, '0')}.png`;
    fs.writeFileSync(path.join(frameRoot, filename), Buffer.from(event.data, 'base64'));
    frames.push({filename, timestamp: event.metadata.timestamp});
    if (frames.length === 1) resolveFirstFrame();
    frameNumber += 1;
    await cdp.send('Page.screencastFrameAck', {sessionId: event.sessionId});
  };
  cdp.on('Page.screencastFrame', onFrame);
  await cdp.send('Page.startScreencast', {
    format: 'png',
    everyNthFrame: 1,
    maxHeight: 856,
    maxWidth: 1490,
  });
  let firstFrameTimeout;
  try {
    await Promise.race([
      firstFrame,
      new Promise((resolve, reject) => {
        firstFrameTimeout = setTimeout(
          () => reject(new Error(`${flowId}: no initial screencast frame captured`)),
          5000,
        );
      }),
    ]);
  } catch (error) {
    await cdp.send('Page.stopScreencast');
    cdp.off('Page.screencastFrame', onFrame);
    throw error;
  } finally {
    clearTimeout(firstFrameTimeout);
  }
  return async () => {
    await cdp.send('Page.stopScreencast');
    cdp.off('Page.screencastFrame', onFrame);
    assert.ok(frames.length > 1, `${flowId}: fewer than two screencast frames captured`);
    const durations = frames.slice(1).map((frame, index) => frame.timestamp - frames[index].timestamp);
    assert.ok(durations.every((duration) => duration > 0), `${flowId}: screencast timestamps are not increasing`);
    const concatLines = ['ffconcat version 1.0'];
    frames.forEach((frame, index) => {
      concatLines.push(`file '${frame.filename}'`);
      concatLines.push(`duration ${index < durations.length ? durations[index] : durations.at(-1)}`);
    });
    concatLines.push(`file '${frames.at(-1).filename}'`);
    fs.writeFileSync(path.join(frameRoot, 'frames.ffconcat'), `${concatLines.join('\n')}\n`);
    return frames;
  };
}

async function captureFlow(page, cdp, flowId, selectors, action, settleMs) {
  const finishScreencast = await startScreencast(cdp, flowId);
  await startSampling(page, flowId, selectors);
  await action();
  await page.waitForTimeout(settleMs);
  const samples = await finishSampling(page, flowId);
  const frames = await finishScreencast();
  assert.ok(samples.length > 1, `${flowId}: no animation samples captured`);
  return {id: flowId, frames, samples};
}

async function main() {
  assert.ok(process.env.CITYWALK_GOOGLE_MAPS_API_KEY, 'CITYWALK_GOOGLE_MAPS_API_KEY is required');
  fs.mkdirSync(outputRoot, {recursive: true});

  const server = spawn(
    path.join(serverRoot, 'venv-legacy/bin/python'),
    [path.join(serverRoot, 'tests/legacy_ui_server.py')],
    {cwd: legacyScripts, stdio: ['ignore', 'pipe', 'pipe']},
  );
  const serverLog = [];
  server.stdout.on('data', (chunk) => serverLog.push(chunk.toString()));
  server.stderr.on('data', (chunk) => serverLog.push(chunk.toString()));

  let browser;
  try {
    await waitForServer(serverLog);
    browser = await chromium.launch({executablePath: chromePath, headless: true});
    const context = await browser.newContext({
      recordVideo: {dir: outputRoot, size: {width: 1490, height: 856}},
      viewport: {width: 1490, height: 856},
    });
    const page = await context.newPage();
    const cdp = await context.newCDPSession(page);
    const video = page.video();
    await page.goto(`${origin}/business/createguide`, {waitUntil: 'networkidle'});
    await page.waitForFunction(() => document.querySelectorAll('#contentTableView > li').length === 4);
    await page.waitForFunction(() => window.map?.getCenter?.());

    const flows = [];
    flows.push(await captureFlow(
      page,
      cdp,
      'content-selection',
      ['#contentTableView', '#contentTableView_0', '#pageNavigationView .backbutton', '#editContentView'],
      () => page.click('#contentTableView_0'),
      900,
    ));
    flows.push(await captureFlow(
      page,
      cdp,
      'edit-panel-close',
      ['#contentTableView', '#pageNavigationView .backbutton', '#editContentView'],
      () => page.click('#pageNavigationView .backbutton'),
      500,
    ));
    flows.push(await captureFlow(
      page,
      cdp,
      'map-pan-zoom',
      ['#leftwindow', '#map'],
      () => page.evaluate(() => {
        window.map.panBy(160, 80);
        window.map.setZoom(window.map.getZoom() + 1);
      }),
      1500,
    ));
    await page.click('#contentTableView_0');
    await page.waitForFunction(() => getComputedStyle(document.querySelector('#editContentView')).display !== 'none');
    flows.push(await captureFlow(
      page,
      cdp,
      'translation-panel-populate',
      ['#translateResultsTableView', '#translateResultsTableView .listContainer', '#editContentView'],
      async () => {
        await page.fill('#labelField input', 'CERN');
        await page.fill('#titleField textarea', '世界最大の素粒子物理学研究所');
        await page.fill('#textField textarea', 'この地下にフランスとの国境地帯にまたがり円形に位置するぜん');
        await page.waitForFunction(
          () => document.querySelectorAll('#translateResultsTableView .listContainer > li').length === 11,
          null,
          {timeout: 7000},
        );
      },
      800,
    ));
    flows.push(await captureFlow(
      page,
      cdp,
      'translation-panel-update',
      ['#translateResultsTableView', '#translateResultsTableView .listContainer', '#textField'],
      async () => {
        await page.fill(
          '#textField textarea',
          'この地下にフランスとの国境地帯にまたがり円形に位置する全長27kmの大型ハドロン衝突型加速器が埋め込まれている。',
        );
        await page.waitForFunction(() => (
          document.querySelector('#translateResultsTableView .listContainer')
            ?.textContent.includes('Embedded in this basement is the 27km-long Large Hadron Collider')
        ), null, {timeout: 7000});
      },
      800,
    ));
    flows.push(await captureFlow(
      page,
      cdp,
      'target-user-dropdown',
      ['#targetUserSelectButton', '#targetUserSelectButton .listmenu'],
      async () => {
        await page.click('#targetUserSelectButton .dropdownButtonClickable');
        await page.waitForTimeout(350);
        await page.click('#targetUserSelectButton .listitem[data-value="2"]');
      },
      500,
    ));

    fs.writeFileSync(
      path.join(outputRoot, 'motion_trace.json'),
      `${JSON.stringify({schema: 1, viewport: {width: 1490, height: 856}, flows}, null, 2)}\n`,
    );
    await page.close();
    await context.close();
    const recordedPath = await video.path();
    const finalVideoPath = path.join(outputRoot, 'local_reproduction.webm');
    if (recordedPath !== finalVideoPath) fs.renameSync(recordedPath, finalVideoPath);
  } finally {
    if (browser) await browser.close();
    server.kill('SIGTERM');
  }
}

if (require.main === module) {
  main().catch((error) => {
    console.error(error.stack || error);
    process.exitCode = 1;
  });
}

module.exports = {startScreencast};
