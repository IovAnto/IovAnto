"""Pezzi condivisi dai generatori di SVG del profilo.

Ogni asset esiste in due varianti, Catppuccin Mocha per il tema scuro di GitHub e
Latte per quello chiaro. Il README le seleziona con <picture>.

Il font va incorporato come data URI: un SVG mostrato dentro un <img> non può
scaricare risorse esterne, quindi un @font-face che punta a un URL verrebbe
ignorato in silenzio e il testo cadrebbe sul monospace di sistema, con
allineamenti diversi su ogni macchina. Il sottoinsieme in tools/ contiene i soli
ASCII stampabili, che è tutto ciò che scriviamo: 7 KB invece di 14.
"""

import base64
import pathlib

QUI = pathlib.Path(__file__).resolve().parent
ASSETS = QUI.parent / "assets"

# Catppuccin, https://github.com/catppuccin/catppuccin — licenza MIT
MOCHA = {
    "nome": "mocha",
    "base": "#1e1e2e", "mantle": "#181825", "crust": "#11111b",
    "surface0": "#313244", "surface1": "#45475a", "surface2": "#585b70",
    "overlay0": "#6c7086",
    "text": "#cdd6f4", "subtext0": "#a6adc8", "subtext1": "#bac2de",
    "green": "#a6e3a1", "teal": "#94e2d5", "blue": "#89b4fa",
    "mauve": "#cba6f7", "peach": "#fab387", "yellow": "#f9e2af",
    "red": "#f38ba8", "pink": "#f5c2e7", "lavender": "#b4befe",
}

LATTE = {
    "nome": "latte",
    "base": "#eff1f5", "mantle": "#e6e9ef", "crust": "#dce0e8",
    "surface0": "#ccd0da", "surface1": "#bcc0cc", "surface2": "#acb0be",
    "overlay0": "#9ca0b0",
    "text": "#4c4f69", "subtext0": "#6c6f85", "subtext1": "#5c5f77",
    "green": "#40a02b", "teal": "#179299", "blue": "#1e66f5",
    "mauve": "#8839ef", "peach": "#fe640b", "yellow": "#df8e1d",
    "red": "#d20f39", "pink": "#ea76cb", "lavender": "#7287fd",
}

TEMI = (MOCHA, LATTE)

# IBM Plex Mono, SIL Open Font License 1.1
_FONT = QUI / "plex-mono-subset.woff2"


def blocco_font() -> str:
    """Il <style> con il font incorporato, da mettere dentro ogni SVG."""
    b64 = base64.b64encode(_FONT.read_bytes()).decode("ascii")
    return (
        "<style>"
        "@font-face{font-family:'PlexM';font-style:normal;font-weight:400;"
        f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}"
        "text{font-family:'PlexM',ui-monospace,'DejaVu Sans Mono',monospace;"
        "white-space:pre}"
        "</style>"
    )


def scrivi(nome_base: str, tema: dict, svg: str) -> pathlib.Path:
    ASSETS.mkdir(parents=True, exist_ok=True)
    dest = ASSETS / f"{nome_base}-{tema['nome']}.svg"
    dest.write_text(svg, encoding="utf-8")
    return dest


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# Larghezza di un carattere a font-size 1: IBM Plex Mono avanza di 600/1000 em.
AVANZAMENTO = 0.6


def larghezza_testo(n_caratteri: int, dimensione: float) -> float:
    return n_caratteri * dimensione * AVANZAMENTO
