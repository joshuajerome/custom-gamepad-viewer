import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import vm from 'node:vm';

import { bundleModules, collectSources, importsOf } from '../../web/js/bundle.js';
import { DEFAULT_LAYOUT } from '../../web/js/layout.js';
import { parseSettings, toQuery } from '../../web/js/settings.js';
import { buildStandalone, standaloneHtml } from '../../web/js/standalone.js';

const webDir = new URL('../../web/', import.meta.url);
const SITE = 'https://site.test/';
const TYPES = { '.png': 'image/png', '.svg': 'image/svg+xml', '.json': 'application/json' };

// fetch() stand-in serving web/ from disk at https://site.test/
async function diskFetch(url) {
  const path = String(url).replace(SITE, '');
  const file = new URL(path, webDir);
  if (!existsSync(file)) return { ok: false, status: 404 };
  const bytes = readFileSync(file);
  const ext = path.slice(path.lastIndexOf('.'));
  return {
    ok: true,
    status: 200,
    headers: { get: () => TYPES[ext] || 'text/plain' },
    text: async () => bytes.toString('utf8'),
    json: async () => JSON.parse(bytes.toString('utf8')),
    arrayBuffer: async () => bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.length),
  };
}

test('importsOf resolves relative specifiers', () => {
  assert.deepEqual(
    importsOf('js/overlay.js', "import { a } from './layout.js';\nimport {b as c} from '../x/y.js';\n"),
    ['js/layout.js', 'x/y.js'],
  );
});

test('bundleModules orders dependencies and wires imports, aliases and exports', () => {
  const sources = {
    'main.js': "import { greet, Box as B } from './lib.js';\nimport { N } from './n.js';\n"
      + 'globalThis.out = greet(new B(N).v);\n',
    'lib.js': "import { N } from './n.js';\nexport function greet(x) { return `hi ${x + N}`; }\n"
      + 'export class Box { constructor(v) { this.v = v; } }\nexport async function later() {}\n',
    'n.js': 'export const N = 2;\n',
  };
  const script = bundleModules('main.js', sources);
  assert.ok(script.indexOf('// n.js') < script.indexOf('// lib.js'));
  assert.ok(script.indexOf('// lib.js') < script.indexOf('// main.js'));
  const ctx = {};
  vm.runInNewContext(script, ctx);
  assert.equal(ctx.out, 'hi 4');
});

test('bundleModules rejects cycles and missing modules', () => {
  assert.throws(() => bundleModules('a.js', {
    'a.js': "import { b } from './b.js';", 'b.js': "import { a } from './a.js';",
  }), /cycle/);
  assert.throws(() => bundleModules('a.js', { 'a.js': "import { b } from './b.js';" }), /Missing/);
});

test('standaloneHtml escapes closing tags in embedded content', () => {
  const html = standaloneHtml({
    title: 'T<x>', css: 'a{}</style><b>', script: 'let s = "</script>";', config: { q: '</script>' },
  });
  assert.equal((html.match(/<\/script>/g) || []).length, 2); // only the two real closers
  assert.equal((html.match(/<\/style>/g) || []).length, 1);
  assert.ok(html.includes('<title>Tx</title>'));
});

function stubElement() {
  const el = {
    children: [],
    style: { props: {}, setProperty(k, v) { this.props[k] = v; } },
    classList: { set: new Set(), toggle(c, on) { if (on) this.set.add(c); else this.set.delete(c); } },
    dataset: {},
    appendChild(c) { this.children.push(c); return c; },
  };
  return el;
}

test('the bundled overlay runs standalone with baked settings and theme', async () => {
  const sources = await collectSources('js/overlay.js', SITE, diskFetch);
  const script = bundleModules('js/overlay.js', sources);
  assert.doesNotMatch(script, /^\s*(import|export)\s/m);

  const stage = stubElement();
  const frames = [];
  const ctx = {
    CGV_STANDALONE: { query: 'theme=dualsense&p=2', vars: { '--base': 'url("data:x")' } },
    document: {
      head: stubElement(),
      baseURI: SITE,
      getElementById: (id) => (id === 'stage' ? stage : stubElement()),
      createElement: () => stubElement(),
    },
    navigator: { getGamepads: () => [null, null, null, null] },
    location: { search: '?theme=wrong' },
    innerWidth: 903,
    innerHeight: 713,
    addEventListener() {},
    requestAnimationFrame: (fn) => frames.push(fn),
    fetch: () => { throw new Error('standalone must not fetch'); },
    URL,
    URLSearchParams,
  };
  ctx.globalThis = ctx;
  vm.runInNewContext(script, ctx);
  frames.shift()(); // one render tick

  const root = stage.children[0];
  assert.equal(root.style.props['--base'], 'url("data:x")');
  assert.match(root.className, /\bds4\b.*\bdisconnected\b/);
  assert.equal(stage.style.width, '903px');
});

test('buildStandalone inlines PNG theme images as data URIs', async () => {
  const settings = parseSettings('?theme=white&p=3');
  const html = await buildStandalone({
    layout: DEFAULT_LAYOUT, settings, query: toQuery(settings), siteUrl: SITE, fetchFn: diskFetch,
  });
  assert.ok(html.includes('data:image/png;base64,'));
  assert.ok(!html.includes('https://site.test/'), 'no network references remain');
  assert.ok(html.includes('"query":"theme=white&p=3"'));
  assert.ok(html.includes('.controller.ds4'), 'layout CSS inlined');
});

test('buildStandalone bakes recoloured SVGs for colourable themes', async () => {
  const settings = parseSettings('?theme=dualsense&colors=shell:123456');
  const html = await buildStandalone({
    layout: DEFAULT_LAYOUT, settings, query: toQuery(settings), siteUrl: SITE, fetchFn: diskFetch,
  });
  assert.ok(html.includes('data:image/svg+xml'));
  assert.ok(html.includes('%23123456'), 'shell override applied (url-encoded #)');
  assert.ok(!html.includes('https://site.test/'));
});
