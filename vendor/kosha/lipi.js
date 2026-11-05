// Devanagari → Kannada for Vedic text.
//
// The two scripts share the ISCII layout, so letters, vowel signs, virama,
// anusvāra, visarga, avagraha and digits map by a fixed offset (U+0900 →
// U+0C80). Svara marks (U+0951 udātta/svarita, U+0952 anudātta, U+1CDA
// double svarita) and the dandas are shared by both scripts and pass through.
//
// Vedic signs that the Kannada fonts lack are written the way Kannada
// Vedic books write them:
//   ꣳ / ᳪ  anusvāra before ś ṣ s h r, read "gum"      → ಗ್ಂ
//   ꣵ      the doubled form after a short vowel ("ggum") → ಗ್ಗ್ಂ
//   ᳵ      jihvāmūlīya (before k, kh)                  → ೱ  (U+0CF1)
//   ᳶ      upadhmānīya (before p, ph)                  → ೲ  (U+0CF2)
//   ॐ                                                  → ಓಂ
//   ॰      abbreviation mark                           → .

const SPECIAL = new Map([
  [0xA8F3, 'ಗ್ಂ'], [0x1CEA, 'ಗ್ಂ'], [0xA8F5, 'ಗ್ಗ್ಂ'],
  [0x1CF5, 'ೱ'], [0x1CF6, 'ೲ'],
  [0x0950, 'ಓಂ'], [0x0970, '.'],
]);

// Kannada code points that are unassigned or mean something else, so the
// Devanagari letter is kept rather than mapped by offset.
const GAPS = new Set([0x0C84, 0x0C8D, 0x0C91, 0x0CA9, 0x0CB4, 0x0CC5, 0x0CC9, 0x0CCE, 0x0CCF, 0x0CD0, 0x0CD1, 0x0CD2, 0x0CD3, 0x0CD4]);

export function toKnda(s) {
  let out = '';
  for (const ch of s) {
    const c = ch.codePointAt(0);
    const sp = SPECIAL.get(c);
    if (sp !== undefined) { out += sp; continue; }
    if ((c >= 0x0901 && c <= 0x094D) || (c >= 0x0960 && c <= 0x0963) || (c >= 0x0966 && c <= 0x096F)) {
      const k = c + 0x380;
      out += GAPS.has(k) ? ch : String.fromCodePoint(k);
    } else out += ch;
  }
  return out;
}

// Characters a converted line may contain: Kannada letters and signs, the
// shared Vedic marks and dandas, joiners, digits and plain punctuation.
export function isCleanKannada(s) {
  return /^[ಀ-ೳ॒॑᳚।॥‌‍0-9\s.,;:!?'"()\-–—‘’“”|*+=/[\]{}]*$/.test(s);
}
