#!/usr/bin/env python3
"""Costruisce una pagina di anteprima con i sei SVG, per vederli animati prima
di pubblicare.

Gli SVG vengono incorporati come <img src="data:image/svg+xml;base64,...">, non
inline: è esattamente il contesto in cui GitHub li mostrerà. Cambia parecchio —
dentro un <img> l'SVG non può caricare risorse esterne e non esegue script, e i
suoi stili restano suoi invece di finire sul resto della pagina.

    python3 anteprima.py     # scrive ../anteprima.html
"""

import base64
import pathlib

QUI = pathlib.Path(__file__).resolve().parent
ASSETS = QUI.parent / "assets"
USCITA = QUI.parent / "anteprima.html"

PEZZI = [
    ("header", "Intestazione: la sessione che si digita da sola",
     "Giro da 14,8 s, di cui 8,4 fermo sullo schermo completo. Poi pulisce e "
     "ridigita. Il fotogramma a t=0 e' il terminale pieno."),
    ("stats", "Pannello dati, rigenerato dalla Action",
     "Statico. I numeri arrivano dall'API di GitHub, la barra e' proporzionale ai "
     "byte di codice veri."),
]


def dato(nome, tema):
    b = (ASSETS / f"{nome}-{tema}.svg").read_bytes()
    return ("data:image/svg+xml;base64," + base64.b64encode(b).decode("ascii"),
            len(b) / 1024)


def main():
    blocchi = []
    for nome, titolo, nota in PEZZI:
        scuro, kb = dato(nome, "mocha")
        chiaro, _ = dato(nome, "latte")
        blocchi.append(f"""
    <section>
      <h2>{titolo}</h2>
      <p class="nota">{nota} &middot; {kb:.1f} KB per variante</p>
      <div class="coppia">
        <figure>
          <img src="{scuro}" alt="{titolo}, variante scura">
          <figcaption>Mocha &mdash; tema scuro di GitHub</figcaption>
        </figure>
        <figure class="chiara">
          <img src="{chiaro}" alt="{titolo}, variante chiara">
          <figcaption>Latte &mdash; tema chiaro di GitHub</figcaption>
        </figure>
      </div>
    </section>""")

    pagina = f"""<title>Anteprima del profilo GitHub</title>
<style>
  :root {{
    --fondo: #f6f6f4; --testo: #1b1b1a; --tenue: #6a6a66; --filo: #dcdcd6;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --fondo: #131314; --testo: #e8e8e4; --tenue: #97978f; --filo: #2c2c2e; }}
  }}
  :root[data-theme="dark"] {{
    --fondo: #131314; --testo: #e8e8e4; --tenue: #97978f; --filo: #2c2c2e;
  }}
  :root[data-theme="light"] {{
    --fondo: #f6f6f4; --testo: #1b1b1a; --tenue: #6a6a66; --filo: #dcdcd6;
  }}
  body {{
    margin: 0; padding: 2.5rem 1.5rem 5rem;
    background: var(--fondo); color: var(--testo);
    font: 16px/1.6 ui-sans-serif, system-ui, sans-serif;
  }}
  main {{ max-width: 900px; margin: 0 auto; display: grid; gap: 3rem; }}
  h1 {{ font-size: 1.5rem; margin: 0 0 .3rem; }}
  h2 {{ font-size: 1.05rem; margin: 0 0 .2rem; }}
  .nota {{ margin: 0 0 1rem; color: var(--tenue); font-size: .87rem; }}
  .coppia {{ display: grid; gap: 1.2rem; }}
  figure {{ margin: 0; }}
  figure img {{ display: block; width: 100%; height: auto; border: 1px solid var(--filo); border-radius: 8px; }}
  figure.chiara img {{ background: #fff; }}
  figcaption {{ margin-top: .4rem; color: var(--tenue); font-size: .8rem; }}
  header p {{ color: var(--tenue); margin: 0; }}
</style>

<main>
  <header>
    <h1>Profilo GitHub &mdash; anteprima degli asset</h1>
    <p>Le animazioni girano davvero: sono SVG dentro un &lt;img&gt;, come su GitHub.
       Ogni pezzo esiste in due varianti, scelte automaticamente dal tema di chi guarda.</p>
  </header>
  {"".join(blocchi)}
</main>
"""
    USCITA.write_text(pagina, encoding="utf-8")
    print(f"{USCITA.name}  {USCITA.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
