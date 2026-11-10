"""Alternative card paintings for the kāṇḍas and parvas, and alternative work-chip icons.

Each unit has two extra motifs drawn from its story (motifs only, no figures):
A in a Kalamkari manner (cream line, stitched border), B in a Pattachitra manner
(gold line, saw-tooth border). The card shows one of current / A / B, chosen at
random each time the app is opened (site/static/app.js).
"""
import math

def spokes(cx, cy, r, n, w=".7"):
    return '<path d="' + "".join(f"M{cx} {cy}L{cx+r*math.cos(2*math.pi*i/n):.2f} {cy+r*math.sin(2*math.pi*i/n):.2f}" for i in range(n)) + f'" stroke-width="{w}"/>'
def dot(x, y, r=.6): return f'<circle cx="{x}" cy="{y}" r="{r}" fill="currentColor" stroke="none"/>'
WAVES = '<path d="M2 19.5q2.5-2 5 0t5 0t5 0t5 0"/>'
WAVES2 = '<path d="M3.5 22.5q2.1-1.6 4.2 0t4.2 0t4.2 0t4.2 0" stroke-width=".7"/>'

R = {  # Rāmāyaṇa kāṇḍas: (name, A (motif, caption), B (motif, caption))
1: ("Bāla", ("Tryambaka, Śiva's bow, broken at Sītā's svayaṃvara",
   '<path d="M3 15C5 8.5 8.6 6.2 11.2 6.8"/><path d="M12.8 6.8C15.4 6.2 19 8.5 21 15"/><path d="M3 15Q6.5 17.2 9.2 16.4M21 15Q17.5 17.2 14.8 16.4" stroke-width=".7"/><path d="M12 4.6V2.4M10.4 5.1L9.2 3.6M13.6 5.1L14.8 3.6" stroke-width=".8"/><path d="M4 20.5h16"/>'),
   ("Putrakāmeṣṭi: the sacrificial fire for sons",
   '<path d="M4.5 21h15M6 21v-3h12v3M7.5 18v-2h9v2"/><path d="M12 16c-3.2-2-2.4-5.6 0-9 .6 2.2 2.4 2.8 2.4 5 0 2-1.2 3.2-2.4 4z"/><path d="M9.2 16c-1.3-1-1.1-2.7 0-3.8M14.8 16c1.3-1 1.1-2.7 0-3.8" stroke-width=".8"/>')),
2: ("Ayodhyā", ("Pādukā on the throne: Bharata's regency",
   '<path d="M5 21v-8h14v8M4 13h16M6 13V8.5C6 6.4 8 5 12 5s6 1.4 6 3.5V13"/><ellipse cx="10" cy="16.8" rx="1.2" ry="2.6"/><ellipse cx="14" cy="16.8" rx="1.2" ry="2.6"/>' + dot(10, 15.6, .45) + dot(14, 15.6, .45)),
   ("The royal umbrella, set aside at the exile",
   '<path d="M4 11Q12 1.8 20 11Z"/><path d="M4 11q2 1.6 4 0t4 0t4 0t4 0" stroke-width=".8"/><path d="M12 11v10M12 4.2V2.4"/><path d="M9 21h6" stroke-width=".8"/>')),
3: ("Araṇya", ("The leaf hut at Pañcavaṭī",
   '<path d="M3.5 20.5V13L10 7.5l6.5 5.5v7.5Z"/><path d="M3.5 13L10 7.5M5.8 11.2l1.6 1.6M8 9.4l1.6 1.6M12 9.4l-1.6 1.6M14.2 11.2l-1.6 1.6" stroke-width=".7"/><path d="M8.5 20.5v-4h3v4"/><path d="M19.5 20.5v-6"/><circle cx="19.5" cy="11.5" r="3"/><path d="M2 20.5h20"/>'),
   ("The golden deer",
   '<path d="M5.5 14c0-2.4 3-3.4 7-3.4 2.2 0 3.6-.6 4.6-2l1.4-1.6 1.1 1c-.3 1.6-1 2.9-2.1 3.6 0 2.4-1 3.9-2.5 4.4h-6c-2 0-3.5-.9-3.5-2z"/><path d="M8 16v5M10 16.5V21M14 16.5V21M16 16v5"/><path d="M18.4 7l-1-3M18.4 7l1.6-2.4M17.7 5.3l-1.3-.6" stroke-width=".8"/>' + dot(9, 13, .5) + dot(11.5, 12.4, .5) + dot(13.4, 13.6, .5))),
4: ("Kiṣkindhā", ("Seven sāla trees pierced by one arrow",
   "".join(f'<path d="M{x:.1f} 21V7.5"/><circle cx="{x:.1f}" cy="6" r="1.5"/>' for x in [3.5 + i * 2.83 for i in range(7)]) + '<path d="M1.5 13.5H22.5M19.6 11.2l2.9 2.3-2.9 2.3" stroke-width="1.1"/>'),
   ("Sītā's jewels, dropped from the sky",
   '<path d="M4.5 8.5Q12 19 19.5 8.5"/>' + "".join(dot(4.5 + i * 1.5, 8.5 + 7.6 * math.sin(math.pi * i / 10), .6) for i in range(11)) + '<path d="M12 15.6c-1.4 1.4-1.4 3 0 4.6 1.4-1.6 1.4-3.2 0-4.6z"/>' + dot(8, 3.4, .5) + dot(12, 2.4, .6) + dot(16, 3.4, .5) + '<path d="M10 4.6l-.4 1.4M14 4.6l.4 1.4" stroke-width=".6"/>')),
5: ("Sundara", ("Rāma's signet ring, carried to Sītā",
   '<circle cx="12" cy="14.5" r="6"/><circle cx="12" cy="14.5" r="4.4" stroke-width=".7"/><path d="M9.2 8.6L12 4.6l2.8 4z"/><path d="M12 2.4v-1M8.6 3.6l-.8-.8M15.4 3.6l.8-.8" stroke-width=".8"/>'),
   ("The Aśoka grove where Sītā waits",
   '<path d="M12 21v-8M12 15l-3-2.5M12 14l3.2-2.6"/><path d="M5 11.5c-1.6-3.4 1.2-6.6 4.2-5.8C10 3 14 3 15 5.6c3.2-.6 5.6 2.6 4 5.6-1 2-3.4 2.4-5 1.6-1 1-3 1-4 0-1.8.8-4.2.4-5-1.3z"/>' + dot(8, 8.6, .7) + dot(12, 6.6, .7) + dot(15.6, 8.4, .7) + dot(10.4, 10.4, .7) + dot(17, 10.6, .7) + '<path d="M7 21h10"/>')),
6: ("Yuddha", ("Setu: the stone bridge to Laṅkā",
   WAVES + WAVES2 + '<path d="M1.5 14.6h1.6M20.9 14.6h1.6M2.3 14.6v3M21.7 14.6v3" stroke-width="1"/>' + "".join(f'<rect x="{3 + 18 * ((i + .5) / 8) - 1.05:.2f}" y="{13.6 - 3.4 * math.sin(math.pi * (i + .5) / 8) - 1.3:.2f}" width="2.1" height="2.6" rx=".7"/>' for i in range(8))),
   ("The mountain of healing herbs",
   '<path d="M2.5 20.5L8.5 10l3 4.4L15.2 7l6.3 13.5Z"/><path d="M15.2 7V4M13.2 5.2l-1-1M17.2 5.2l1-1" stroke-width=".8"/><path d="M12.6 17.5c1-.8 2-.8 3 0M8 17.8c.8-.6 1.6-.6 2.4 0" stroke-width=".7"/>' + dot(15.2, 9.6, .6) + dot(14, 12, .5) + dot(16.6, 12.4, .5))),
7: ("Uttara", ("The crown of the coronation",
   '<path d="M5.5 19h13M5.5 19v-6.5l2.4 2L10 8.5l2 4 2-4 2.1 6 2.4-2V19"/><path d="M12 8.5V4"/>' + dot(12, 3, .9) + '<path d="M7 17h10" stroke-width=".7"/>' + dot(9, 17.9, .45) + dot(12, 17.9, .45) + dot(15, 17.9, .45)),
   ("Palm-leaf manuscript: the epic as it was sung",
   '<rect x="2.5" y="8.5" width="19" height="6.5" rx="1.6"/><path d="M4.5 10.8h15M4.5 12.8h15" stroke-width=".6"/><circle cx="8" cy="11.8" r=".8"/><circle cx="16" cy="11.8" r=".8"/><path d="M8 15v3.5M16 15v3.5" stroke-width=".8"/><path d="M7 18.5l1 2 1-2M15 18.5l1 2 1-2" stroke-width=".7"/><path d="M2 7h20" stroke-width=".8"/>')),
}

