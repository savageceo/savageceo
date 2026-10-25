#!/usr/bin/env node
/**
 * build-profile.mjs — render a SAVAGE house GitHub profile from data + template.
 *
 *   node scripts/build-profile.mjs           # rebuild the profile README
 *   node scripts/build-profile.mjs --ping    # also probe each domain's liveness
 *   node scripts/build-profile.mjs --check   # exit 1 if the README is stale (CI guard)
 *
 * Source of truth: data/profile.json + data/properties.json + templates/profile.tpl.md.
 * kind "user" writes README.md (personal profile repo), kind "org" writes
 * profile/README.md (org .github repo). Never edit the README by hand.
 */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => readFileSync(join(ROOT, p), 'utf8');
const json = (p) => JSON.parse(read(p));

const profile = json('data/profile.json');
const props = json('data/properties.json');
const template = read('templates/profile.tpl.md');

const PING = process.argv.includes('--ping');
const CHECK = process.argv.includes('--check');

const isOrg = profile.kind === 'org';
const A = isOrg ? '../assets/' : 'assets/';
const TARGET = isOrg ? 'profile/README.md' : 'README.md';

/* ── the duo: THE ARCHITECT + ONYX, equal-height portraits, names above ── */
function renderDuo(duo) {
  const cell = (p) => [
    `    <td align="center" width="430" valign="top">`,
    `      <img src="${A}${p.nameSvg}" height="34" alt="${p.name}" /><br/>`,
    `      <img src="${A}${p.img}" height="392" alt="${p.alt}" /><br/>`,
    `      <sub>${p.caption}</sub>`,
    `    </td>`,
  ].join('\n');
  return ['<table>', '  <tr>', duo.map(cell).join('\n'), '  </tr>', '</table>'].join('\n');
}

/* ── the roster table, driven entirely by properties.json ── */
function renderProperties(items, statuses, lastCol) {
  const head =
    `| Property | Type | Live at | Status | ${lastCol} |\n` +
    '|:--|:--|:--|:--:|:--:|';
  const rows = items.map((it) => {
    const s = statuses[it.status] ?? { dot: '⚪', label: it.status };
    const live = it.url ? `[${it.domain} ↗](${it.url})` : it.domain ?? '—';
    const src = !it.src ? '—' : it.src.url ? `[${it.src.label}](${it.src.url})` : `\`${it.src.label}\``;
    return `| **${it.name}** | ${it.tag} | ${live} | ${s.dot} ${s.label} | ${src} |`;
  });
  return [head, ...rows].join('\n');
}

/* ── the legend lists only the statuses this board actually uses ── */
function renderLegend(items, statuses) {
  const used = Object.keys(statuses).filter((k) => items.some((it) => it.status === k));
  const dots = used.map((k) => `${statuses[k].dot} ${statuses[k].label}`).join('&nbsp;&nbsp;·&nbsp;&nbsp;');
  return `${dots}&nbsp;&nbsp;—&nbsp;&nbsp;names link to the live site.`;
}

/* ── the law: a clean centered ascii plaque ── */
function renderLaw(lines) {
  const w = Math.max(...lines.map((l) => l.length)) + 6;
  const pad = (l) => {
    const total = w - l.length;
    const left = Math.floor(total / 2);
    return ' '.repeat(left) + l + ' '.repeat(total - left);
  };
  const top = '╔' + '═'.repeat(w) + '╗';
  const bot = '╚' + '═'.repeat(w) + '╝';
  const body = lines.map((l) => '║' + pad(l) + '║').join('\n');
  return '```text\n' + [top, body, bot].join('\n') + '\n```';
}

/* ── the house: one line that walks every SAVAGE org ── */
function renderHouse(house, login) {
  return house
    .map((h) => (h.login === login ? `<b>${h.name}</b>` : `<a href="https://github.com/${h.login}">${h.name}</a>`))
    .join('&nbsp;&nbsp;·&nbsp;&nbsp;');
}

/* ── optional: probe liveness so the board can self-heal ── */
async function pingStatuses(items) {
  await Promise.all(
    items.map(async (it) => {
      if (!it.url) return;
      try {
        const ctl = new AbortController();
        const t = setTimeout(() => ctl.abort(), 7000);
        const res = await fetch(it.url, { method: 'GET', redirect: 'follow', signal: ctl.signal });
        clearTimeout(t);
        if (!res.ok && it.status === 'live') it.status = 'soon'; // demote, never crash
      } catch {
        if (it.status === 'live') it.status = 'soon';
      }
    })
  );
}

// shields.io escapes literal text: '-' -> '--', '_' -> '__', ' ' -> '_'
const shield = (s) => s.replace(/-/g, '--').replace(/_/g, '__').replace(/ /g, '_');
const badgeUrl =
  `https://img.shields.io/badge/${shield(profile.signature)}-${shield(profile.login)}` +
  `-0a0a0a?style=for-the-badge&labelColor=0a0a0a&color=c9a962`;

const out = {
  '{{a}}': A,
  '{{hero}}': profile.hero,
  '{{brand}}': profile.brand,
  '{{tagline}}': profile.tagline,
  '{{blurb}}': profile.blurb,
  '{{rosterTitle}}': profile.rosterTitle,
  '{{footer}}': profile.footer,
  '{{signature}}': profile.signature,
  '{{badgeUrl}}': badgeUrl,
  '{{badgeAlt}}': `${profile.signature} / ${profile.login}`,
  '{{login}}': profile.login,
};

const main = async () => {
  if (PING) await pingStatuses(props.items);

  let md = template;
  md = md.replace('{{duo}}', renderDuo(profile.duo));
  md = md.replace('{{properties}}', renderProperties(props.items, props.statuses, profile.lastCol));
  md = md.replace('{{legend}}', renderLegend(props.items, props.statuses));
  md = md.replace('{{law}}', renderLaw(profile.law));
  md = md.replace('{{house}}', renderHouse(profile.house, profile.login));
  for (const [k, v] of Object.entries(out)) md = md.replaceAll(k, v);

  const target = join(ROOT, TARGET);
  const current = (() => { try { return readFileSync(target, 'utf8'); } catch { return null; } })();

  if (CHECK) {
    if (current !== md) {
      console.error(`✘ ${TARGET} is stale — run: node scripts/build-profile.mjs`);
      process.exit(1);
    }
    console.log(`✓ ${TARGET} is up to date`);
    return;
  }

  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, md);
  console.log(`✓ wrote ${TARGET} — ${props.items.length} properties, ${profile.duo.length} principals${PING ? ' (pinged)' : ''}`);
};

main().catch((e) => { console.error(e); process.exit(1); });
