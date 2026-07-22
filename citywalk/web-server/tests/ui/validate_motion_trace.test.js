const test = require('node:test');
const {validateMotionTrace} = require('./validate_motion_trace');

const visible = (overrides = {}) => ({display: 'block', opacity: 1, transform: 'none', ...overrides});
const contract = {
  schema: 1,
  viewport: {width: 1490, height: 856},
  capture_required_flows: [
    'content-selection',
    'edit-panel-close',
    'map-pan-zoom',
    'translation-panel-populate',
    'translation-panel-update',
    'target-user-dropdown',
  ],
};
const trace = {
  schema: 1,
  viewport: {width: 1490, height: 856},
  flows: [
    {id: 'content-selection', samples: [
      {elapsed_ms: 1, elements: {'#contentTableView': visible(), '#contentTableView_0': visible(), '#editContentView': visible({display: 'none'})}},
      {elapsed_ms: 17, elements: {'#contentTableView': visible({display: 'none'}), '#contentTableView_0': visible({opacity: 0, transform: 'matrix(1, 0, 0, 1, -20, 0)'}), '#editContentView': visible()}},
    ]},
    {id: 'edit-panel-close', samples: [
      {elapsed_ms: 1, elements: {'#contentTableView': visible({display: 'none'}), '#editContentView': visible()}},
      {elapsed_ms: 17, elements: {'#contentTableView': visible(), '#editContentView': visible({display: 'none', opacity: 0})}},
    ]},
    {id: 'map-pan-zoom', samples: [
      {elapsed_ms: 1, elements: {}, map: {center: {lat: 46.9, lng: 7.4}, zoom: 14}},
      {elapsed_ms: 17, elements: {}, map: {center: {lat: 46.8, lng: 7.5}, zoom: 15}},
    ]},
    {id: 'translation-panel-populate', samples: [
      {elapsed_ms: 1, elements: {'#translateResultsTableView': visible()}, translation: {count: 0, scroll_top: 0}},
      {elapsed_ms: 17, elements: {'#translateResultsTableView': visible()}, translation: {count: 11, scroll_top: 0}},
    ]},
    {id: 'translation-panel-update', samples: [
      {elapsed_ms: 1, elements: {'#translateResultsTableView': visible({text: 'short'})}, translation: {count: 11}},
      {elapsed_ms: 17, elements: {'#translateResultsTableView': visible({text: 'Embedded in this basement is the 27km-long Large Hadron Collider'})}, translation: {count: 11}},
    ]},
    {id: 'target-user-dropdown', samples: [
      {elapsed_ms: 1, elements: {'#targetUserSelectButton': visible({text: '対象ユーザー'}), '#targetUserSelectButton .listmenu': visible()}},
      {elapsed_ms: 17, elements: {'#targetUserSelectButton': visible({text: '高リテラシー'}), '#targetUserSelectButton .listmenu': visible({display: 'none'})}},
    ]},
  ],
};

test('accepts a complete motion trace', () => validateMotionTrace(contract, trace));
