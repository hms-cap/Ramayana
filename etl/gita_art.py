"""Card art for the Bhagavadgītā: one card per adhyāya (1–18) and one for the Dhyāna ślokas (0).

card(n) returns the fields a home/read card needs: kb (card colour), kp (panel colour), svg (the painting,
data-v="0") and alts (two alternative paintings, data-v 1 and 2). Motifs only, no figures, drawn with the
same 24x24 line-icon vocabulary as etl/card_art.py.
"""
from __future__ import annotations

import card_art

# card / panel colours: warm saffron and earth tones, cycled
PAL = [("#6B3A10", "#97561C"), ("#5C2A1E", "#8A4130"), ("#4A3A12", "#75601F"),
       ("#2E4A3A", "#456F57"), ("#3B2E5C", "#594887"), ("#5A2440", "#863760")]

_WHEEL = card_art._chakra()
_SHANKHA = card_art._shankha()
_FLUTE = card_art._flute()
_LAMP = ('<path d="M5 15q7 5 14 0"/><path d="M5 15h14"/><path d="M12 15v4M8 21h8"/>'
         '<path d="M12 12c-2-2-1.5-5 0-8c1.5 3 2 6 0 8z"/>')
_LOTUS = ('<path d="M12 19c-3-3-3-8 0-12c3 4 3 9 0 12z"/><path d="M12 19c-5-.5-8-4-8-8c4 0 7 3 8 8z"/>'
          '<path d="M12 19c5-.5 8-4 8-8c-4 0-7 3-8 8z"/><path d="M4 21h16"/>')
_OM = ('<path d="M5 9.5c1-3 6-3 6 .5c0 2.5-3 3-4 3c2 0 5 .5 5 3.8c0 4-6 4.2-7.6 1.2"/>'
       '<path d="M12 13c1.6-3.2 6.5-2.6 6.5 1.5c0 3.4-2.8 4.6-4.5 4.5"/><path d="M14 6.5q2.5 1.4 5 0"/>'
       + card_art.dot(16.5, 3.6, .9))

# one motif per adhyāya, cycled through the set; adhyāya 0 (Dhyāna) gets the lamp
_MOTIFS = [_LAMP, _SHANKHA, _WHEEL, _LOTUS, _FLUTE, _OM]


def card(n: int) -> dict:
    kb, kp = PAL[n % len(PAL)]
    m = _MOTIFS[n % len(_MOTIFS)]
    a = _MOTIFS[(n + 2) % len(_MOTIFS)]
    b = _MOTIFS[(n + 4) % len(_MOTIFS)]
    return {"kb": kb, "kp": kp, "svg": card_art.card_svg(m, "A", 0),
            "alts": [card_art.card_svg(a, "B", 1), card_art.card_svg(b, "A", 2)]}
