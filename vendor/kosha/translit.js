// Minimal Devanagari <-> IAST transliteration for Vedic names and text.
// Svara marks (udātta/anudātta/svarita) are dropped when going to IAST.

const VOWELS = [
  ['ai', 'ऐ', 'ै'], ['au', 'औ', 'ौ'], ['ā', 'आ', 'ा'], ['ī', 'ई', 'ी'], ['ū', 'ऊ', 'ू'],
  ['ṝ', 'ॠ', 'ॄ'], ['ṛ', 'ऋ', 'ृ'], ['ḹ', 'ॡ', 'ॣ'], ['ḷ', 'ऌ', 'ॢ'],
  ['a', 'अ', ''], ['i', 'इ', 'ि'], ['u', 'उ', 'ु'], ['e', 'ए', 'े'], ['o', 'ओ', 'ो'],
];
const CONSONANTS = [
  ['kh', 'ख'], ['gh', 'घ'], ['ch', 'छ'], ['jh', 'झ'], ['ṭh', 'ठ'], ['ḍh', 'ढ'], ['ḷh', 'ळ्ह'],
  ['th', 'थ'], ['dh', 'ध'], ['ph', 'फ'], ['bh', 'भ'],
  ['k', 'क'], ['g', 'ग'], ['ṅ', 'ङ'], ['c', 'च'], ['j', 'ज'], ['ñ', 'ञ'],
  ['ṭ', 'ट'], ['ḍ', 'ड'], ['ṇ', 'ण'], ['t', 'त'], ['d', 'द'], ['n', 'न'],
  ['p', 'प'], ['b', 'ब'], ['m', 'म'], ['y', 'य'], ['r', 'र'], ['l', 'ल'], ['v', 'व'],
  ['ś', 'श'], ['ṣ', 'ष'], ['s', 'स'], ['h', 'ह'], ['ḻ', 'ळ'],
];
const VIRAMA = '्';
const DIGITS = '०१२३४५६७८९';

const SVARA = /[॒॑᳚᳐-᳿꣠-ꣿ॓॔]/g;

/** Normalise ISO-15919 / accented IAST to plain IAST. */
export function isoToIast(s) {
  return s.normalize('NFD')
    .replace(/r̥̄/g, 'ṝ').replace(/r̥/g, 'ṛ')
    .replace(/l̥̄/g, 'ḹ').replace(/l̥/g, 'ḷ')
    .replace(/ṁ/g, 'ṃ')
    .normalize('NFC');
}

/** Strip pitch accents (acute/grave) from romanised text. */
export function stripRomanAccents(s) {
  // Only drop acute/grave sitting on a vowel (ś = s + U+0301 must survive).
  return s.normalize('NFD')
    .replace(/([aeiouAEIOU]|[rlRL][̣̥])([̣̥̄]*)[̀́]/g, '$1$2')
    .normalize('NFC');
}

export function iastToDeva(input) {
  // m̐ (anunāsika) becomes candrabindu; mark it before the letter loop
  const s = stripRomanAccents(isoToIast(input)).toLowerCase().replace(/m?\u0310/g, '\u0001');
  let out = '';
  let i = 0;
  let pendingConsonant = false;
  const match = (list) => list.find(([r]) => s.startsWith(r, i));
  while (i < s.length) {
    // ḷ is the Vedic consonant ळ (īḷe), except right after a consonant (kḷp-), where it is the vowel ऌ
    if (s[i] === 'ḷ' && !s.startsWith('ḷh', i) && !pendingConsonant) {
      out += 'ळ'; pendingConsonant = true; i += 1; continue;
    }
    // GRETIL marks vowel hiatus with a diaeresis: praüga = pra-uga
    if (s[i] === 'ü' || s[i] === 'ï') {
      if (pendingConsonant) { out += VIRAMA; pendingConsonant = false; }
      out += s[i] === 'ü' ? 'उ' : 'इ'; i += 1; continue;
    }
    if (s[i] === '\u0001') {
      if (pendingConsonant) { out += VIRAMA; pendingConsonant = false; }
      out += 'ँ'; i += 1; continue;
    }
    const c = match(CONSONANTS);
    if (c) {
      if (pendingConsonant) out += VIRAMA;
      out += c[1];
      pendingConsonant = true;
      i += c[0].length;
      continue;
    }
    const v = match(VOWELS);
    if (v) {
      out += pendingConsonant ? v[2] : v[1];
      pendingConsonant = false;
      i += v[0].length;
      continue;
    }
    if (pendingConsonant) { out += VIRAMA; pendingConsonant = false; }
    const ch = s[i];
    if (ch === 'ṃ' || ch === 'ṁ') out += 'ं';
    else if (ch === 'ḥ') out += 'ः';
    else if (ch === "'" || ch === '’') out += 'ऽ';
    else if (ch >= '0' && ch <= '9') out += DIGITS[+ch];
    else out += ch;
    i += 1;
  }
  if (pendingConsonant) out += VIRAMA;
  return out;
}

const D_VOWEL = Object.fromEntries(VOWELS.map(([r, ind]) => [ind, r]));
const D_SIGN = Object.fromEntries(VOWELS.filter(([, , m]) => m).map(([r, , m]) => [m, r]));
D_SIGN['ॆ'] = 'e'; D_SIGN['ॊ'] = 'o'; // short e/o signs, as written in some South Indian sources
const D_CONS = Object.fromEntries(CONSONANTS.filter(([, d]) => d.length === 1).map(([r, d]) => [d, r]));
D_CONS['ळ'] = 'ḷ';
D_CONS['ऱ'] = 'r'; // Taittirīya ṟ before ś/ṣ is read as r

export function devaToIast(input) {
  const s = input.normalize('NFC')
    .replace(/[ᳵᳶ]/g, 'ः').replace(/ꣳ/g, 'ं') // jihvāmūlīya/upadhmānīya, Vedic anusvāra
    .replace(SVARA, '');
  let out = '';
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    const next = s[i + 1];
    if (D_CONS[ch]) {
      out += D_CONS[ch];
      if (next === VIRAMA) { i++; continue; }
      if (next === '़') { i++; }
      const n2 = s[i + 1];
      if (D_SIGN[n2] !== undefined) { out += D_SIGN[n2]; i++; } else out += 'a';
      continue;
    }
    if (D_VOWEL[ch]) { out += D_VOWEL[ch]; continue; }
    if (ch === 'ॐ') { out += 'oṃ'; continue; }
    if (ch === '॰') { out += '.'; continue; }
    if (ch === VIRAMA) continue;                         // stray virama with no consonant
    if (D_SIGN[ch] !== undefined) { out += D_SIGN[ch]; continue; } // stray vowel sign
    if (ch === 'ं' || ch === 'ᳪ') { out += 'ṃ'; continue; }
    if (ch === 'ँ') { out += 'm̐'; continue; }
    if (ch === 'ः') { out += 'ḥ'; continue; }
    if (ch === 'ऽ') { out += "'"; continue; }
    if (ch === '।') { out += '|'; continue; }
    if (ch === '॥') { out += '||'; continue; }
    const d = DIGITS.indexOf(ch);
    if (d >= 0) { out += String(d); continue; }
    out += ch;
  }
  return out;
}

/** Fold a name to a cross-Saṃhitā key: agniḥ, Agni, अग्निः -> "agni". */
export function nameKey(iast) {
  return stripRomanAccents(isoToIast(iast)).toLowerCase()
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z ]/g, ' ').trim().split(/\s+/)
    .map((w) => w.replace(/h$/, '')).join('-');
}
