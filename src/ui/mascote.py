"""Pepita, a mascote-gema do Gems Finder — SVG inline traduzido do protótipo.

Expressões disponíveis: feliz, foco, treino, chill e triste (neutra/pensativa,
nunca brava). A Pepita é a voz do app nos avisos e feedbacks.
"""

from __future__ import annotations

_OLHOS: dict[str, str] = {
    "foco": (
        '<circle class="eye" cx="21" cy="30" r="2.6" fill="#141414"/>'
        '<circle class="eye b" cx="35" cy="30" r="2.6" fill="#141414"/>'
        '<path d="M15 25.5h12M29 25.5h12" stroke="#141414" stroke-width="2" stroke-linecap="round"/>'
    ),
    "treino": (
        '<circle class="eye" cx="21" cy="29" r="3.4" fill="#141414"/>'
        '<circle class="eye b" cx="35" cy="29" r="3.4" fill="#141414"/>'
    ),
    "chill": (
        '<path d="M17 30c2-3 6-3 8 0M31 30c2-3 6-3 8 0" stroke="#141414" '
        'stroke-width="2.2" fill="none" stroke-linecap="round"/>'
    ),
    "triste": (
        '<circle class="eye" cx="21" cy="31" r="2.8" fill="#141414"/>'
        '<circle class="eye b" cx="35" cy="31" r="2.8" fill="#141414"/>'
        '<path d="M17 25.8c2.2-1.4 5-1.4 7.2.6M39 25.8c-2.2-1.4-5-1.4-7.2.6" '
        'stroke="#141414" stroke-width="1.9" fill="none" stroke-linecap="round"/>'
    ),
    "feliz": (
        '<circle class="eye" cx="21" cy="29" r="2.8" fill="#141414"/>'
        '<circle class="eye b" cx="35" cy="29" r="2.8" fill="#141414"/>'
    ),
}

_BOCA: dict[str, str] = {
    "foco": '<path d="M23 39h10" stroke="#141414" stroke-width="2.2" stroke-linecap="round"/>',
    "treino": '<ellipse cx="28" cy="39" rx="5" ry="6" fill="#141414"/>',
    "chill": ('<path d="M22 37c3 4 9 4 12 0" stroke="#141414" stroke-width="2.2" '
              'fill="none" stroke-linecap="round"/>'),
    "triste": ('<path d="M24 39.5h8" stroke="#141414" stroke-width="2.2" fill="none" '
               'stroke-linecap="round"/>'),
    "feliz": ('<path d="M21 37c4 5 10 5 14 0" stroke="#141414" stroke-width="2.2" '
              'fill="none" stroke-linecap="round"/>'),
}

_BRACOS_TREINO = (
    '<path d="M9 34 2 22M47 34l7-12" stroke="#141414" stroke-width="2.2" stroke-linecap="round"/>'
    '<circle cx="2" cy="21" r="3" fill="#141414"/><circle cx="54" cy="21" r="3" fill="#141414"/>'
)
_BRACOS_PADRAO = (
    '<path d="M9 38c-5 2-6 6-5 9M47 38c5 2 6 6 5 9" stroke="#141414" stroke-width="2.2" '
    'fill="none" stroke-linecap="round"/>'
    '<circle cx="4" cy="48" r="3" fill="#141414"/><circle cx="52" cy="48" r="3" fill="#141414"/>'
)


def mascote(cor: str, humor: str = "feliz", tamanho: int = 64) -> str:
    """SVG inline da Pepita. Humores: feliz, foco, treino, chill e triste."""
    bracos = _BRACOS_TREINO if humor == "treino" else _BRACOS_PADRAO
    return (
        f'<svg class="gf-mascote" width="{tamanho}" height="{round(tamanho * 1.15)}" '
        'viewBox="-4 0 64 66" aria-hidden="true">'
        f'{bracos}'
        f'<path d="M28 4 8 17l6 34h28l6-34L28 4z" fill="{cor}" stroke="#141414" '
        'stroke-width="2.4" stroke-linejoin="round"/>'
        '<path d="M28 4 8 17h40L28 4z" fill="#fff" fill-opacity=".35" stroke="#141414" '
        'stroke-width="1.6" stroke-linejoin="round"/>'
        f'{_OLHOS.get(humor, "")}{_BOCA.get(humor, "")}'
        '<path d="M20 55v6M36 55v6" stroke="#141414" stroke-width="2.2" stroke-linecap="round"/>'
        '<path d="M15 62h9M32 62h9" stroke="#141414" stroke-width="2.4" stroke-linecap="round"/>'
        '</svg>'
    )


LOGO = (
    '<svg width="34" height="38" viewBox="0 0 34 38" aria-hidden="true">'
    '<path d="M17 2 4 12l13 24 13-24L17 2z" fill="#CFF25E" stroke="#141414" '
    'stroke-width="2" stroke-linejoin="round"/>'
    '<circle cx="13" cy="17" r="1.9" fill="#141414"/>'
    '<circle cx="21" cy="17" r="1.9" fill="#141414"/>'
    '<path d="M13.5 22c1.8 2 5.2 2 7 0" stroke="#141414" stroke-width="1.8" '
    'fill="none" stroke-linecap="round"/></svg>'
)