M = {
1: ("Ādi", ("The fish target on the wheel: Draupadī's svayaṃvara",
   '<circle cx="12" cy="6" r="3.6"/>' + spokes(12, 6, 3.6, 8, ".5") + '<path d="M8.5 11.5c2-1.6 5-1.6 7 0-2 1.6-5 1.6-7 0zM15.5 11.5l2-1.2v2.4z"/><path d="M12 9.6v-0"/><ellipse cx="12" cy="19" rx="8" ry="2.4"/><path d="M8.8 19.2c1.6-.9 3.6-.9 5.2 0" stroke-width=".6"/>'),
   ("Gaṅgā, mother of Bhīṣma",
   '<path d="M12 13c-2.6-1.4-2.6-5 0-8 2.6 3 2.6 6.6 0 8z"/><path d="M12 13c-2.4.2-4.4-1-5-3.6 2.4-.4 4.4.8 5 3.6zM12 13c2.4.2 4.4-1 5-3.6-2.4-.4-4.4.8-5 3.6z"/>' + '<path d="M2 16.5q2.5-2 5 0t5 0t5 0t5 0"/>' + WAVES + WAVES2)),
2: ("Sabhā", ("Maya's assembly hall",
   '<path d="M3 9L12 3l9 6Z"/><path d="M4 9h16M6 9v10M10 9v10M14 9v10M18 9v10M3 19h18"/><path d="M8 21.6q2-1.2 4 0t4 0" stroke-width=".7"/>'),
   ("The pool that looked like a floor",
   '<rect x="3.5" y="3.5" width="17" height="17" rx="1.5"/><path d="M9.2 3.5v17M14.8 3.5v17M3.5 9.2h17M3.5 14.8h17" stroke-width=".6"/><path d="M12 14.2c-1.6-.8-1.6-3.2 0-4.6 1.6 1.4 1.6 3.8 0 4.6z"/><path d="M12 14.2c-1.6.2-2.8-.6-3-2.2 1.6-.2 2.8.6 3 2.2zM12 14.2c1.6.2 2.8-.6 3-2.2-1.6-.2-2.8.6-3 2.2z" stroke-width=".8"/><path d="M4.8 6.4q1 .8 2 0M17.2 18q1 .8 2 0M4.8 18q1 .8 2 0M17.2 6.4q1 .8 2 0" stroke-width=".6"/>')),
3: ("Vana", ("The inexhaustible bowl",
   '<path d="M4 12h16"/><path d="M5 12c0 4.6 3 7.6 7 7.6s7-3 7-7.6"/><path d="M9.5 19.6h5M10.5 21.4h3"/><path d="M8 9q4-4 8 0M10 6.4q2-2 4 0" stroke-width=".8"/>' + dot(9, 13.6) + dot(12, 14.4) + dot(15, 13.6)),
   ("The yakṣa's lake",
   '<ellipse cx="12" cy="17.5" rx="9" ry="3"/><path d="M8 17.6c1.4-.8 3-.8 4.4 0M13.6 18.6c1-.6 2.2-.6 3.2 0" stroke-width=".6"/><path d="M15 14.6V9.8M15 9.8c-2.2 0-3.6-1.4-3.4-3 1.4-.2 2.6.6 3.4 1.6"/><path d="M15 7.4c.2-2 1.4-3 2.6-3l2 .8-1.8.4" /><path d="M6.6 14.6c-1-.8-1-2.2 0-3 1 .8 1 2.2 0 3z"/>')),
4: ("Virāṭa", ("The cow-bell: the raid on Virāṭa's herds",
   '<path d="M8 18c0-6 1-11 4-11s4 5 4 11z"/><path d="M7 18h10"/><circle cx="12" cy="20" r="1.1"/><path d="M10 7c0-2.4 4-2.4 4 0"/><path d="M5 5q7-4 14 0" stroke-width=".7"/>'),
   ("Ankle bells of the dance teacher",
   '<path d="M3.5 8.5Q12 18 20.5 8.5"/>' + "".join(f'<circle cx="{4.8 + i * 2.4:.1f}" cy="{9.8 + 5.6 * math.sin(math.pi * (i + .5) / 7):.2f}" r="1.1"/>' for i in range(7)) + '<path d="M3.5 8.5q8.5 7.2 17 0" stroke-width=".6"/>')),
5: ("Udyoga", ("The peace mission: a sealed message",
   '<path d="M6 4h12v15H6z"/><path d="M6 4c-1.6 0-2 2-.8 2.6M18 19c1.6 0 2-2 .8-2.6" stroke-width=".8"/><path d="M8.5 8h7M8.5 10.5h7M8.5 13h4.5" stroke-width=".7"/><circle cx="15" cy="15.6" r="1.8"/>'),
   ("The scales of war and peace",
   '<path d="M12 3.5V20M8 20.5h8M4 7h16"/>' + dot(12, 3.2, .8) + '<path d="M4 7l-2 5.5M4 7l2 5.5M20 7l-2 5.5M20 7l2 5.5" stroke-width=".6"/><path d="M1.5 12.5q2.5 2.6 5 0M17.5 12.5q2.5 2.6 5 0"/>')),
6: ("Bhīṣma", ("The chariot with the monkey banner: the Gītā",
   '<circle cx="8.5" cy="16.5" r="4.5"/>' + spokes(8.5, 16.5, 4.5, 8, ".5") + '<path d="M13 16.5h7M16.5 21V3"/><path d="M16.5 3l5 2.2-5 2.2"/><path d="M13 12h7" stroke-width=".8"/>'),
   ("The Gītā on its stand",
   '<path d="M6 21L18 13M6 13l12 8"/><path d="M4 11.5c2.6-1.4 5.4-1.4 8 0 2.6-1.4 5.4-1.4 8 0V6c-2.6-1.4-5.4-1.4-8 0-2.6-1.4-5.4-1.4-8 0z"/><path d="M12 6v5.5" stroke-width=".7"/><path d="M6 8h4M14 8h4" stroke-width=".5"/>')),
7: ("Droṇa", ("The bow laid down",
   '<path d="M3 16.5Q12 3 21 16.5"/><path d="M3 16.5H21" stroke-width=".6"/><path d="M11.2 9.2h1.6v2.2h-1.6z" stroke-width=".8"/><path d="M2.4 17.6l1.2-1.6M21.6 17.6l-1.2-1.6" stroke-width=".8"/><path d="M2 20h20"/>'),
   ("The sun at dusk: Jayadratha's last day",
   '<path d="M2 16h20"/><path d="M6.5 16a5.5 5.5 0 0 1 11 0"/><path d="M12 8.6V6M7.4 10.4L5.6 8.6M16.6 10.4l1.8-1.8M4.4 13.4l-2.2-.8M19.6 13.4l2.2-.8" stroke-width=".8"/><path d="M5 19.4h14M8 22h8" stroke-width=".7"/>')),
8: ("Karṇa", ("Kavaca and kuṇḍala: armour and earrings",
   '<path d="M8 3.5v2.4M16 3.5v2.4"/><circle cx="8" cy="9.6" r="3.6"/><circle cx="8" cy="9.6" r="1.5"/><circle cx="16" cy="9.6" r="3.6"/><circle cx="16" cy="9.6" r="1.5"/><path d="M8 13.2v3M16 13.2v3"/><path d="M6.5 17.8L8 20.6l1.5-2.8zM14.5 17.8L16 20.6l1.5-2.8z"/>'),
   ("Sūrya, Karṇa's father",
   '<circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="2.6" stroke-width=".7"/>' + "".join(f'<path d="M{12 + 6.6 * math.cos(a):.2f} {12 + 6.6 * math.sin(a):.2f}L{12 + 9.6 * math.cos(a):.2f} {12 + 9.6 * math.sin(a):.2f}"/>' for a in [2 * math.pi * i / 12 for i in range(12)]))),
9: ("Śalya", ("The lake where Duryodhana hid",
   '<path d="M2 15.5q2.5-2 5 0t5 0t5 0t5 0"/>' + WAVES + WAVES2 + '<path d="M12 13.6V9"/><circle cx="12" cy="6" r="3"/>' + dot(11, 5.4, .5) + dot(13, 6.6, .5) + '<path d="M4 13V8M5.6 13V9.4M18.4 13V8.6M20 13V9.8" stroke-width=".7"/>'),
   ("Balarāma's plough, on pilgrimage",
   '<path d="M5 4.5L16 17"/><path d="M3.4 6.2L6.8 2.8"/><path d="M16 17l4.6 3.2h-6.2z"/><path d="M12 12.4L9.4 17.2M8 17.2h3" stroke-width=".9"/><path d="M2 21.5h20" stroke-width=".7"/>')),
10: ("Sauptika", ("The owl at night",
   '<path d="M12 6c-3.6 0-5 3-5 6.6S9 19 12 19s5-2.8 5-6.4S15.6 6 12 6z"/><path d="M8 6.4L7.2 4M16 6.4l.8-2.4" stroke-width=".8"/><circle cx="10.2" cy="10.4" r="1.4"/><circle cx="13.8" cy="10.4" r="1.4"/><path d="M12 11.6l-.6 1.2h1.2z" stroke-width=".6"/><path d="M4 19.5h16"/><path d="M19.5 3.5a2.6 2.6 0 1 0 1.8 4.4 3.2 3.2 0 0 1-1.8-4.4z" stroke-width=".8"/>'),
   ("The jewel taken from Aśvatthāmā",
   '<path d="M7 9l2.4-3.4h5.2L17 9l-5 8.4z"/><path d="M7 9h10M9.4 5.6L12 9l2.6-3.4M12 9v8.4" stroke-width=".6"/><path d="M12 2.6V1.4M5 4.4l-1-.8M19 4.4l1-.8M4.4 11.4l-1.4.4M19.6 11.4l1.4.4" stroke-width=".8"/>')),
11: ("Strī", ("Water offered to the dead",
   '<g transform="rotate(35 9 8)"><path d="M6.4 3.4h5.2M7 3.4v1.8c-2.6 1-3.6 3-3.6 5 0 2.8 2.4 4.6 5.6 4.6s5.6-1.8 5.6-4.6c0-2-1-4-3.6-5V3.4"/><path d="M5.2 9h7.6" stroke-width=".6"/></g>'
   '<path d="M14.4 7.6c1.4 2.4 2 5.6 2 9.6" stroke-width=".9"/><path d="M15.6 7.4c1.2 2.2 1.8 5.2 1.8 8.8" stroke-width=".5"/>' + WAVES + WAVES2),
   ("Lamps floating on the river",
   WAVES + WAVES2 + "".join(f'<path d="M{x - 2} 15.4q2 1.6 4 0z"/><path d="M{x} 14.2c-.8-.8-.8-2 0-2.8.8.8.8 2 0 2.8z" stroke-width=".8"/>' for x in (6, 12, 18)))),
12: ("Śānti", ("The banyan: Bhīṣma's teaching on dharma",
   '<path d="M2.5 10c0-4 4.4-6.6 9.5-6.6s9.5 2.6 9.5 6.6z"/><path d="M12 10v11M9.5 21h5"/><path d="M5 10v6M7.4 10v8.4M16.6 10v8.4M19 10v6" stroke-width=".7"/>'),
   ("Pūrṇakumbha: the full vessel of peace",
   '<path d="M7.6 13c-2 3-.8 8 4.4 8s6.4-5 4.4-8z"/><path d="M9 13h6M9.6 11h4.8M9.6 11v2M14.4 11v2"/><circle cx="12" cy="7.6" r="2.6"/><path d="M9.6 10.4L6 8.8M14.4 10.4L18 8.8M10 10.6L7.6 6.6M14 10.6l2.4-4" stroke-width=".8"/>')),
13: ("Anuśāsana", ("Dāna: the gift of gold",
   '<path d="M4 15h16"/><path d="M5 15c0 3.4 3 5.6 7 5.6s7-2.2 7-5.6"/>' + "".join(f'<ellipse cx="{x}" cy="{y}" rx="2" ry=".9"/>' for x, y in ((9, 13.6), (12, 13.6), (15, 13.6), (10.5, 12), (13.5, 12), (12, 10.4))) + '<path d="M12 7.6V5.4M9.4 8.4L8 6.8M14.6 8.4L16 6.8" stroke-width=".8"/>'),
   ("Tulasī in its shrine",
   '<path d="M7 21v-7h10v7"/><path d="M6 14h12M10 21v-3.6c0-1.2 4-1.2 4 0V21" stroke-width=".8"/><path d="M12 14V5"/><path d="M12 11c-2.4.2-3.8-1-3.8-2.6 2-.2 3.4.8 3.8 2.6zM12 8.4c2.4.2 3.8-1 3.8-2.6-2-.2-3.4.8-3.8 2.6zM12 6c-1.6 0-2.4-.8-2.4-2 1.4 0 2.2.8 2.4 2z"/>')),
14: ("Āśvamedhika", ("The sacrificial horse",
   '<path d="M8 21l1-7.4C8 10.8 9.2 7 13 5.2L15 3l1 2.6c2 1 4 3.6 4 5.6l-2 1-3-1.4c-1 1.8-1 5.6 0 10.2"/><path d="M12 6.4c-.6 1.6-1.6 3-2.4 4.6M13.6 5.6c-.4 1.4-1 2.6-1.8 3.8" stroke-width=".7"/>' + dot(16.6, 7.4, .55)),
   ("The yūpa, the sacrificial post",
   '<path d="M12 21V6"/><path d="M10 6h4l-.6-2.4h-2.8z"/><path d="M10.4 8.4h3.2" stroke-width=".8"/><path d="M7.6 12q4.4 3.4 8.8 0" stroke-width=".8"/>' + dot(9, 13.2, .5) + dot(12, 14, .5) + dot(15, 13.2, .5) + '<path d="M7.5 21h9M9 18.4h6" stroke-width=".8"/>')),
15: ("Āśramavāsika", ("The forest fire",
   '<path d="M6 21v-5M18 21v-5"/><path d="M6 16c-2.2-1.6-1.6-4.2 0-6.2 1.6 2 2.2 4.6 0 6.2zM18 16c-2.2-1.6-1.6-4.2 0-6.2 1.6 2 2.2 4.6 0 6.2z"/><path d="M12 19c-3.4-1.6-3-5.6 0-10.4.8 2.6 3 3.6 3 6.2 0 2.4-1.4 3.6-3 4.2z"/><path d="M12 19c-1-.8-1-2.2 0-3.4 1 1.2 1 2.6 0 3.4z" stroke-width=".7"/><path d="M2 21h20"/>'),
   ("Staff and water-pot of the renunciant",
   '<path d="M6 2.5v19"/><path d="M4.6 2.5h2.8" stroke-width=".8"/><path d="M11 14c0-3 2-4.6 4.6-4.6S20 11 20 14s-2 6-4.4 6S11 17 11 14z"/><path d="M12.4 10.6c0-3.4 6.4-3.4 6.4 0" stroke-width=".8"/><path d="M19.6 12.4L22 10.4" />')),
16: ("Mausala", ("The iron club among the reeds",
   '<path d="M5 20L18 5" stroke-width="2"/><path d="M15.6 7.6l2.2 2M7 17.4l2.2 2" stroke-width=".8"/><path d="M3 21.5c.6-3 1-6 .6-9M5.6 21.5c.4-2.4.8-4.6 2.2-6.6M19 21.5c-.4-3-.4-6 .6-9M21 21.5c-.2-2 0-4 .8-5.6" stroke-width=".7"/>'),
   ("Dvārakā under the sea",
   '<path d="M5 15V9.6L7 7l2 2.6V15M10.4 15V7l1.6-3 1.6 3v8M15 15V9.6L17 7l2 2.6V15"/>' + '<path d="M2 15q2.5-2 5 0t5 0t5 0t5 0"/>' + WAVES + WAVES2)),
17: ("Mahāprasthānika", ("Paw-prints on the last path",
   '<path d="M3 21L21 3" stroke-width=".6" stroke-dasharray="1 2"/>' + "".join(f'<ellipse cx="{x}" cy="{y}" rx="1.3" ry="1.1"/>' + dot(x - 1.3, y - 1.6, .45) + dot(x, y - 2, .45) + dot(x + 1.3, y - 1.6, .45) for x, y in ((6, 19.4), (10.6, 15), (15, 10.6), (19.4, 6.2)))),
   ("The Himālaya",
   '<path d="M1.5 20.5L8 9l3.4 5L15.6 6l6.9 14.5Z"/><path d="M6 12.6l2-1.4 1.6 1.4M13.6 9.8l2-1.2 2 1.4" stroke-width=".8"/><path d="M2 20.5h20"/>' + dot(19, 3.6, .7) + dot(4, 4.6, .5))),
18: ("Svargārohaṇa", ("The celestial chariot",
   '<path d="M6 13h12l-1.6 4H7.6z"/><path d="M7 13V9.4L12 5l5 4.4V13"/><path d="M12 5V2.8"/>' + dot(12, 2.4, .6) + '<path d="M2 15.4c1.6-1.8 3.4-1.8 4 0M18 15.4c.6-1.8 2.4-1.8 4 0" stroke-width=".8"/><path d="M4 20.6c1.6-1.6 3.6-1.6 5.2 0 1.6-1.6 4-1.6 5.6 0 1.6-1.6 3.6-1.6 5.2 0" stroke-width=".8"/>'),
   ("The gate of heaven",
   '<path d="M6 21V11a6 6 0 0 1 12 0v10"/><path d="M8.6 21v-9a3.4 3.4 0 0 1 6.8 0v9" stroke-width=".8"/><path d="M4 21h16M5 11h14" stroke-width=".8"/>' + dot(12, 2.6, .8) + dot(6, 4.4, .5) + dot(18, 4.4, .5) + dot(3.4, 8, .4) + dot(20.6, 8, .4))),
}



