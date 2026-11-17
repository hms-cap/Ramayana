/* A small local pañcāṅga: tithi, nakṣatra, yoga, karaṇa, vāra, amānta māsa, saṃvatsara, ṛtu, ayana, sunrise and
   sunset for a place, computed in the browser (no server). Adapted from the VedaAlokana app's panchanga.js.

   Sun: Meeus, Astronomical Algorithms ch. 25 (about 0.01°). Moon: Meeus ch. 47 with its 59 largest longitude terms
   (about 0.01–0.05°). Sidereal positions use the Lahiri ayanāṃśa. Ending times are found by bisection, so they can
   differ from printed pañcāṅgas by a few minutes; the day's elements are those current at sunrise.
   window.VRPanchanga(date, lat, lon) → names in IAST, times in ms. */
(function () {
  "use strict";
const R = Math.PI / 180;
const norm = (a) => ((a % 360) + 360) % 360;
const jd = (ms) => ms / 86400000 + 2440587.5 + 69 / 86400; // ≈ TT

function sunLon(J) {
  const T = (J - 2451545) / 36525;
  const L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T;
  const M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T;
  const C = (1.914602 - 0.004817 * T - 0.000014 * T * T) * Math.sin(M * R)
    + (0.019993 - 0.000101 * T) * Math.sin(2 * M * R) + 0.000289 * Math.sin(3 * M * R);
  const om = 125.04 - 1934.136 * T;
  return norm(L0 + C - 0.00569 - 0.00478 * Math.sin(om * R));
}

// [D, M, M', F, coefficient × 1e-6°]
const MOON = [
  [0,0,1,0,6288774],[2,0,-1,0,1274027],[2,0,0,0,658314],[0,0,2,0,213618],[0,1,0,0,-185116],[0,0,0,2,-114332],
  [2,0,-2,0,58793],[2,-1,-1,0,57066],[2,0,1,0,53322],[2,-1,0,0,45758],[0,1,-1,0,-40923],[1,0,0,0,-34720],
  [0,1,1,0,-30383],[2,0,0,-2,15327],[0,0,1,2,-12528],[0,0,1,-2,10980],[4,0,-1,0,10675],[0,0,3,0,10034],
  [4,0,-2,0,8548],[2,1,-1,0,-7888],[2,1,0,0,-6766],[1,0,-1,0,-5163],[1,1,0,0,4987],[2,-1,1,0,4036],
  [2,0,2,0,3994],[4,0,0,0,3861],[2,0,-3,0,3665],[0,1,-2,0,-2689],[2,0,-1,2,-2602],[2,-1,-2,0,2390],
  [1,0,1,0,-2348],[2,-2,0,0,2236],[0,1,2,0,-2120],[0,2,0,0,-2069],[2,-2,-1,0,2048],[2,0,1,-2,-1773],
  [2,0,0,2,-1595],[4,-1,-1,0,1215],[0,0,2,2,-1110],[3,0,-1,0,-892],[2,1,1,0,-810],[4,-1,-2,0,759],
  [0,2,-1,0,-713],[2,2,-1,0,-700],[2,1,-2,0,691],[2,-1,0,-2,596],[4,0,1,0,549],[0,0,4,0,537],
  [4,-1,0,0,520],[1,0,-2,0,-487],[2,1,0,-2,-399],[0,0,2,-2,-381],[1,1,1,0,351],[3,0,-2,0,-340],
  [4,0,-3,0,330],[2,-1,2,0,327],[0,2,1,0,-323],[1,1,-1,0,299],[2,0,3,0,294],
];
function moonLon(J) {
  const T = (J - 2451545) / 36525;
  const Lp = 218.3164477 + 481267.88123421 * T - 0.0015786 * T * T;
  const D = 297.8501921 + 445267.1114034 * T - 0.0018819 * T * T;
  const M = 357.5291092 + 35999.0502909 * T - 0.0001536 * T * T;
  const Mp = 134.9633964 + 477198.8675055 * T + 0.0087414 * T * T;
  const F = 93.2720950 + 483202.0175233 * T - 0.0036539 * T * T;
  const E = 1 - 0.002516 * T - 0.0000074 * T * T;
  let s = 0;
  for (const [d, m, mp, f, c] of MOON) {
    const e = Math.abs(m) === 1 ? E : Math.abs(m) === 2 ? E * E : 1;
    s += c * e * Math.sin((d * D + m * M + mp * Mp + f * F) * R);
  }
  s += 3958 * Math.sin((119.75 + 131.849 * T) * R) + 1962 * Math.sin((Lp - F) * R) + 318 * Math.sin((53.09 + 479264.29 * T) * R);
  const om = 125.04 - 1934.136 * T;
  return norm(Lp + s / 1e6 - 0.00478 * Math.sin(om * R));
}

const ayanamsa = (J) => 23.85306 + 1.39722 * ((J - 2451545) / 36525); // Lahiri
const elong = (ms) => { const J = jd(ms); return norm(moonLon(J) - sunLon(J)); };
const sidMoon = (ms) => { const J = jd(ms); return norm(moonLon(J) - ayanamsa(J)); };
const sidSun = (ms) => { const J = jd(ms); return norm(sunLon(J) - ayanamsa(J)); };
const yogaAng = (ms) => norm(sidMoon(ms) + sidSun(ms));

  // First moment after t0 at which the angle f(t) (increasing, mod 360) reaches `target`.
function crossing(f, target, t0, maxHours = 40) {
  const ahead = (t) => norm(f(t) - target + 180) - 180; // <0 before, ≥0 after
  let a = t0; let b = t0;
  for (let h = 0; h < maxHours; h++) { b = a + 3600e3; if (ahead(a) < 0 && ahead(b) >= 0) break; a = b; }
  for (let i = 0; i < 30; i++) { const m = (a + b) / 2; if (ahead(m) < 0) a = m; else b = m; }
  return b;
}
// Last moment before t0 at which the elongation was 0 (new moon), and the next one.
function newMoons(t0) {
  let a = t0;
  while (true) { const b = a - 12 * 3600e3; if (elong(b) > elong(a)) { a = b; break; } a = b; }
  const prev = crossing(elong, 0, a, 14);
  const next = crossing(elong, 0, prev + 25 * 86400e3, 7 * 24);
  return [prev, next];
}

function sunAlt(ms, lat, lon) {
  const J = jd(ms); const T = (J - 2451545) / 36525;
  const lam = sunLon(J) * R; const eps = (23.4393 - 0.013 * T) * R;
  const ra = Math.atan2(Math.cos(eps) * Math.sin(lam), Math.cos(lam));
  const dec = Math.asin(Math.sin(eps) * Math.sin(lam));
  const gmst = norm(280.46061837 + 360.98564736629 * (J - 2451545)) * R;
  const H = gmst + lon * R - ra;
  return Math.asin(Math.sin(lat * R) * Math.sin(dec) + Math.cos(lat * R) * Math.cos(dec) * Math.cos(H)) / R;
}
function sunEvent(dayStart, lat, lon, rising) {
  const h0 = -0.833; const step = 10 * 60e3;
  for (let t = dayStart; t < dayStart + 86400e3; t += step) {
    const a = sunAlt(t, lat, lon) - h0; const b = sunAlt(t + step, lat, lon) - h0;
    if (rising ? a < 0 && b >= 0 : a > 0 && b <= 0) {
      let lo = t; let hi = t + step;
      for (let i = 0; i < 20; i++) { const m = (lo + hi) / 2; const v = sunAlt(m, lat, lon) - h0; if ((v < 0) === rising) lo = m; else hi = m; }
      return hi;
    }
  }
  return null;
}

const NAMES = {
  tithi: ['Pratipat', 'Dvitīyā', 'Tṛtīyā', 'Caturthī', 'Pañcamī', 'Ṣaṣṭhī', 'Saptamī', 'Aṣṭamī', 'Navamī', 'Daśamī', 'Ekādaśī', 'Dvādaśī', 'Trayodaśī', 'Caturdaśī', 'Pūrṇimā', 'Amāvāsyā'],
  nakshatra: ['Aśvinī', 'Bharaṇī', 'Kṛttikā', 'Rohiṇī', 'Mṛgaśirā', 'Ārdrā', 'Punarvasu', 'Puṣya', 'Āśleṣā', 'Maghā', 'Pūrvaphalgunī', 'Uttaraphalgunī', 'Hasta', 'Citrā', 'Svātī', 'Viśākhā', 'Anurādhā', 'Jyeṣṭhā', 'Mūla', 'Pūrvāṣāḍhā', 'Uttarāṣāḍhā', 'Śravaṇa', 'Dhaniṣṭhā', 'Śatabhiṣak', 'Pūrvabhādrapadā', 'Uttarabhādrapadā', 'Revatī'],
  yoga: ['Viṣkambha', 'Prīti', 'Āyuṣmān', 'Saubhāgya', 'Śobhana', 'Atigaṇḍa', 'Sukarmā', 'Dhṛti', 'Śūla', 'Gaṇḍa', 'Vṛddhi', 'Dhruva', 'Vyāghāta', 'Harṣaṇa', 'Vajra', 'Siddhi', 'Vyatīpāta', 'Varīyān', 'Parigha', 'Śiva', 'Siddha', 'Sādhya', 'Śubha', 'Śukla', 'Brahma', 'Indra', 'Vaidhṛti'],
  karana: ['Bava', 'Bālava', 'Kaulava', 'Taitila', 'Gara', 'Vaṇija', 'Viṣṭi'],
  karanaFixed: { 0: 'Kiṃstughna', 57: 'Śakuni', 58: 'Catuṣpāda', 59: 'Nāga' },
  vara: ['Bhānuvāsara', 'Somavāsara', 'Maṅgalavāsara', 'Budhavāsara', 'Guruvāsara', 'Śukravāsara', 'Śanivāsara'],
  masa: ['Caitra', 'Vaiśākha', 'Jyeṣṭha', 'Āṣāḍha', 'Śrāvaṇa', 'Bhādrapada', 'Āśvayuja', 'Kārtika', 'Mārgaśīrṣa', 'Pauṣa', 'Māgha', 'Phālguna'],
  rtu: ['Vasanta', 'Grīṣma', 'Varṣā', 'Śarad', 'Hemanta', 'Śiśira'],
  samvatsara: ['Prabhava', 'Vibhava', 'Śukla', 'Pramoda', 'Prajāpati', 'Āṅgirasa', 'Śrīmukha', 'Bhāva', 'Yuva', 'Dhātṛ', 'Īśvara', 'Bahudhānya', 'Pramāthī', 'Vikrama', 'Vṛṣa', 'Citrabhānu', 'Svabhānu', 'Tāraṇa', 'Pārthiva', 'Vyaya', 'Sarvajit', 'Sarvadhārī', 'Virodhī', 'Vikṛti', 'Khara', 'Nandana', 'Vijaya', 'Jaya', 'Manmatha', 'Durmukha', 'Hemalamba', 'Vilamba', 'Vikārī', 'Śārvarī', 'Plava', 'Śubhakṛt', 'Śobhakṛt', 'Krodhī', 'Viśvāvasu', 'Parābhava', 'Plavaṅga', 'Kīlaka', 'Saumya', 'Sādhāraṇa', 'Virodhakṛt', 'Paridhāvī', 'Pramādī', 'Ānanda', 'Rākṣasa', 'Nala', 'Piṅgala', 'Kālayukta', 'Siddhārthī', 'Raudra', 'Durmati', 'Dundubhi', 'Rudhirodgārī', 'Raktākṣī', 'Krodhana', 'Akṣaya'],
};

// The pañcāṅga for the local calendar day containing `date`, at a place. Names are in IAST.
function panchanga(date, lat, lon) {
  const d0 = new Date(date); d0.setHours(0, 0, 0, 0);
  const day = d0.getTime();
  const rise = sunEvent(day, lat, lon, true) ?? day + 6 * 3600e3;
  const set = sunEvent(day, lat, lon, false);
  const e = elong(rise);
  const ti = Math.floor(e / 12);
  const tithiEnd = crossing(elong, (ti + 1) * 12 % 360, rise);
  const nk = Math.floor(sidMoon(rise) / (360 / 27));
  const nkEnd = crossing(sidMoon, (nk + 1) * (360 / 27) % 360, rise);
  const yg = Math.floor(yogaAng(rise) / (360 / 27));
  const ygEnd = crossing(yogaAng, (yg + 1) * (360 / 27) % 360, rise);
  const k = Math.floor(e / 6);
  const karana = NAMES.karanaFixed[k] || NAMES.karana[(k - 1) % 7];
  const [nm, nextNm] = newMoons(rise);
  const sign = Math.floor(sidSun(nm) / 30);
  const masaI = (sign + 1) % 12;
  const adhika = Math.floor(sidSun(nextNm) / 30) === sign;
  const g = new Date(rise);
  const sy = g.getFullYear() - (g.getMonth() < 4 && masaI >= 9 ? 1 : 0);
  return {
    sunrise: rise, sunset: set,
    paksha: ti < 15 ? 'Śukla' : 'Kṛṣṇa',
    tithi: ti === 14 ? NAMES.tithi[14] : ti === 29 ? NAMES.tithi[15] : NAMES.tithi[ti % 15],
    tithiEnd, nakshatra: NAMES.nakshatra[nk], nakshatraEnd: nkEnd,
    yoga: NAMES.yoga[yg], yogaEnd: ygEnd, karana,
    vara: NAMES.vara[g.getDay()],
    masa: (adhika ? 'Adhika ' : '') + NAMES.masa[masaI],
    rtu: NAMES.rtu[Math.floor(masaI / 2)],
    ayana: sidSun(rise) >= 270 || sidSun(rise) < 90 ? 'Uttarāyaṇa' : 'Dakṣiṇāyana',
    samvatsara: NAMES.samvatsara[(((sy - 1987) % 60) + 60) % 60],
  };
}

  window.VRPanchanga = panchanga;
})();
