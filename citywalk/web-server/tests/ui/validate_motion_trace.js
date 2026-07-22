const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

function flowById(trace, id) {
  const flow = trace.flows.find((candidate) => candidate.id === id);
  assert.ok(flow, `motion trace is missing flow: ${id}`);
  return flow;
}

function validateSamples(flow) {
  assert.ok(flow.samples.length > 1, `${flow.id}: at least two samples are required`);
  let previous = -Infinity;
  for (const sample of flow.samples) {
    assert.ok(Number.isFinite(sample.elapsed_ms), `${flow.id}: elapsed_ms is not finite`);
    assert.ok(sample.elapsed_ms > previous, `${flow.id}: timestamps are not strictly increasing`);
    previous = sample.elapsed_ms;
  }
}

function validateMotionTrace(contract, trace) {
  assert.equal(trace.schema, 1);
  assert.deepEqual(trace.viewport, contract.viewport);
  for (const id of contract.capture_required_flows) validateSamples(flowById(trace, id));

  const selection = flowById(trace, 'content-selection').samples;
  const selectedCell = selection.map((sample) => sample.elements['#contentTableView_0']).filter(Boolean);
  assert.ok(selectedCell.length > 1, 'content-selection: selected cell was not sampled');
  assert.ok(
    selectedCell.some((sample) => sample.opacity < selectedCell[0].opacity || sample.transform !== selectedCell[0].transform),
    'content-selection: selected cell has no visible trajectory',
  );
  assert.equal(selection.at(-1).elements['#contentTableView'].display, 'none');
  assert.notEqual(selection.at(-1).elements['#editContentView'].display, 'none');

  const close = flowById(trace, 'edit-panel-close').samples;
  assert.notEqual(close[0].elements['#editContentView'].display, 'none');
  assert.equal(close.at(-1).elements['#editContentView'].display, 'none');
  assert.notEqual(close.at(-1).elements['#contentTableView'].display, 'none');

  const map = flowById(trace, 'map-pan-zoom').samples.map((sample) => sample.map).filter(Boolean);
  assert.ok(map.length > 1, 'map-pan-zoom: map state was not sampled');
  assert.equal(map.at(-1).zoom - map[0].zoom, 1, 'map-pan-zoom: zoom delta differs');
  assert.notDeepEqual(map.at(-1).center, map[0].center, 'map-pan-zoom: center did not change');

  const population = flowById(trace, 'translation-panel-populate').samples;
  assert.ok(
    population.some((sample) => sample.translation?.count < 11),
    'translation-panel-populate: no pre-completion state was sampled',
  );
  assert.equal(population.at(-1).translation?.count, 11);
  assert.notEqual(population.at(-1).elements['#translateResultsTableView'].display, 'none');

  const update = flowById(trace, 'translation-panel-update').samples;
  assert.equal(update[0].translation?.count, 11);
  assert.equal(update.at(-1).translation?.count, 11);
  assert.ok(
    update.at(-1).elements['#translateResultsTableView'].text.includes('27km-long Large Hadron Collider'),
    'translation-panel-update: completed long-form translation is missing',
  );

  const dropdown = flowById(trace, 'target-user-dropdown').samples;
  assert.ok(
    dropdown.some((sample) => sample.elements['#targetUserSelectButton .listmenu']?.display !== 'none'),
    'target-user-dropdown: open menu state was not sampled',
  );
  assert.equal(dropdown.at(-1).elements['#targetUserSelectButton .listmenu'].display, 'none');
  assert.match(dropdown.at(-1).elements['#targetUserSelectButton'].text, /高リテラシー/);
}

function main() {
  const citywalkRoot = path.resolve(__dirname, '../../..');
  const goldenRoot = path.join(citywalkRoot, 'web-server/tests/golden/ui_legacy');
  const contract = JSON.parse(fs.readFileSync(path.join(goldenRoot, 'motion_contract.json')));
  const tracePath = process.argv[2] || path.join(goldenRoot, 'motion/motion_trace.json');
  const trace = JSON.parse(fs.readFileSync(tracePath));
  validateMotionTrace(contract, trace);
  console.log(`${tracePath}: motion trace OK`);
}

if (require.main === module) main();

module.exports = {validateMotionTrace};