def card_svg(motif: str, style: str, v: int) -> str:
    """SVG in the card's 160x120 art box; the panel takes the card's own colour (--kp)."""
    if style == "A":
        fg = "#F6E6C4"
        frame = (f'<rect x="10" y="9" width="140" height="104" rx="16" fill="none" stroke="{fg}" stroke-width="2.6" stroke-dasharray="5 4" stroke-linecap="round" opacity=".5"/>'
                 f'<rect x="15" y="14" width="130" height="94" rx="12" fill="none" stroke="{fg}" stroke-width="1" opacity=".55"/>')
    else:
        fg = "#F3C66A"
        p = "".join(f"M{x} 9l3 5l3-5" for x in range(18, 140, 6))
        q = "".join(f"M{x} 113l3-5l3 5" for x in range(18, 140, 6))
        frame = (f'<path d="{p}{q}" fill="none" stroke="{fg}" stroke-width="1.2" opacity=".7"/>'
                 f'<rect x="10" y="9" width="140" height="104" rx="16" fill="none" stroke="{fg}" stroke-width="1.2" opacity=".7"/>')
    return (f'<svg class="kart" data-v="{v}" viewBox="0 0 160 120" aria-hidden="true" focusable="false">'
            f'<rect x="4" y="4" width="152" height="114" rx="18" style="fill:var(--kp)"/>{frame}'
            f'<g transform="translate(42 21) scale(3.15)" fill="none" stroke="{fg}" color="{fg}" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round">{motif}</g></svg>')


