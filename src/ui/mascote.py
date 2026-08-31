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


# Ícone da marca (assets/icons_with_headset/icone-gems-finder-sem-borda.svg):
# a Pepita de headset sem moldura nem fundo, pra assentar em qualquer cor.
# Embutido inline porque o Streamlit não serve arquivos locais via <img src="...">.
LOGO = (
    '<svg class="gf-logo" width="41" height="46" viewBox="-7 15 70 79" '
    'role="img" aria-label="Gems Finder">'
    '<path d="M2 46C2 14 54 14 54 46" fill="none" stroke="#141414" '
    'stroke-width="7" stroke-linecap="round"/>'
    '<rect x="-4" y="40" width="13" height="26" rx="6.5" fill="#141414"/>'
    '<rect x="47" y="40" width="13" height="26" rx="6.5" fill="#141414"/>'
    '<path d="M13 74c-5 2-6 6-5 9M43 74c5 2 6 6 5 9" stroke="#141414" '
    'stroke-width="2.6" fill="none" stroke-linecap="round"/>'
    '<circle cx="8" cy="84" r="3.2" fill="#141414"/>'
    '<circle cx="48" cy="84" r="3.2" fill="#141414"/>'
    '<path d="M28 38 10 50l5 32h26l5-32L28 38z" fill="#CFF25E" stroke="#141414" '
    'stroke-width="2.8" stroke-linejoin="round"/>'
    '<path d="M28 38 10 50h36L28 38z" fill="#E4F8A8" stroke="#141414" '
    'stroke-width="1.9" stroke-linejoin="round"/>'
    '<circle cx="21" cy="60" r="2.7" fill="#141414"/>'
    '<circle cx="35" cy="60" r="2.7" fill="#141414"/>'
    '<path d="M21 67c4 5 10 5 14 0" stroke="#141414" stroke-width="2.3" '
    'fill="none" stroke-linecap="round"/>'
    '<path d="M23 82v6M33 82v6" stroke="#141414" stroke-width="2.4" '
    'stroke-linecap="round"/>'
    '<path d="M18.5 89h8M30.5 89h8" stroke="#141414" stroke-width="2.6" '
    'stroke-linecap="round"/>'
    '</svg>'
)
