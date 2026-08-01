#!/usr/bin/env python3
"""Genera header-mocha.svg e header-latte.svg: una sessione di terminale che si
digita da sola.

Come funziona l'animazione, perché non è ovvio:

- Niente JavaScript. GitHub sanifica l'HTML e comunque un SVG dentro un <img>
  non esegue script. Si usa SMIL, che i browser attuali supportano.
- La digitazione è un clip rettangolare che si allarga a scatti, uno per
  carattere (calcMode="discrete"). Il testo sotto è già tutto lì, colorato con
  i tspan: il clip decide quanto se ne vede.
- Ogni animazione dura quanto l'intero giro e si ripete all'infinito; i tempi
  dei singoli eventi stanno nei keyTimes. È l'unico modo per far ripartire in
  sincrono una sequenza con più elementi.
- Il giro comincia dallo stato finito, tenuto fermo per qualche secondo, e solo
  dopo pulisce e ridigita. Così il fotogramma a t=0 è il terminale completo:
  se un renderer non esegue SMIL — anteprime social, certi client di posta —
  quello che si vede è comunque una composizione sensata, non uno schermo vuoto.

    python3 gen_header.py
"""

from common import TEMI, blocco_font, esc, scrivi

# ---------------------------------------------------------------- contenuto

PROMPT = "antonio@github"
SEP = ":~$ "

# (comando digitato, righe di output)
SESSIONE = [
    ("whoami", ["Antonio Iovine, software engineer"]),
    ("cat focus.txt", ["systems / low-level / terminal tooling"]),
    ("ls projects/", ["dns-switcher   LC-3   LiteFTP   gotodo   TetrisTUI"]),
    ("status", ["open to work, based in Verona, Italy"]),
]

# ---------------------------------------------------------------- geometria

DIM = 14.5                     # dimensione del font
CAR = DIM * 0.6                # avanzamento di un carattere in IBM Plex Mono
INTERLINEA = 21.0
PAD_X, PAD_Y = 22.0, 16.0
BARRA = 32.0                   # altezza della barra del titolo
LARGH = 812.0

# ---------------------------------------------------------------- tempi (s)

T_CARATTERE = 0.055            # quanto ci mette un carattere a comparire
T_PAUSA_OUTPUT = 0.28          # dal comando alla sua risposta
T_DOPO_OUTPUT = 0.62           # dalla risposta al comando dopo
T_FERMO = 8.4                  # quanto resta fermo lo stato completo, a fine giro


def costruisci_scaletta():
    """Assegna a ogni riga la finestra temporale in cui compare.

    Restituisce (righe, totale). Il tempo 0 è l'inizio della pausa a schermo
    pieno; la digitazione comincia a T_FERMO.
    """
    righe, t = [], T_FERMO
    for indice, (comando, output) in enumerate(SESSIONE):
        n = len(PROMPT) + len(SEP) + len(comando)
        fine = t + len(comando) * T_CARATTERE
        righe.append({
            "tipo": "comando", "testo": comando, "caratteri": n,
            "inizio": t, "fine": fine,
        })
        t = fine + T_PAUSA_OUTPUT
        for riga in output:
            righe.append({"tipo": "output", "testo": riga, "inizio": t, "fine": t})
            t += 0.16
        if indice < len(SESSIONE) - 1:
            t += T_DOPO_OUTPUT

    # Il prompt vuoto in fondo, con l'unico cursore che lampeggia a riposo.
    # Senza questa riga ogni comando terrebbe acceso il proprio cursore durante
    # la pausa, e se ne vedrebbero quattro invece di uno.
    t += 0.30
    righe.append({"tipo": "prompt", "testo": "", "inizio": t, "fine": t})
    return righe, t + 0.45