def alts(work: str, k: int) -> list[str]:
    _, a, b = (R if work == "ram" else M)[k]
    return [card_svg(a[1], "A", 1), card_svg(b[1], "B", 2)]


def captions(work: str, k: int) -> list[str]:
    _, a, b = (R if work == "ram" else M)[k]
    return [a[0], b[0]]


# work-chip icons: current, A, B (24x24 line icons, stroke = currentColor)
def _bow():
    return '<path d="M6 3.5C14 6 14 18 6 20.5"/><path d="M6 3.5V20.5" stroke-width="1"/><path d="M3.5 12H20"/><path d="M17 9l3 3-3 3"/><path d="M3.5 12l-1.5-1.5M3.5 12l-1.5 1.5"/>'
def _paduka():
    return ('<path d="M7.6 3.5C5.2 3.5 4.6 8 5 12.2C5.4 17 6 20 7.9 20C9.8 20 10.4 17 10.5 12.2C10.6 8 10.1 3.5 7.6 3.5Z"/>'
            '<path d="M16.4 3.5C18.8 3.5 19.4 8 19 12.2C18.6 17 18 20 16.1 20C14.2 20 13.6 17 13.5 12.2C13.4 8 13.9 3.5 16.4 3.5Z"/>'
            + dot(7.7, 7.4, 1.15) + dot(16.3, 7.4, 1.15) + '<path d="M2.5 22H21.5"/>')
