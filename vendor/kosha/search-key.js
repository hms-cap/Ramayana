// Search keys: fold Kannada, Devanagari, IAST and plain-English spellings to the same string.
//
// One module for the browser and the build scripts, so an indexed line and a typed query are
// folded by exactly the same rules. No DOM, no Node-only APIs.
//
//   toDeva(s)      Kannada → Devanagari (everything else is left as it is)
//   toIast(s)      any script → lower-case IAST, pitch accents and svara marks dropped
//   strictKey(s)   IAST letters only, diacritics kept:        agnimīḷe
//   looseKey(s)    phonetic skeleton, a-z only:               agnimile
//
// strictKey is for exact and prefix hits. looseKey is for everything typed without diacritics.

import { devaToIast, isoToIast, stripRomanAccents } from './translit.js';

const KANNADA = /[ಀ-೿]/;
const INDIC = /[ऀ-ॿ᳐-᳿꣠-ꣿ]/;
const JOINERS = /[̐‌‍]/g; // candrabindu mark, ZWNJ, ZWJ

/** Kannada → Devanagari: letters, signs and digits sit at a fixed offset (U+0C80 ↔ U+0900). */
export function toDeva(s) {
  const t = String(s)
    // Kannada Vedic books write the Devanagari ꣳ / ꣵ ("gum") as ಗ್ಂ / ಗ್ಗ್ಂ; both are anusvāra here
    .replace(/ಗ್ಗ್ಂ|ಗ್ಂ/g, 'ं')
    .replace(/ೱ/g, 'ᳵ') // jihvāmūlīya
    .replace(/ೲ/g, 'ᳶ') // upadhmānīya
    .replace(/ೞ/g, 'ಳ'); // archaic ೞ is read as ಳ (ḷ) in Vedic text
  let out = '';
  for (const ch of t) {
    const c = ch.codePointAt(0);
    const inBlock = (c >= 0x0C81 && c <= 0x0CCD) || (c >= 0x0CE0 && c <= 0x0CE3) || (c >= 0x0CE6 && c <= 0x0CEF);
    out += inBlock ? String.fromCodePoint(c - 0x380) : ch;
  }
  // short ऎ / ऒ have no place in Sanskrit; treat them as ए / ओ
  return out.replace(/ऎ/g, 'ए').replace(/ऒ/g, 'ओ');
}

/** Any script → lower-case IAST. Latin input only has accents and ISO-15919 marks normalised. */
export function toIast(s) {
  let t = String(s).normalize('NFC');
  if (KANNADA.test(t)) t = toDeva(t);
  // devaToIast drops U+1CEA as a svara mark before its own ᳪ → ṃ rule can run; ꣵ is dropped too.
  // For search all three "gum" signs are an ordinary anusvāra, which is what the Kannada path gives.
  t = INDIC.test(t) ? devaToIast(t.replace(/[\u1CEA\uA8F3\uA8F5]/g, '\u0902')) : stripRomanAccents(isoToIast(t));
  return t.normalize('NFC').toLowerCase();
}

/** IAST letters only (diacritics kept), no spaces, digits or punctuation. */
export function strictKey(s) {
  return toIast(s).replace(JOINERS, '').normalize('NFC').replace(/[^\p{L}\p{M}]/gu, '');
}

const collapse = (w) => w.replace(/(.)\1+/g, '$1'); // tt → t, aa → a, ii → i

// Rules that do not depend on word breaks run on the joined string, so "bhir īḍyo" (IAST) and
// "bhirīḍyo" (Devanagari, sandhi joined) fold alike. Only a typed final h needs the break.
function foldJoined(k) {
  return collapse(
    k
      .replace(/sh+/g, 's') // ś ṣ were already s; typed sh → s
      .replace(/([kgcjtdpb])h+/g, '$1') // aspirates fold: kh gh ch jh th dh ph bh → k g c j t d p b
      .replace(/ee/g, 'i').replace(/oo/g, 'u') // typed long ī, ū
      .replace(/ri/g, 'r') // ṛ and typed "ri" are the same sound
      .replace(/w/g, 'v').replace(/z/g, 's').replace(/x/g, 'ks')
      .replace(/gy/g, 'jn')
      .replace(/nts/g, 'ns') // traditional text has the extra t of mahāntsupāraḥ; IAST editions write mahān supāraḥ
      .replace(/m(?=[^aeiou])/g, 'n'), // m before a consonant is n; before collapsing, so "indram mahó" = "indraṃ mahó"
  );
}

/**
 * Phonetic skeleton for lenient matching, a–z only:
 *   - script, svara marks, accents and word breaks ignored
 *   - long vowels → short; ṛ ri → r; ḷ ḻ → l; ś ṣ sh → s; ṭ ḍ ṇ → t d n
 *   - aspirates fold (kh th bh → k t b); doubled letters collapse (taittirīya = taitiriya)
 *   - anusvāra, ṅ ñ ṇ → n; m before a consonant → n; the extra t of -ntsu- dropped
 *   - visarga dropped; a final m or n is dropped (suktam = sukta), unless { keepFinal: true } (used to
 *     measure where a word ends inside a longer key)
 */
export function looseKey(s, { keepFinal = false } = {}) {
  const t = toIast(s)
    .replace(JOINERS, '')
    .replace(/ḥ/g, '') // ḥ: visarga
    .replace(/[ṃṁ]/g, 'n') // ṃ ṁ: anusvāra
    .normalize('NFD').replace(/[̀-ͯ]/g, ''); // every other diacritic: ā → a, ṣ → s, ṭ → t …
  const words = t.split(/[^a-z]+/).filter(Boolean).map((w) => w.replace(/([aeiou])h$/, '$1')); // typed visarga: agnih → agni
  const k = foldJoined(words.join(''));
  return keepFinal ? k : k.replace(/[mn]$/, '');
}
