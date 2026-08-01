#!/usr/bin/env python3
"""Genera stats-mocha.svg e stats-latte.svg: un pannello in stile neofetch con
dati veri presi dall'API di GitHub.

Non è una stats card di terze parti: i dati li legge e li disegna questo file.
Nessun servizio esterno vede il profilo, e il risultato è un file statico nel
repo, che GitHub serve senza dipendere da nessuno.

Se l'API non risponde o restituisce dati incompleti lo script esce con codice 1
SENZA scrivere niente: sul profilo resta l'ultima immagine buona. È il motivo
per cui il workflow non ha `continue-on-error`, e non deve averlo — un fallimento
rumoroso è preferibile a un pannello che mostra zeri.

    GITHUB_TOKEN=... python3 gen_stats.py [utente]
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

from common import ASSETS, TEMI, blocco_font, esc, scrivi

UTENTE = sys.argv[1] if len(sys.argv) > 1 else "IovAnto"
API = "https://api.github.com"

# Il nome mostrato nell'intestazione del pannello. Sta separato dall'account
# interrogato perché l'intestazione del terminale dice "antonio@github": due
# stringhe diverse per la stessa persona si leggerebbero come una svista.
NOME_MOSTRATO = "antonio"

LARGH, ALT = 812.0, 312.0

# I linguaggi che ci interessa distinguere; il resto finisce in "other".
COLORI_LINGUAGGI = {
    "Rust": "peach", "C": "blue", "Python": "yellow", "Go": "teal",
    "Java": "red", "SystemVerilog": "green", "Shell": "subtext1",
    "C++": "lavender", "JavaScript": "pink", "Assembly": "mauve",
}

# Formati di documento e di build che GitHub conta come "linguaggi". Restano
# fuori dalla ripartizione perché non dicono niente su cosa uno sa programmare:
# le relazioni universitarie in LaTeX pesano più del codice che le accompagna.
# L'esclusione è dichiarata sotto la barra, non nascosta.
NON_CODICE = {"TeX", "Makefile", "HTML", "CSS", "Dockerfile", "Roff", "Batchfile"}


def chiama(percorso):
    req = urllib.request.Request(
        f"{API}{percorso}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{UTENTE}-profile-stats",
        },
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)


def raccogli():
    """Legge i dati. Solleva un'eccezione se qualcosa non torna: chi chiama
    deve poter distinguere 'API muta' da 'utente senza repo'."""
    utente = chiama(f"/users/{UTENTE}")
    repos = []
    pagina = 1
    while True:
        lotto = chiama(f"/users/{UTENTE}/repos?per_page=100&page={pagina}&type=owner")
        repos.extend(lotto)
        if len(lotto) < 100:
            break
        pagina += 1

    propri = [r for r in repos if not r["fork"] and not r["private"]]
    if not propri:
        raise RuntimeError("nessun repo pubblico non-fork: mi rifiuto di scrivere zeri")

    byte_per_lingua, release_totali = {}, 0
    for r in propri:
        for lingua, byte in chiama(f"/repos/{UTENTE}/{r['name']}/languages").items():
            if lingua in NON_CODICE:
                continue
            byte_per_lingua[lingua] = byte_per_lingua.get(lingua, 0) + byte
        release_totali += len(chiama(f"/repos/{UTENTE}/{r['name']}/releases?per_page=100"))

    if not byte_per_lingua:
        raise RuntimeError("nessun linguaggio rilevato")

    # Il repo del profilo va escluso da "Latest": questo script ci committa
    # dentro ogni notte, quindi sarebbe sempre lui il più recente e il campo
    # non direbbe mai niente.
    candidati = [r for r in propri if r["name"].lower() != UTENTE.lower()]
    recente = max(candidati or propri, key=lambda r: r["pushed_at"])
    stelle = sum(r["stargazers_count"] for r in propri)

    return {
        "repo": len(propri),
        "release": release_totali,
        "stelle": stelle,
        "lingue": byte_per_lingua,
        "recente": recente["name"],
        "recente_quando": recente["pushed_at"][:10],
        "dal": utente["created_at"][:4],
        "aggiornato": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


def ripartizione(byte_per_lingua, quante=6):
    totale = sum(byte_per_lingua.values())
    ordinate = sorted(byte_per_lingua.items(), key=lambda kv: -kv[1])
    principali = ordinate[:quante]
    resto = sum(b for _, b in ordinate[quante:])
    voci = [(n, b / totale * 100) for n, b in principali]
    if resto:
        voci.append(("other", resto / totale * 100))
    return voci


def logo_github(x, y, colore, lato=94.0):
    """Il segno di GitHub, dalla sagoma di Octicons (MIT).

    Ha più senso del grafo di git per questo pannello: stelle e release sono
    concetti di GitHub, in git non esistono. Il segno è un marchio di GitHub,
    che ne consente l'uso per identificare e linkare GitHub — che è appunto
    quello che fa qui.
    """
    scala = lato / 24.0
    d = ("M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 "
         "0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 "
         "3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 "
         "1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 "
         "0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 "
         "1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 "
         "2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 "
         "2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 "
         "12.297c0-6.627-5.373-12-12-12")
    return (f'<path transform="translate({x},{y}) scale({scala:.4f})" '
            f'fill="{colore}" opacity="0.92" d="{d}"/>')


def genera(tema, d):
    p = tema
    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {LARGH:.0f} {ALT:.0f}" '
        f'width="{LARGH:.0f}" height="{ALT:.0f}" role="img" '
        f'aria-label="Riepilogo GitHub di {esc(UTENTE)}: {d["repo"]} repository pubblici, '
        f'{d["release"]} release, linguaggio principale {esc(ripartizione(d["lingue"])[0][0])}">',
        blocco_font(),
        f'<rect width="{LARGH:.0f}" height="{ALT:.0f}" rx="10" fill="{p["base"]}"/>',
        logo_github(64, 105, p["peach"]),
    ]

    sx = 210.0
    o.append(f'<text x="{sx}" y="58" font-size="15" fill="{p["green"]}">'
             f'{esc(NOME_MOSTRATO)}<tspan fill="{p["overlay0"]}">@</tspan>'
             f'<tspan fill="{p["blue"]}">github</tspan></text>')
    o.append(f'<line x1="{sx}" y1="68" x2="{LARGH - 48:.0f}" y2="68" '
             f'stroke="{p["surface1"]}" stroke-width="1"/>')

    righe = [
        ("Repos", f'{d["repo"]} public'),
        ("Releases", f'{d["release"]} shipped'),
        ("Stars", f'{d["stelle"]}'),
        ("Latest", f'{d["recente"]}  ({d["recente_quando"]})'),
        ("Member since", d["dal"]),
    ]
    y = 92
    for chiave, valore in righe:
        o.append(f'<text x="{sx}" y="{y}" font-size="13" fill="{p["subtext0"]}">'
                 f'{esc(chiave)}</text>')
        o.append(f'<text x="{sx + 150:.0f}" y="{y}" font-size="13" fill="{p["text"]}">'
                 f'{esc(valore)}</text>')
        y += 23

    # barra dei linguaggi, proporzionale ai byte veri
    voci = ripartizione(d["lingue"])
    bx, by, bw, bh = sx, 218.0, LARGH - sx - 48, 12.0
    o.append(f'<text x="{bx}" y="{by - 10:.0f}" font-size="11" fill="{p["overlay0"]}">'
             f'languages by bytes</text>')
    o.append(f'<clipPath id="barra"><rect x="{bx}" y="{by}" width="{bw:.1f}" '
             f'height="{bh}" rx="6"/></clipPath>')
    cur = bx
    for nome, quota in voci:
        w = bw * quota / 100
        colore = p[COLORI_LINGUAGGI.get(nome, "surface2")]
        o.append(f'<rect clip-path="url(#barra)" x="{cur:.2f}" y="{by}" '
                 f'width="{w:.2f}" height="{bh}" fill="{colore}"/>')
        cur += w

    # legenda, che va a capo invece di sbordare
    lx, ly = bx, by + 34
    limite = bx + bw
    for nome, quota in voci:
        etichetta = f"{nome} {quota:.0f}%"
        larghezza = 14 + len(etichetta) * 11 * 0.6 + 20
        if lx + larghezza > limite:
            lx, ly = bx, ly + 19
        colore = p[COLORI_LINGUAGGI.get(nome, "surface2")]
        o.append(f'<circle cx="{lx + 4:.1f}" cy="{ly - 4:.1f}" r="4" fill="{colore}"/>')
        o.append(f'<text x="{lx + 14:.1f}" y="{ly:.1f}" font-size="11" '
                 f'fill="{p["subtext0"]}">{esc(etichetta)}</text>')
        lx += larghezza

    o.append(f'<text x="{bx}" y="{ALT - 14:.0f}" font-size="10" '
             f'fill="{p["overlay0"]}">code only, document formats excluded</text>')
    o.append(f'<text x="{LARGH - 48:.0f}" y="{ALT - 14:.0f}" text-anchor="end" '
             f'font-size="10" fill="{p["overlay0"]}">'
             f'regenerated {esc(d["aggiornato"])}</text>')

    o.append("</svg>")
    return "".join(o)


if __name__ == "__main__":
    try:
        dati = raccogli()
    except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError,
            KeyError, ValueError) as e:
        print(f"dati non disponibili, non scrivo niente: {e}", file=sys.stderr)
        sys.exit(1)

    for tema in TEMI:
        dest = scrivi("stats", tema, genera(tema, dati))
        print(f"{dest.name:21} {dest.stat().st_size / 1024:5.1f} KB")

    # Impronta dei soli dati, senza l'orario di generazione. Serve al workflow
    # per capire se è cambiato qualcosa davvero: gli SVG cambiano a ogni giro
    # perché contengono il timestamp, e senza questo confronto il repo
    # riceverebbe un commit ogni notte anche a dati identici.
    impronta = {k: v for k, v in dati.items() if k != "aggiornato"}
    (ASSETS / "stats.json").write_text(
        json.dumps(impronta, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"  {dati['repo']} repo, {dati['release']} release, "
          f"{len(dati['lingue'])} linguaggi, ultimo: {dati['recente']}")