def _chakra():
    sp = "".join(f'M12 12L{12+9*math.cos(math.radians(a)):.2f} {12+9*math.sin(math.radians(a)):.2f}' for a in range(0, 360, 30))
    te = "".join(f'M{12+9*math.cos(math.radians(a)):.2f} {12+9*math.sin(math.radians(a)):.2f}L{12+11.3*math.cos(math.radians(a+15)):.2f} {12+11.3*math.sin(math.radians(a+15)):.2f}L{12+9*math.cos(math.radians(a+30)):.2f} {12+9*math.sin(math.radians(a+30)):.2f}' for a in range(0, 360, 30))
    return f'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="2.2"/><path d="{sp}" stroke-width=".7"/><path d="{te}" stroke-width=".8"/>'
def _shankha():
    return ('<g transform="rotate(-30 12 12)"><path d="M12 1.6L7.3 7.9C5.5 10.9 6.1 15.4 9.4 18.7L12 22.2L14.6 18.7C17.9 15.4 18.5 10.9 16.7 7.9Z"/>'
            '<path d="M10.5 3.6Q12 3 13.5 3.6M9 5.7Q12 4.7 15 5.7M7.4 7.9Q12 6.6 16.6 7.9" stroke-width=".8"/>'
            '<path d="M16.7 9.4C20.6 10.6 20.8 15.2 15.4 17.8"/><path d="M12 8.6V19" stroke-width=".6"/></g>')
