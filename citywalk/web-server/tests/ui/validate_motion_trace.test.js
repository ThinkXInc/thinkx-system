const test = require('node:test');
const {validateMotionTrace} = require('./validate_motion_trace');

const visible = (overrides = {}) => ({display: 'block', opacity: 1, transform: 'none', ...overrides});
const contract = {
  schema: 1,
  viewport: {width: 1490, height: 856},
  capture_required_flows: ['content-selection', 'edit-panel-close', 'map-pan-zoom'],
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
  ],
};

test('accepts a complete motion trace', () => validateMotionTrace(contract, trace));