def anim_clip(inizio, fine, caratteri, totale, prefisso_car):
    """Il clip che scopre un comando un carattere alla volta.

    Fuori dalla finestra di digitazione il clip è largo tutto: serve perché la
    riga resti leggibile sia nella pausa iniziale sia dopo essere stata scritta.
    """
    pieno = (prefisso_car + caratteri) * CAR + 4
    partenza = prefisso_car * CAR + 2      # il prompt c'è già, si digita dopo

    valori, tempi = [pieno, 0.0], [0.0, T_FERMO / totale]
    for i in range(caratteri + 1):
        valori.append(partenza + i * CAR)
        tempi.append((inizio + i * T_CARATTERE) / totale)
    valori.append(pieno)
    tempi.append(min(fine / totale, 0.999))
    valori.append(pieno)
    tempi.append(1.0)

    v = ";".join(f"{x:.1f}" for x in valori)
    k = ";".join(f"{x:.5f}" for x in tempi)
    return (f'<animate attributeName="width" calcMode="discrete" '
            f'values="{v}" keyTimes="{k}" dur="{totale:.2f}s" '
            f'repeatCount="indefinite"/>')


def anim_opacita(inizio, totale):
    """Comparsa netta di una riga di output, visibile anche nella pausa iniziale."""
    k = ";".join(["0", f"{T_FERMO / totale:.5f}",
                  f"{inizio / totale:.5f}", "1"])
    return (f'<animate attributeName="opacity" calcMode="discrete" '
            f'values="1;0;1;1" keyTimes="{k}" dur="{totale:.2f}s" '
            f'repeatCount="indefinite"/>')


def anim_cursore(inizio, fine, caratteri, totale, prefisso_car):
    """Il blocco che segue la posizione di scrittura di una riga di comando.

    Fuori dalla propria digitazione se ne sta fuori campo. In particolare resta
    nascosto durante la pausa a schermo pieno: lì l'unico cursore visibile deve
    essere quello del prompt finale, come in un terminale vero.
    """
    x0 = prefisso_car * CAR
    valori, tempi = [-100.0], [0.0]

    for i in range(caratteri + 1):
        valori.append(x0 + i * CAR)
        tempi.append((inizio + i * T_CARATTERE) / totale)

    valori.append(-100.0)                   # sparisce appena la riga è finita
    tempi.append(min((fine + 0.02) / totale, 0.998))
    valori.append(-100.0)
    tempi.append(1.0)

    v = ";".join(f"{x:.1f}" for x in valori)
    k = ";".join(f"{x:.5f}" for x in tempi)
    return (f'<animate attributeName="x" calcMode="discrete" '
            f'values="{v}" keyTimes="{k}" dur="{totale:.2f}s" '
            f'repeatCount="indefinite"/>')


def anim_lampeggio(inizio, totale, periodo=0.9):
    """Il lampeggio del cursore in fondo, acceso solo quando il prompt c'è.

    Visibile in due finestre: la pausa iniziale a schermo pieno, e dopo che
    l'ultimo output è comparso. Nel mezzo resta spento, perché in quel momento
    il prompt finale non è ancora stato stampato.
    """
    valori, tempi, t, acceso = [], [], 0.0, True
    while t < totale:
        visibile = (t < T_FERMO) or (t >= inizio)
        valori.append(1 if (visibile and acceso) else 0)
        tempi.append(t / totale)
        acceso = not acceso
        t += periodo / 2
    tempi[0] = 0.0
    # keyTimes deve chiudere esattamente a 1, altrimenti il browser scarta
    # l'animazione in silenzio e il cursore resta fisso
    valori.append(valori[-1])
    tempi.append(1.0)
    v = ";".join(str(x) for x in valori)
    k = ";".join(f"{x:.5f}" for x in tempi)
    return (f'<animate attributeName="opacity" calcMode="discrete" '
            f'values="{v}" keyTimes="{k}" dur="{totale:.2f}s" '
            f'repeatCount="indefinite"/>')