def _flute():
    holes = "".join(dot(3 + 18 * t, 20 - 14.8 * t, .55) for t in (0.4, 0.5, 0.6, 0.7))
    return ('<path d="M3 20L21 5.2" stroke-width="2.2"/>' + holes + '<path d="M9 22.4C10.4 16.6 12.6 12.4 15.6 8.6"/>'
            '<ellipse cx="17.6" cy="6.2" rx="3.6" ry="2.5" transform="rotate(-40 17.6 6.2)"/>'
            '<ellipse cx="17.7" cy="6.1" rx="1.7" ry="1.15" transform="rotate(-40 17.7 6.1)" fill="currentColor" stroke="none"/>')
def _setu_icon():
    return R[6][1][1]


def _pothi():   # palm-leaf manuscript: leaves with a cord through the holes
    return ('<path d="M3 8h18v8H3z"/><path d="M3 8l-1 2v4l1 2M21 8l1 2v4l-1 2" stroke-width="1.2"/>'
            '<path d="M7 11h4M7 13h6M14 11h3M15 13h2" stroke-width="1"/>' + dot(5.2, 12, .9) + dot(18.8, 12, .9) + '<path d="M5.2 12C5.2 6 18.8 6 18.8 12" stroke-width=".8"/>')
def _book():    # open book
    return '<path d="M12 6.5C9.5 4.8 6 4.5 3 5v13c3-.5 6.5-.2 9 1.5C14.5 17.8 18 17.5 21 18V5c-3-.5-6.5-.2-9 1.5z"/><path d="M12 6.5V19.5"/><path d="M6 8.5q2 0 4 .8M6 11.5q2 0 4 .8M14 9.3q2-.8 4-.8M14 12.3q2-.8 4-.8" stroke-width=".9"/>'
