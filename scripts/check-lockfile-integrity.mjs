#!/usr/bin/env node
// Fails if any package-lock.json entry is missing its `resolved` URL or
// `integrity` hash.
//
// Why this exists: `npm ci` does NOT fail on a lockfile with no integrity
// hashes — it installs happily and silently skips tarball verification. That
// is how merge c356ff4 stripped all 153 hashes without anything noticing.
// This check is the part `npm ci` cannot do for us.

import { readFileSync } from 'node:fs';

const lockPath = process.argv[2] ?? 'package-lock.json';
const lock = JSON.parse(readFileSync(lockPath, 'utf8'));

if (lock.lockfileVersion < 2) {
  console.error(`✖ ${lockPath}: lockfileVersion ${lock.lockfileVersion} has no "packages" map; expected >= 2.`);
  process.exit(1);
}

const missing = [];

for (const [path, entry] of Object.entries(lock.packages ?? {})) {
  // The root project itself, workspace links and on-disk `file:` deps are
  // never fetched from a registry, so they legitimately carry no hash.
  if (path === '') continue;
  if (entry.link) continue;
  if (entry.resolved?.startsWith('file:')) continue;

  const lacks = [];
  if (!entry.resolved) lacks.push('resolved');
  if (!entry.integrity) lacks.push('integrity');
  if (lacks.length) missing.push(`${path}@${entry.version ?? '?'} — missing ${lacks.join(' + ')}`);
}

const checked = Object.keys(lock.packages ?? {}).length - 1;

if (missing.length) {
  console.error(`✖ ${lockPath}: ${missing.length} of ${checked} entries lack registry integrity metadata.\n`);
  for (const line of missing.slice(0, 20)) console.error(`    ${line}`);
  if (missing.length > 20) console.error(`    ... and ${missing.length - 20} more`);
  console.error(`
  Supply-chain tamper detection is off for these packages.

  This usually means the lockfile was regenerated against an existing
  node_modules, so npm rebuilt the tree from disk without contacting the
  registry. Regenerate it properly:

      rm -rf node_modules
      npm install --package-lock-only
`);
  process.exit(1);
}

console.log(`✔ ${lockPath}: all ${checked} entries carry resolved + integrity.`);