def genera(tema):
    righe, totale = costruisci_scaletta()
    alt = BARRA + PAD_Y * 2 + len(righe) * INTERLINEA + 6

    p = tema
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {LARGH:.0f} {alt:.0f}" '
        f'width="{LARGH:.0f}" height="{alt:.0f}" role="img" '
        f'aria-label="Sessione di terminale: whoami, focus, progetti, stato">',
        blocco_font(),
        f'<rect width="{LARGH:.0f}" height="{alt:.0f}" rx="10" fill="{p["base"]}"/>',
        f'<rect width="{LARGH:.0f}" height="{BARRA:.0f}" rx="10" fill="{p["mantle"]}"/>',
        f'<rect y="{BARRA - 10:.0f}" width="{LARGH:.0f}" height="10" fill="{p["mantle"]}"/>',
        f'<line x1="0" y1="{BARRA:.0f}" x2="{LARGH:.0f}" y2="{BARRA:.0f}" '
        f'stroke="{p["surface0"]}" stroke-width="1"/>',
    ]
    for i, colore in enumerate((p["red"], p["yellow"], p["green"])):
        out.append(f'<circle cx="{20 + i * 18}" cy="{BARRA / 2:.0f}" r="5.5" fill="{colore}"/>')
    out.append(
        f'<text x="{LARGH / 2:.0f}" y="{BARRA / 2 + 4.5:.0f}" text-anchor="middle" '
        f'font-size="12" fill="{p["overlay0"]}">antonio@github</text>')

    prefisso = len(PROMPT) + len(SEP)

    for idx, riga in enumerate(righe):
        y = BARRA + PAD_Y + INTERLINEA * (idx + 1) - 6

        if riga["tipo"] == "comando":
            cid = f"c{idx}"
            # width e opacity partono già dallo stato completo: se un renderer
            # ignora SMIL, quello che resta è il terminale pieno, non uno vuoto
            pieno = (prefisso + len(riga["testo"])) * CAR + 4
            out.append(
                f'<clipPath id="{cid}"><rect x="{PAD_X:.0f}" y="{y - DIM:.1f}" '
                f'height="{DIM + 8:.1f}" width="{pieno:.1f}">'
                + anim_clip(riga["inizio"], riga["fine"], len(riga["testo"]),
                            totale, prefisso)
                + '</rect></clipPath>')
            out.append(
                f'<g clip-path="url(#{cid})">'
                f'<text xml:space="preserve" x="{PAD_X:.0f}" y="{y:.1f}" font-size="{DIM}">'
                f'<tspan fill="{p["green"]}">{PROMPT}</tspan>'
                f'<tspan fill="{p["overlay0"]}">{esc(SEP)}</tspan>'
                f'<tspan fill="{p["text"]}">{esc(riga["testo"])}</tspan>'
                f'</text></g>')
            out.append(
                f'<rect x="-100" y="{y - DIM + 2:.1f}" width="{CAR:.1f}" '
                f'height="{DIM + 2:.1f}" fill="{p["lavender"]}" opacity="0.85" '
                f'transform="translate({PAD_X:.0f},0)">'
                + anim_cursore(riga["inizio"], riga["fine"], len(riga["testo"]),
                               totale, prefisso)
                + '</rect>')
        elif riga["tipo"] == "prompt":
            # il prompt vuoto che resta in fondo, con l'unico cursore lampeggiante
            out.append(
                f'<text xml:space="preserve" x="{PAD_X:.0f}" y="{y:.1f}" '
                f'font-size="{DIM}" opacity="1">'
                + anim_opacita(riga["inizio"], totale)
                + f'<tspan fill="{p["green"]}">{PROMPT}</tspan>'
                + f'<tspan fill="{p["overlay0"]}">{esc(SEP)}</tspan>'
                + '</text>')
            out.append(
                f'<rect x="{PAD_X + prefisso * CAR:.1f}" y="{y - DIM + 2:.1f}" '
                f'width="{CAR:.1f}" height="{DIM + 2:.1f}" fill="{p["lavender"]}" '
                f'opacity="1">'
                + anim_lampeggio(riga["inizio"], totale)
                + '</rect>')

        else:
            out.append(
                f'<text xml:space="preserve" x="{PAD_X:.0f}" y="{y:.1f}" font-size="{DIM}" '
                f'fill="{p["subtext0"]}" opacity="1">'
                + anim_opacita(riga["inizio"], totale)
                + esc(riga["testo"]) + '</text>')

    out.append("</svg>")
    return "".join(out), totale


if __name__ == "__main__":
    for tema in TEMI:
        svg, totale = genera(tema)
        dest = scrivi("header", tema, svg)
        print(f"{dest.name:22} {len(svg) / 1024:5.1f} KB   giro da {totale:.1f}s")
