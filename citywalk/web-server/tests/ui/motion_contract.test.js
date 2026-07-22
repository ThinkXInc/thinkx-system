const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const citywalkRoot = path.resolve(__dirname, '../../..');
const legacyViewRoot = path.join(
  citywalkRoot,
  'legacy/www/server/application/views',
);
const contractPath = path.join(
  citywalkRoot,
  'web-server/tests/golden/ui_legacy/motion_contract.json',
);

function source(relativePath) {
  return fs.readFileSync(path.join(legacyViewRoot, relativePath), 'utf8');
}

test('legacy motion contract remains tied to original implementation', () => {
  const contract = JSON.parse(fs.readFileSync(contractPath, 'utf8'));
  assert.equal(contract.schema, 1);

  const contentTable = source('src/ECMA/business/view_components/content_table_view.js');
  assert.match(contentTable, /const interval = 50;/);
  assert.match(contentTable, /cell\.__index__\*interval/);
  assert.match(contentTable, /interval\*this\._cells\.length/);

  const editContent = source('src/ECMA/business/view_components/edit_content_view.js');
  assert.match(editContent, /const interval = 100;/);
  assert.match(editContent, /opacity: 0/);
  assert.match(editContent, /EditContentViewState\.onclosecomplete/);

  const translation = source('src/ECMA/business/view_components/translate_results_table_view.js');
  assert.match(translation, /const interval = 50;/);
  assert.match(translation, /cell\.__index__\*interval/);
  assert.match(translation, /interval\*this\._cells\.length/);

  const mixin = source('src/less/mixin.less');
  assert.match(mixin, /\.fadeOutToLeft\s*\{/);
  assert.match(mixin, /animation-duration: 0\.4s;/);
  assert.match(mixin, /transform: translateX\(-20px\);/);

  const createGuide = source('src/less/business/createguide.less');
  assert.match(createGuide, /\.fadeInToBottom\(0\.4s, 0s, 1\);/);

  const translationHelper = source('src/ECMA/business/helpers/translate.js');
  assert.doesNotMatch(translationHelper, /api-free\.deepl\.com|auth_key|fetch\s*\(/);
  assert.match(translationHelper, /Legacy external translation integration was removed/);
  assert.match(translationHelper, /onfailed\(error\)/);
});
