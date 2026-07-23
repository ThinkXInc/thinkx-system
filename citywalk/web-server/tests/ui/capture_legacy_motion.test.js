// thinkx-system/citywalk/web-server/tests/ui/capture_legacy_motion.test.js
//
// Regression test for distinct PNG frames emitted by the Chrome CDP screencast.

const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const {chromium} = require('playwright-core');

const buildRoot = path.resolve(__dirname, '../.build');
fs.mkdirSync(buildRoot, {recursive: true});
const outputRoot = fs.mkdtempSync(path.join(buildRoot, 'motion-screencast-'));
process.env.CITYWALK_MOTION_OUTPUT = outputRoot;
const {startScreencast} = require('./capture_legacy_motion');
const chromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

test('captures animated Chrome frames as PNG', async (context) => {
  let browser;
  let browserContext;
  context.after(async () => {
    if (browserContext) await browserContext.close();
    if (browser) await browser.close();
    fs.rmSync(outputRoot, {recursive: true, force: true});
  });
  await assert.rejects(startScreencast({}, '../outside'), /invalid flow ID/);
  browser = await chromium.launch({executablePath: chromePath, headless: true});
  browserContext = await browser.newContext({viewport: {width: 320, height: 240}});
  const page = await browserContext.newPage();
  await page.setContent('<div id="target" style="width:40px;height:40px;background:#000"></div>');
  const cdp = await browserContext.newCDPSession(page);
  const finish = await startScreencast(cdp, 'smoke');
  await page.evaluate(async () => {
    const animation = document.querySelector('#target').animate(
      [{transform: 'translateX(0px)'}, {transform: 'translateX(200px)'}],
      {duration: 500, fill: 'forwards'},
    );
    await animation.finished;
  });
  const frames = await finish();
  assert.ok(frames.length > 1);
  const frameHashes = new Set();
  for (const frame of frames) {
    const bytes = fs.readFileSync(path.join(outputRoot, 'smoke', frame.filename));
    assert.deepEqual([...bytes.subarray(0, 8)], [137, 80, 78, 71, 13, 10, 26, 10]);
    frameHashes.add(crypto.createHash('sha256').update(bytes).digest('hex'));
  }
  assert.ok(frameHashes.size > 1, 'screencast contains no visible frame change');
  const concat = fs.readFileSync(path.join(outputRoot, 'smoke', 'frames.ffconcat'), 'utf8');
  assert.match(concat, /^ffconcat version 1\.0\n/);
  assert.equal((concat.match(/^duration /gm) || []).length, frames.length);
  assert.equal((concat.match(/^file /gm) || []).length, frames.length + 1);
});
