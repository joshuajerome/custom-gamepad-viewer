/* Tiny ES-module bundler for the standalone (offline) overlay.

file:// pages can't load ES modules or fetch(), so the builder inlines the
overlay's module graph into one classic script. This handles exactly the
module syntax this codebase uses:

  import { a, b as c } from './x.js';
  export function f() {}   export async function f() {}
  export const X = ...;    export class C {}

Each module becomes an IIFE that receives its imports and returns its exports,
emitted in dependency order. Pure string transforms; no DOM.
*/

const IMPORT_RE = /^\s*import\s*\{([^}]*)\}\s*from\s*['"]([^'"]+)['"];?[ \t]*\r?\n?/gm;
const EXPORT_RE = /^(\s*)export\s+(async\s+function|function|const|let|class)\s+([A-Za-z_$][\w$]*)/gm;

function resolve(from, spec) {
  if (!spec.startsWith('.')) throw new Error(`Only relative imports are supported: ${spec}`);
  const parts = from.split('/').slice(0, -1);
  for (const seg of spec.split('/')) {
    if (seg === '..') parts.pop();
    else if (seg !== '.') parts.push(seg);
  }
  return parts.join('/');
}

/** Relative module paths imported by `source` (resolved against `path`). */
export function importsOf(path, source) {
  return [...source.matchAll(IMPORT_RE)].map((m) => resolve(path, m[2]));
}

function transform(path, source, ids) {
  const bindings = [];
  let body = source.replace(IMPORT_RE, (_, names, spec) => {
    const dep = resolve(path, spec);
    const list = names.split(',').map((n) => n.trim()).filter(Boolean)
      .map((n) => n.replace(/\s+as\s+/, ': '));
    bindings.push(`const { ${list.join(', ')} } = ${ids.get(dep)};`);
    return '';
  });
  const exported = [];
  body = body.replace(EXPORT_RE, (_, indent, kind, name) => {
    exported.push(name);
    return `${indent}${kind} ${name}`;
  });
  if (/^\s*export\b/m.test(body)) throw new Error(`Unsupported export syntax in ${path}`);
  return `const ${ids.get(path)} = (() => {\n${bindings.join('\n')}\n${body}\n`
    + `return { ${exported.join(', ')} };\n})(); // ${path}\n`;
}

/**
 * Bundle `entry` and its imports. `sources` maps module path -> source text and
 * must contain the whole graph (see importsOf). Returns one classic script.
 */
export function bundleModules(entry, sources) {
  const order = [];
  const state = new Map(); // path -> 'visiting' | 'done'
  const visit = (path) => {
    if (state.get(path) === 'done') return;
    if (state.get(path) === 'visiting') throw new Error(`Import cycle at ${path}`);
    if (!(path in sources)) throw new Error(`Missing module source: ${path}`);
    state.set(path, 'visiting');
    for (const dep of importsOf(path, sources[path])) visit(dep);
    state.set(path, 'done');
    order.push(path);
  };
  visit(entry);

  const ids = new Map(order.map((p, i) => [p, `__cgv_m${i}`]));
  return `(() => {\n'use strict';\n${order.map((p) => transform(p, sources[p], ids)).join('\n')}})();\n`;
}

/** Fetch a module graph starting at `entry` (paths relative to `baseUrl`). */
export async function collectSources(entry, baseUrl, fetchFn = fetch) {
  const sources = {};
  const pending = [entry];
  while (pending.length) {
    const path = pending.pop();
    if (path in sources) continue;
    const res = await fetchFn(new URL(path, baseUrl), { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
    sources[path] = await res.text();
    pending.push(...importsOf(path, sources[path]));
  }
  return sources;
}