def _lekhani(): # stylus on a leaf
    return '<path d="M4 20l1.2-4.2L16.5 4.5a2 2 0 0 1 2.8 0l.2.2a2 2 0 0 1 0 2.8L8.2 18.8z"/><path d="M14.5 6.5l3 3M5.2 15.8l3 3" stroke-width="1.1"/><path d="M12 21h9" stroke-width="1.2"/>'


def _ratha():   # chariot wheel beside the Kapidhvaja banner (a pennant on its staff)
    sp = "".join(f'M9.5 15.5L{9.5+6*math.cos(math.radians(a)):.2f} {15.5+6*math.sin(math.radians(a)):.2f}' for a in range(0, 360, 45))
    return (f'<circle cx="9.5" cy="15.5" r="6"/><circle cx="9.5" cy="15.5" r="1.6"/><path d="{sp}" stroke-width=".8"/>'
            '<path d="M19 21.5V2.8"/><path d="M19 3.6L13.4 5.6l2 2.2-2 2.2L19 11.2" stroke-width="1.2"/><path d="M16.5 21.5h5" stroke-width="1.2"/>')
def _patra():   # leaves of a palm-leaf manuscript, stacked and slightly fanned, cord through the hole
    return ('<path d="M4.5 7.2L20.5 4.4v3L4.5 10.2z" stroke-width="1.1"/><path d="M4.5 10.2L20.5 7.4v3L4.5 13.2z" stroke-width="1.1"/>'
            '<path d="M3 13.6h18v6.4H3z"/><path d="M7 16.8h10" stroke-width=".9"/>' + dot(5.2, 16.8, .8) + dot(18.8, 16.8, .8))
def _dipa():    # oil lamp with its flame
    return ('<path d="M12 2.8c-2.4 2.6-2.4 5 0 7.6c2.4-2.6 2.4-5 0-7.6z"/><path d="M12 10.6v1.6" stroke-width="1"/>'
            '<path d="M3 12.8h14.5q0 5.2-7 5.2t-7.5-5.2z"/><path d="M17.5 13c1.6 0 3.2-.6 3.5-1.8" stroke-width="1.2"/><path d="M10.5 18v2.6M7 21.5h7" />')


def chip_icons(work: str) -> list[str]:
    fs = {"ram": [_bow, _paduka, _setu_icon], "app": [_pothi, _book, _lekhani], "gita": [_ratha, _patra, _dipa]}.get(work, [_chakra, _shankha, _flute])
    return [f'<svg class="wico" data-v="{i}" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{f()}</svg>'
            for i, f in enumerate(fs)]
