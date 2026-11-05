// The dictionary screens (Śabdārtha Kaustubha, Sanskrit → Kannada): home with the letters and the word of the day, a letter page,
// a word page, and the look-up box. Used by Vedāvalokanam (app.js) and by the standalone Dictionary app (kosha/app.js), which
// pass in the few things that differ between them (where to put the page, how to translate labels, where the data lives).
import { devaToIast } from './translit.js';
import { looseKey } from './search-key.js';
import { fmt } from './common.js';
import { FIELDS, SOURCE, koshaHref, koshaRows, lookup as koshaLookup, neighbours as koshaNeighbours, shardAt, wordOfDay, anotherWord } from './kosha.js';

/**
 * env: { main, $, esc, T, Tp, go, getHash, setTitle, json, tsv, setReaderNav, SUN_SVG, ARROW,
 *        base ('' beside data/, '../' one folder down), sourcesHref, creditExtra (html appended to the credit line) }
 */
export function createKosha(env) {
const { main, $, esc, T, Tp, go, getHash, setTitle, json, tsv, setReaderNav, SUN_SVG, ARROW, base = '', sourcesHref = '#/about', creditExtra = '' } = env;
const cache = {};
const koshaData = {
  keys: () => (cache.kkeys ||= tsv(base + 'data/kosha/keys.tsv').then((ls) => ls.map((l) => l.split('\t'))).catch((e) => { cache.kkeys = null; throw e; })),
  // an older copy kept by the offline cache has no letters: fetch it fresh, and if that fails, fall back to the plain letters
  manifest: async () => (cache.kman ||= await (async () => {
    let m = await json(base + 'data/kosha/shards.json');
    if (!m.letters) { try { m = await (await fetch(`${base}data/kosha/shards.json?fresh=${Date.now()}`, { cache: 'reload' })).json(); } catch { /* offline */ } }
    if (!m.letters) m = { ...m, letters: KOSHA_LETTERS.map((l) => [l, 0, l]) };
    return m;
  })()),
  words: async () => (cache.kwotd ||= (await json(base + 'data/kosha/wotd.json')).words),
  shard: async (f) => ((cache.kshard ||= new Map()).has(f) ? cache.kshard.get(f) : (cache.kshard.set(f, await json(`${base}data/kosha/${f}.json`)), cache.kshard.get(f))),
};
// the letters of the browse bar: vowels, then consonants
const KOSHA_LETTERS = [...'अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह'];
const kLine = (f, text, lang = 'sa') => (text ? `<div class="k-f"><small>${T(f[1], f[0])}</small><span lang="${lang}">${esc(text)}</span></div>` : '');
function koshaSenses(senses) {
  return senses.map((s) => {
    const [pos, kn, ...rest] = s;
    return `<li class="k-sense"><div class="k-top">${pos ? `<small class="k-pos" lang="sa">${esc(pos)}</small>` : ''}<span class="k-kn" lang="kn">${esc(kn || '')}</span></div>
      ${rest.map((v, j) => kLine(FIELDS[j + 2], v)).join('')}</li>`;
  }).join('');
}
// "About the author" on the dictionary page. Only what the catalogue records and booksellers' listings say: no dates or life
// story are given in the sources used, so none are written here.
const KOSHA_AUTHOR = `<details class="k-about" id="kAbout">
  <summary>${T('About the author', 'लेखकपरिचयः')}</summary>
  <div class="k-about-b">
    <h2 class="k-an"><span>Chakravarti Srinivasa Gopalacharya</span> <span lang="kn">ಚಕ್ರವರ್ತಿ ಶ್ರೀನಿವಾಸ ಗೋಪಾಲಾಚಾರ್ಯ</span></h2>
    <p class="k-at">Sāhitya Vidvān</p>
    <p>Chakravarti Srinivasa Gopalacharya compiled the <i>Śabdārtha Kaustubha</i>, a Sanskrit–Kannada dictionary in six volumes. The scanned edition runs to 3,016 pages, and a bookseller describes more than 75,000 entries. Each gives the word’s derivation, its Kannada meanings and its usages, with terms from the śāstras, sāhitya, tarka, vyākaraṇa and other fields.</p>
    <p>Part 2 of an earlier Sanskrit–Kannada word-book under his name, the <i>Saṃskṛta-Kannaḍa Śabdakośa</i>, is catalogued as printed by Bangalore Press in 1967 (522 pages). A 2014 printing of the <i>Śabdārtha Kaustubha</i> is sold under the BAPPCO imprint.</p>
    <p>This app reads the dictionary from the open digital text distributed by the indic-dict project.</p>
    <p class="k-an-note">His dates and life are not given in the sources used for this app. They are best taken from the preface of the printed volumes.</p>
    <p class="k-an-src"><a href="https://archive.org/details/Sabdartha_Kausthubha_Sanskrit_Kannada_Dictionary_Sahitya_Vidwan_Sri_Chakravarti_" rel="noopener">Scanned edition</a> · <a href="https://archive.org/details/gss.samskrutakannada0000part2.chak" rel="noopener">Śabdakośa, part 2</a> · <a href="https://www.exoticindia.com/book/details/sanskrit-kannada-dictionary-set-of-6-volumes-nzf763" rel="noopener">Six-volume set</a></p>
  </div>
</details>`;

async function viewKosha(head, params) {
  kosha_off?.();
  setTitle(head ? `${devaToIast(head)} · Dictionary` : 'Dictionary');
  const man = await koshaData.manifest();
  const bar = `<form class="k-find" id="kFind" role="search"><input id="kq" type="search" autocomplete="off" autocapitalize="none" spellcheck="false" placeholder="${esc(Tp('Look up a word: agni, अग्नि, ಅಗ್ನಿ', 'शब्दं विचिनु'))}" aria-label="${esc(Tp('Look up a word', 'शब्दं विचिनु'))}"><div class="k-sug" id="kSug" hidden></div></form>`;
  const credit = `<p class="k-credit">${esc(SOURCE)} · ${T('Sanskrit words with Kannada meanings', 'संस्कृतशब्दाः कन्नडार्थैः सह')}. <a href="#/kosha?about=author">${T('About the author', 'लेखकपरिचयः')}</a> · <a href="${sourcesHref}">${T('Sources', 'स्रोतांसि')}</a>${creditExtra}</p>`;
  if (head) {
    const e = await koshaLookup(koshaData, head);
    if (!e) { main.innerHTML = `<div class="col">${bar}<h1>${esc(head)}</h1><p class="lede">${esc(Tp('That word is not in the dictionary.', 'अयं शब्दः कोशे नास्ति।'))} <a href="#/kosha">${esc(Tp('Browse the dictionary', 'कोशं पश्य'))}</a></p></div>`; wireKoshaFind(); return; }
    const { prev, next } = await koshaNeighbours(koshaData, head);
    // a sideways swipe (or the arrow keys) moves to the neighbouring word
    setReaderNav({ prev: prev && { href: koshaHref(prev), label: devaToIast(prev) }, next: next && { href: koshaHref(next), label: devaToIast(next) }, sec: 'word' });
    main.innerHTML = `<article class="col k-entry"><nav class="k-crumb" aria-label="${esc(Tp('Where you are', 'स्थानम्'))}"><a href="#/kosha">${T('Dictionary', 'कोशः')}</a><span aria-hidden="true">›</span>${/[\u0904-\u0939]/.test([...e[0]][0]) ? `<a href="${koshaLetterHref([...e[0]][0])}" lang="sa">${[...e[0]][0]}</a><span aria-hidden="true">›</span>` : ''}<b lang="sa">${esc(e[0])}</b></nav>${bar}
      <h1 class="k-head" lang="sa">${esc(e[0])}</h1>
      <p class="k-iast">${esc(devaToIast(e[0]))}${e[1].length ? ` · <span class="k-alt">${T('also', 'अपि')} <span lang="sa">${e[1].map(esc).join(', ')}</span></span>` : ''}</p>
      <ol class="k-senses">${koshaSenses(e[2])}</ol>
      <nav class="k-nav" aria-label="${esc(Tp('Neighbouring words', 'समीपशब्दाः'))}">${prev ? `<a href="${koshaHref(prev)}">← <span lang="sa">${esc(prev)}</span></a>` : '<span></span>'}<a href="#/kosha?at=${encodeURIComponent(head)}">${T('Around this word', 'समीपे')}</a>${next ? `<a href="${koshaHref(next)}"><span lang="sa">${esc(next)}</span> →</a>` : '<span></span>'}</nav>
      ${credit}</article>`;
    wireKoshaFind(); return;
  }
  setReaderNav(null);
  const man2 = man;
  if (params.get('letter') || params.get('at')) return viewKoshaList(man2, params, bar, credit);
  // home: the search box, the word of the day and the letters (no word list: a letter opens its own page)
  kScroll.clear();
  main.innerHTML = `<div class="col k-browse">${bar}
    <section class="hero wotd" id="wotd" hidden></section>
    <div class="k-sub"><h2>${T('Browse by letter', 'वर्णक्रमेण')}</h2><small>${fmt(man.letters.length)} ${esc(Tp('letters', 'वर्णाः'))} · ${fmt(man.count)} ${esc(Tp('words', 'शब्दाः'))}</small></div>
    <nav class="k-grid" aria-label="${esc(Tp('Letters', 'वर्णाः'))}">${man.letters.map((l) => `<a class="k-tile" href="${koshaLetterHref(l[0])}"><b lang="sa">${l[0]}</b><small>${l[1] ? fmt(l[1]) : ''}</small></a>`).join('')}</nav>
    ${KOSHA_AUTHOR}
    ${credit}</div>`;
  wireKoshaFind();
  wireWotd($('#wotd')).catch(() => { /* the card is optional: not yet cached and offline */ });
  if (params.get('about') === 'author') { const d = $('#kAbout'); d.open = true; d.scrollIntoView({ block: 'start' }); }
  else if (params.get('find')) setTimeout(() => { window.scrollTo(0, 0); $('#kq')?.focus(); }, 0);
}
const koshaLetterHref = (ch) => `#/kosha?letter=${encodeURIComponent(ch)}`;
const KOSHA_QUICK = [...'अआइउएकखगचजटतदधनपफबमयरलवशसह'];
const kScroll = new Map(); // where each list was left when a word was opened: Back returns to the same spot
let kosha_off = null; // removes the scroll listeners of the list on screen
// a letter page (or the words around one word): a continuous list that starts at the first word, with dividers between letters
async function viewKoshaList(man, params, bar, credit) {
  const letter = params.get('letter');
  const counts = new Map(man.letters.map((l) => [l[0], l[1]]));
  const li = man.letters.find((l) => l[0] === letter);
  const start = li ? li[2] : params.get('at');
  if (letter && !li) { go('#/kosha'); return; }
  const page = await shardAt(koshaData, start);
  const idx = page.entries.findIndex((x) => x[0] >= start);
  const from = li ? Math.max(idx, 0) : Math.max(0, idx - 6);
  const startLetter = [...start][0];
  let shard = page.i; let prevL = li ? letter : null; // the bar already names the letter a letter page opens on
  const rowsHTML = (entries, f) => entries.slice(f).map((x, k) => {
    const ch = [...x[0]][0]; let h = '';
    if (ch !== prevL && counts.get(ch)) h = `<div class="k-div" id="kl-${ch}" data-l="${ch}" data-n="${counts.get(ch)}"><b lang="sa">${ch}</b><small>${fmt(counts.get(ch))} ${esc(Tp('words', 'शब्दाः'))}</small></div>`;
    prevL = ch;
    return `${h}<a${!li && f + k === idx ? ' id="kfirst"' : ''} href="${koshaHref(x[0])}"><b lang="sa">${esc(x[0])}</b><span lang="kn">${esc((x[2][0]?.[1] || '').slice(0, 70))}</span></a>`;
  }).join('');
  main.innerHTML = `<div class="col k-browse has-strip">
    <div class="k-bar" id="kBar"><a href="#/kosha">${T('Dictionary', 'कोशः')}</a><span aria-hidden="true">›</span><b lang="sa" id="kBarL">${startLetter}</b><small id="kBarN">${counts.get(startLetter) ? `${fmt(counts.get(startLetter))} ${esc(Tp('words', 'शब्दाः'))}` : ''}</small></div>
    ${bar}
    <div class="k-list" id="kList">${rowsHTML(page.entries, from)}</div>
    <div class="k-more" id="kMore">${esc(Tp('Loading more words…', 'शब्दाः आगच्छन्ति…'))}</div>
    ${credit}</div>
    <nav class="k-strip" id="kStrip" aria-label="${esc(Tp('Jump to a letter', 'वर्णं गच्छ'))}">${KOSHA_QUICK.map((l) => `<a href="${koshaLetterHref(l)}" lang="sa" data-l="${l}">${l}</a>`).join('')}</nav>`;
  wireKoshaFind();
  const list = $('#kList'); const more = $('#kMore');
  let loaded = 1; let busy = false;
  const loadNext = async () => {
    if (busy) return false;
    if (shard >= man.shards.length - 1) { more.textContent = Tp('End of the dictionary', 'कोशस्य अन्तः'); io?.disconnect(); return false; }
    busy = true;
    try { const es = await koshaData.shard(man.shards[shard + 1][1]); shard++; loaded++; list.insertAdjacentHTML('beforeend', rowsHTML(es, 0)); }
    catch { more.textContent = Tp('Could not load more words. Check the connection.', 'अधिकशब्दाः न लब्धाः।'); busy = false; return false; }
    busy = false; return true;
  };
  const io = 'IntersectionObserver' in window ? new IntersectionObserver((en) => { if (en[0].isIntersecting) loadNext().then((ok) => ok && sync()); }, { rootMargin: '900px 0px' }) : null;
  io?.observe(more);
  // the bar and the strip follow the letter at the top of the screen
  const barL = $('#kBarL'); const barN = $('#kBarN'); let cur = startLetter;
  const sync = () => {
    const lim = $('#kBar').getBoundingClientRect().bottom + 2; let d = null;
    for (const el of list.querySelectorAll('.k-div')) { if (el.getBoundingClientRect().top <= lim) d = el; else break; }
    const ch = d ? d.dataset.l : startLetter;
    if (ch === cur) return;
    cur = ch; barL.textContent = ch; barN.textContent = counts.get(ch) ? `${fmt(counts.get(ch))} ${Tp('words', 'शब्दाः')}` : '';
    document.querySelectorAll('#kStrip a').forEach((a) => (a.dataset.l === ch ? a.setAttribute('aria-current', 'true') : a.removeAttribute('aria-current')));
  };
  let tick = 0;
  const onScroll = () => { if (!tick) tick = requestAnimationFrame(() => { tick = 0; sync(); }); };
  window.addEventListener('scroll', onScroll, { passive: true });
  kosha_off = () => { window.removeEventListener('scroll', onScroll); io?.disconnect(); kosha_off = null; };
  sync();
  list.addEventListener('click', (e) => { if (e.target.closest('a[href^="#/kosha/"]')) kScroll.set(getHash(), { y: window.scrollY, n: loaded }); });
  // Back from a word: load the same stretch of the list and return to the same place
  const saved = kScroll.get(getHash());
  if (saved) {
    while (loaded < saved.n && await loadNext()) { /* load the stretch you had open */ }
    await document.fonts.ready; window.scrollTo(0, saved.y); sync();
  } else if (!li) document.getElementById('kfirst')?.scrollIntoView({ block: 'start' });
  else window.scrollTo(0, 0);
}
// the word-of-the-day card: today's word from a fixed list, and a button for another one at random
const SHUFFLE = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 7h3.5c2 0 3.2 1 4.3 2.6l2.4 3.8c1.1 1.6 2.3 2.6 4.3 2.6H21M3 17h3.5c2 0 3.2-1 4.3-2.6M13.2 8.4c1.1-1.4 2.3-1.4 4.3-1.4H21M18 4l3 3-3 3M18 14l3 3-3 3"/></svg>';
function wotdHTML(w, today) {
  const [head, pos, kn, deriv, quote, src] = w;
  const day = new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short' }).format(new Date());
  return `${SUN_SVG}
    <p class="hero-k" id="wotdK">${today ? `${T('Word of the day', 'अद्यतनः शब्दः')} · ${esc(day)}` : T('Another word', 'अन्यः शब्दः')}</p>
    <a class="wotd-w" href="${koshaHref(head)}" lang="sa">${esc(head)}</a>
    <p class="wotd-i">${esc(devaToIast(head))}${pos ? ` · <span lang="sa">${esc(pos)}</span>` : ''}</p>
    <p class="wotd-kn" lang="kn">${esc(kn)}</p>
    ${deriv ? `<p class="wotd-d"><small>${T('Derivation', 'व्युत्पत्तिः')}</small> <span lang="sa">${esc(deriv)}</span></p>` : ''}
    ${quote ? `<p class="wotd-q" lang="sa">${esc(quote.replace(/^"|"$/g, ''))}<cite>${esc(src)}</cite></p>` : ''}
    <div class="hero-f wotd-f">
      <span class="wotd-btns"><button type="button" class="wotd-b" id="wotdMore">${SHUFFLE}<span>${T('Another word', 'अन्यं शब्दम्')}</span></button>${today ? '' : `<button type="button" class="wotd-b" id="wotdToday"><span>${T('Today’s word', 'अद्यतनः')}</span></button>`}</span>
      <a class="hero-go" href="${koshaHref(head)}" aria-label="${esc(Tp('Open the entry', 'प्रविष्टिं पश्य'))}">${ARROW}</a>
    </div>`;
}
async function wireWotd(el) {
  const words = await koshaData.words();
  const today = wordOfDay(words);
  const show = (w) => {
    el.innerHTML = wotdHTML(w, w === today);
    el.querySelector('#wotdMore').addEventListener('click', () => show(anotherWord(words, w[0])));
    el.querySelector('#wotdToday')?.addEventListener('click', () => show(today));
  };
  show(today);
  el.hidden = false;
}

// the look-up box on the dictionary pages: suggestions as you type, Enter opens the best match
function wireKoshaFind() {
  const input = $('#kq'); const box = $('#kSug'); if (!input) return;
  let rows = [];
  const find = async () => {
    rows = koshaRows(await koshaData.keys(), looseKey(input.value), { prefixLimit: 8 });
    box.innerHTML = rows.map((r) => `<a href="${r.href}">${esc(r.label)}</a>`).join('');
    box.hidden = !rows.length;
  };
  input.addEventListener('input', () => { if (input.value.trim()) find().catch(() => { box.hidden = true; }); else box.hidden = true; });
  $('#kFind').addEventListener('submit', (e) => { e.preventDefault(); if (rows[0]) go(rows[0].href); });
}


return { view: viewKosha, data: koshaData, wotd: async () => wordOfDay(await koshaData.words()) };
}
