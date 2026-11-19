"""Helpers for turning raw directory rows into roster lines (used for the Central build, 18 Oct 2026).

unit("#B2-27-28") -> "#B2-27/28";  unit("#03-65-TO-66") -> "#03-65–66";  unit("#01-34B--01-53") -> "#01-34B & #01-53"
clean("HOE NAM PRAWN NOODLES 河南大虾面") -> "Hoe Nam Prawn Noodles"  (drops CJK duplicates and "(Temporarily Closed)" etc.)
CapitaLand units arrive as tags like ".../tenant-unit-numbers/funan/b2-k05": take the last path part, strip "unit-", upper-case, prefix "#".
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
from speclib import title_if_caps
def unit(u):
    u = u.strip()
    if not u or u == '#': return ''
    u = u.replace('-TO-', '–').replace('TO', '–') if re.search(r'\dTO\d|-TO-', u) else u
    parts = []
    for seg in re.split(r'\s*&\s*|--', u.lstrip('#')):
        seg = seg.strip('#- ').strip()
        if not seg: continue
        m = re.match(r'^(B\d|\d\d|M\d\d)-(.+)$', seg)
        if m:
            fl, rest = m.groups()
            bits = [b for b in rest.split('-') if b]
            if all(re.fullmatch(r'K?\d+[A-Z]?|–', b) for b in bits): rest = '/'.join(bits).replace('/–/', '–')
            seg = f'{fl}-{rest}'
        parts.append('#' + seg)
    return ' & '.join(parts)
def clean(n):
    n = re.sub(r'\s*\((Temporarily Closed|Coming Soon|Opening Soon)\)', '', n, flags=re.I)
    n = re.sub(r'[　-鿿＀-￯]+', '', n).strip()  # drop CJK duplicates of the English name
    n = re.sub(r'\s*\(\s*\)', '', n).replace('’', "'").replace('®', '').replace('™', '')
    n = re.sub(r'\s+', ' ', n).strip(' -/')
    return title_if_caps(n)
