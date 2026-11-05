// Śabdārtha Kaustubha (Sanskrit → Kannada dictionary): lookups over the data built by scripts/build-kosha.mjs.
// No DOM and no module state, so the tests can run it. The app passes in how to load the data:
//   { keys: () => Promise<[[looseKey, headword], …]> (sorted by key), manifest: () => Promise<shards.json>, shard: (file) => Promise<entries[]> }
import { devaToIast } from './translit.js';

export const SOURCE = 'Śabdārtha Kaustubha';
// the fields of a sense, in the order the build writes them: [Sanskrit label, English label]
export const FIELDS = [['पदविभागः', 'Part of speech'], ['कन्नडार्थः', 'Kannada meaning'], ['निष्पत्तिः', 'Formation'], ['व्युत्पत्तिः', 'Derivation'], ['प्रयोगाः', 'Usage'], ['उल्लेखाः', 'Source'], ['विस्तारः', 'More']];

const lower = (keys, k) => { let lo = 0; let hi = keys.length; while (lo < hi) { const mid = (lo + hi) >> 1; if (keys[mid][0] < k) lo = mid + 1; else hi = mid; } return lo; };

/** Headwords whose key is the query (exact) or starts with it (prefix, shortest first). */
export function matchKeys(keys, qk, { prefixLimit = 12 } = {}) {
  const exact = []; const prefix = []; const seen = new Set();
  for (let i = lower(keys, qk); i < keys.length && keys[i][0].startsWith(qk); i++) {
    const [k, h] = keys[i];
    if (seen.has(h)) continue;
    seen.add(h);
    (k === qk ? exact : prefix).push([k, h]);
  }
  prefix.sort((a, b) => a[0].length - b[0].length || (a[1] < b[1] ? -1 : 1));
  return { exact: exact.map((x) => x[1]), prefix: prefix.slice(0, prefixLimit).map((x) => x[1]) };
}

export const koshaHref = (head) => `#/kosha/${encodeURIComponent(head)}`;

/** Search rows for a loose key: whole-key matches, then the headwords that start with it. */
export function koshaRows(keys, qk, { prefixLimit = 12 } = {}) {
  if (qk.length < 2) return [];
  const m = matchKeys(keys, qk, { prefixLimit: qk.length >= 3 ? prefixLimit : 0 });
  const row = (h, score) => ({ group: 'kosha', score, href: koshaHref(h), label: devaToIast(h), hint: `${SOURCE}, Sanskrit–Kannada` });
  return [...m.exact.map((h) => row(h, 1100)), ...m.prefix.map((h, i) => row(h, 500 - Math.min(i, 40)))];
}

/** The shard file that holds a headword: the last one whose first headword is not after it. */
export function shardOf(manifest, head) {
  const s = manifest.shards;
  let lo = 0; let hi = s.length - 1;
  while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (s[mid][0] <= head) lo = mid; else hi = mid - 1; }
  return s[lo]?.[1];
}

/** One entry [headword, variants, senses] by headword, or null. */
export async function lookup(data, head) {
  const file = shardOf(await data.manifest(), head);
  return file ? (await data.shard(file)).find((e) => e[0] === head) || null : null;
}

/** The entries around a headword for browsing: [{ index, entries }] of the shard that holds it, and its neighbours. */
export async function shardAt(data, head) {
  const m = await data.manifest();
  const file = shardOf(m, head);
  const i = m.shards.findIndex((s) => s[1] === file);
  return { i, count: m.shards.length, file, entries: await data.shard(file), first: m.shards[i][0], prev: m.shards[i - 1]?.[0] ?? null, next: m.shards[i + 1]?.[0] ?? null };
}

/** The headwords just before and after a headword (null at either end of the dictionary), across shard boundaries. */
export async function neighbours(data, head) {
  const m = await data.manifest();
  const i = m.shards.findIndex((s) => s[1] === shardOf(m, head));
  const es = await data.shard(m.shards[i][1]);
  const at = es.findIndex((e) => e[0] === head);
  const prev = at > 0 ? es[at - 1][0] : i > 0 ? (await data.shard(m.shards[i - 1][1])).at(-1)[0] : null;
  const next = at >= 0 && at < es.length - 1 ? es[at + 1][0] : i < m.shards.length - 1 ? m.shards[i + 1][0] : null;
  return { prev, next };
}

/** Whole days since 1970 for a date, by its local calendar day (so the word changes at the reader's midnight). */
export const dayNumber = (d = new Date()) => Math.floor(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 86400000);

/** The word of the day: the pool is in a fixed order and the card walks along it one word a day. */
export const wordOfDay = (words, day = dayNumber()) => words[((day % words.length) + words.length) % words.length];

/** Another word at random, never the one shown (rnd is Math.random, or a fixed function in tests). */
export function anotherWord(words, shown, rnd = Math.random) {
  if (words.length < 2) return words[0];
  let w;
  do { w = words[Math.floor(rnd() * words.length)]; } while (w[0] === shown);
  return w;
}
