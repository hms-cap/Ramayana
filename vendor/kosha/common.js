// Small pure helpers and labels shared by the app and by search (no DOM, no state).

export const FACETS = {
  rishi: { label: 'Ṛṣi', deva: 'ऋषि', plural: 'seers', one: 'seer' },
  devata: { label: 'Devatā', deva: 'देवता', plural: 'deities', one: 'deity' },
  chandas: { label: 'Chandas', deva: 'छन्दस्', plural: 'metres', one: 'metre' },
};
export const FKEYS = Object.keys(FACETS);
export const LAYERS = {
  samhita: { label: 'Saṃhitā', deva: 'संहिता', plural: 'Saṃhitās' },
  brahmana: { label: 'Brāhmaṇa', deva: 'ब्राह्मण', plural: 'Brāhmaṇas' },
  aranyaka: { label: 'Āraṇyaka', deva: 'आरण्यक', plural: 'Āraṇyakas' },
  upanishad: { label: 'Upaniṣad', deva: 'उपनिषद्', plural: 'Upaniṣads' },
};

export const fmt = (n) => Number(n).toLocaleString('en-US');
export const cap = (s) => String(s).replace(/(^|[\s-])(\S)/g, (m, a, b) => a + b.toUpperCase());
export function refOf(meta, d1, d2, v, label) {
  if (meta.refFmt === 'label' && label) return label;
  const parts = meta.refFmt === 'v' ? [v] : meta.refFmt === 'd2.v' ? [d2, v] : [d1, d2, v];
  return parts.filter((p) => p !== undefined && p !== null).join('.');
}
export function groupName(meta, d1) {
  if (meta.groupNames?.[d1]) return meta.groupNames[d1];
  return `${meta.levels[0]} ${d1}`;
}
export function findHref(id, filters) {
  const q = new URLSearchParams(Object.entries(filters).filter(([, v]) => v));
  return `#/v/${id}/find?${q}`;
}
