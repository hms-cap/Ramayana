"""Temple-painting (Tanjore-style) niche cards for the 18 parvas: symbols only, no figures.

svg(n) -> inline SVG string for parva n. Colours follow the kāṇḍa cards (gold line, deep panel).
"""
G="#F0C45A"; I="#FFF1CF"
PAL=[("#5A1F2B","#7E3042"),("#1F3A66","#2F5A96"),("#1B4D33","#2C7048"),("#6B3A14","#92561F"),("#0D4E60","#1B7A90"),("#4B2A66","#6D429A")]
_NAMES=[("ಆದಿಪರ್ವ","Ādi Parva"),("ಸಭಾಪರ್ವ","Sabhā Parva"),("ವನಪರ್ವ","Vana Parva"),("ವಿರಾಟಪರ್ವ","Virāṭa Parva"),("ಉದ್ಯೋಗಪರ್ವ","Udyoga Parva"),("ಭೀಷ್ಮಪರ್ವ","Bhīṣma Parva"),("ದ್ರೋಣಪರ್ವ","Droṇa Parva"),("ಕರ್ಣಪರ್ವ","Karṇa Parva"),("ಶಲ್ಯಪರ್ವ","Śalya Parva"),("ಸೌಪ್ತಿಕಪರ್ವ","Sauptika Parva"),("ಸ್ತ್ರೀಪರ್ವ","Strī Parva"),("ಶಾಂತಿಪರ್ವ","Śānti Parva"),("ಅನುಶಾಸನಪರ್ವ","Anuśāsana Parva"),("ಆಶ್ವಮೇಧಿಕಪರ್ವ","Āśvamedhika Parva"),("ಆಶ್ರಮವಾಸಿಕಪರ್ವ","Āśramavāsika Parva"),("ಮೌಸಲಪರ್ವ","Mausala Parva"),("ಮಹಾಪ್ರಸ್ಥಾನಿಕಪರ್ವ","Mahāprasthānika Parva"),("ಸ್ವರ್ಗಾರೋಹಣಪರ್ವ","Svargārohaṇa Parva")]
KN="೧೨೩೪೫೬೭೮೯"
def kn(n): return "".join("೦೧೨೩೪೫೬೭೮೯"[int(c)] for c in str(n))
W="M24 106q9-6 18 0t18 0t18 0t18 0t18 0t18 0"
def motif(n,dk):
    m={
1:f'<ellipse cx="78" cy="84" rx="26" ry="14" fill="{I}"/><path d="M98 78Q116 70 108 52Q104 42 94 46"/><circle cx="94" cy="46" r="5" fill="{I}"/><path d="M89 46L82 49"/><path d="M60 82Q74 68 92 82" stroke="{dk}"/><path d="{W}"/>',
2:f'<rect x="46" y="62" width="30" height="30" rx="5" fill="{G}" transform="rotate(-12 61 77)"/><rect x="86" y="54" width="30" height="30" rx="5" fill="{I}" transform="rotate(10 101 69)"/><g fill="{dk}" stroke="none"><circle cx="54" cy="70" r="2.4"/><circle cx="68" cy="84" r="2.4"/><circle cx="61" cy="77" r="2.4"/><circle cx="94" cy="62" r="2.4"/><circle cx="108" cy="62" r="2.4"/><circle cx="94" cy="76" r="2.4"/><circle cx="108" cy="76" r="2.4"/></g><path d="M40 108H120"/>',
3:f'<path d="M34 108V84"/><circle cx="34" cy="74" r="12" fill="#3B8B5C"/><path d="M122 108V82"/><circle cx="122" cy="72" r="13" fill="#3B8B5C"/><path d="M78 108V90"/><circle cx="78" cy="82" r="9" fill="#3B8B5C"/><path d="M92 34A16 16 0 1 0 92 66A12 12 0 1 1 92 34Z" fill="{G}" stroke="none"/>',
4:f'<path d="M80 108V70"/><circle cx="80" cy="56" r="20" fill="#3B8B5C"/><path d="M60 66L100 48" stroke-width="4"/><path d="M66 70L94 44M72 74L104 52" stroke="{I}" stroke-width="1.4"/><path d="M52 108H108"/>',
5:f'<path d="M46 88Q38 62 68 54Q100 46 112 68Q120 86 100 96Q80 106 62 96Z" fill="{I}"/><path d="M68 72Q90 62 98 78Q100 88 86 90" stroke="{dk}"/><path d="M112 68L126 58" stroke-width="3"/><path d="M30 108H130"/>',
6:f'<path d="M80 102L38 62M80 102L58 50M80 102V46M80 102L102 50M80 102L122 62"/><g fill="{G}" stroke="none"><circle cx="38" cy="62" r="3"/><circle cx="58" cy="50" r="3"/><circle cx="80" cy="46" r="3"/><circle cx="102" cy="50" r="3"/><circle cx="122" cy="62" r="3"/></g><path d="M30 108H130"/>',
7:f'<circle cx="80" cy="72" r="34" stroke-dasharray="10 5"/><circle cx="80" cy="72" r="24" stroke-dasharray="7 5"/><circle cx="80" cy="72" r="14" stroke-dasharray="5 4"/><circle cx="80" cy="72" r="5" fill="{G}"/>',
8:f'<circle cx="80" cy="92" r="28" fill="{G}"/><circle cx="80" cy="92" r="6" fill="{dk}"/><path d="M80 64V120M52 92H108M60 72L100 112M100 72L60 112" stroke="{dk}" stroke-width="1.6"/><rect x="30" y="100" width="100" height="14" fill="{dk}" stroke="none"/><path d="M30 100H130"/><circle cx="118" cy="40" r="7" fill="{G}" stroke="none"/>',
9:f'<path d="M80 108V60" stroke-width="5"/><circle cx="80" cy="46" r="15" fill="{G}"/><g fill="{dk}" stroke="none"><circle cx="72" cy="42" r="2"/><circle cx="88" cy="42" r="2"/><circle cx="80" cy="54" r="2"/><circle cx="80" cy="38" r="2"/></g><path d="M80 31V22"/><path d="M62 108H98"/>',
10:f'<path d="M92 36A24 24 0 1 0 92 84A18 18 0 1 1 92 36Z" fill="{G}" stroke="none"/><g fill="{I}" stroke="none"><circle cx="112" cy="44" r="2.4"/><circle cx="122" cy="62" r="2"/><circle cx="104" cy="76" r="2"/><circle cx="40" cy="48" r="2"/></g><ellipse cx="80" cy="104" rx="14" ry="5" fill="{I}"/><path d="M80 99C74 92 78 88 80 82C82 88 86 92 80 99Z" fill="{G}" stroke="none"/>',
11:f'<path d="M80 100C66 90 64 70 80 52C96 70 94 90 80 100Z" fill="{I}"/><path d="M80 100C64 100 54 88 54 76C68 76 78 86 80 100Z" fill="#FFE6A8"/><path d="M80 100C96 100 106 88 106 76C92 76 82 86 80 100Z" fill="#FFE6A8"/><g fill="{G}" stroke="none"><path d="M36 44Q40 52 36 56Q32 52 36 44Z"/><path d="M124 56Q128 64 124 68Q120 64 124 56Z"/><path d="M118 36Q121 41 118 44Q115 41 118 36Z"/></g>',
12:f'<path d="M42 68Q80 22 118 68Z" fill="{I}"/><path d="M42 68q9 8 19 0t19 0t19 0t19 0" fill="{G}"/><path d="M80 24V18M80 76V104"/><path d="M62 106H98"/>',
13:f'<rect x="38" y="52" width="84" height="44" rx="5" fill="{I}"/><path d="M48 66H112M48 76H112M48 86H96" stroke="{dk}" stroke-width="1.4"/><circle cx="46" cy="74" r="0"/><path d="M60 52V46M100 52V46"/>',
14:f'<path d="M80 36C64 54 62 66 72 76C74 68 80 64 80 64C80 64 86 68 88 76C98 66 96 54 80 36Z" fill="{G}"/><path d="M80 52C74 62 74 68 80 72C86 68 86 62 80 52Z" fill="{I}" stroke="none"/><rect x="52" y="86" width="56" height="10" fill="{I}"/><rect x="42" y="96" width="76" height="10" fill="{I}"/>',
15:f'<path d="M44 76L80 48L116 76Z" fill="{G}"/><rect x="54" y="76" width="52" height="30" fill="{I}"/><path d="M74 106V90a6 6 0 0 1 12 0v16" fill="{dk}"/><path d="M30 108V92"/><circle cx="30" cy="84" r="8" fill="#3B8B5C"/>',
16:f'<path d="M50 104V60M80 104V48M110 104V62"/><path d="M50 60Q44 54 40 48M50 60Q56 54 60 48M80 48Q74 40 70 34M80 48Q86 40 90 34M110 62Q104 56 100 50M110 62Q116 56 120 50"/><path d="{W}"/>',
17:f'<path d="M24 108L62 56L84 84L104 50L136 108Z" fill="{I}" opacity=".9"/><path d="M70 108Q84 96 70 88Q56 80 74 70" stroke="{dk}" stroke-width="2"/><path d="M118 108V80" stroke-width="3"/>',
18:f'<rect x="34" y="94" width="92" height="12" fill="{I}"/><rect x="48" y="82" width="64" height="12" fill="{I}"/><rect x="62" y="70" width="36" height="12" fill="{I}"/><circle cx="80" cy="46" r="14" fill="{G}" stroke="none"/><path d="M80 26V20M96 32L100 28M64 32L60 28M104 46H110M56 46H50"/>',
    }
    return m[n]
def art(n,w="100%",h=124):
    bg,pn=PAL[(n-1)%6]; dk=bg
    return f'<svg viewBox="0 0 160 120" width="{w}" height="{h}" fill="none" stroke="{G}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 120V58Q12 40 40 32Q70 24 80 6Q90 24 120 32Q148 40 148 58V120Z" fill="{pn}"/><path d="M20 120V60Q20 46 44 39Q72 31 80 16Q88 31 116 39Q140 46 140 60V120Z" stroke-width="1" opacity=".6"/><circle cx="80" cy="3.5" r="2.5" fill="{G}" stroke="none"/>{motif(n,dk)}</svg>'


PALETTE = PAL


def svg(n: int) -> str:
    """Inline SVG for parva n; sized by CSS (class kart)."""
    return art(n).replace('width="100%" height="124" ', 'class="kart" ')
