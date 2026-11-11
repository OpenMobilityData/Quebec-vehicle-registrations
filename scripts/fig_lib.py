"""Shared chart style (same palette as the other OpenMobilityData repositories; validated with the
dataviz palette validator there). Text wears ink colours, never the series colour."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

BLUE, ORANGE, AQUA, YELLOW, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#c9930a", "#6250d6"
INK, MUTED, GRID, AXIS, SURFACE = "#1f2428", "#5f6b74", "#e2e4e1", "#c9cdd2", "#ffffff"
SRC = {
    "en": "Sources: SAAQ, open data « Véhicules en circulation », 2011–2022 (files of December 18, 2023); "
          "SAAQ, files released under the access Act, file 03.06.34729 (decision of September 17, 2025), 2023–2024.",
    "fr": "Sources : SAAQ, données ouvertes « Véhicules en circulation », 2011–2022 (fichiers du 18 décembre 2023) ; "
          "SAAQ, fichiers communiqués en vertu de la Loi sur l’accès, dossier 03.06.34729 (décision du 17 septembre 2025), 2023–2024.",
}

plt.rcParams.update({
    "font.family": "Helvetica Neue", "font.size": 10, "text.color": INK, "axes.labelcolor": MUTED,
    "axes.edgecolor": AXIS, "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
    "axes.spines.right": False, "axes.spines.left": False, "axes.grid": True, "axes.grid.axis": "y",
    "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True, "xtick.major.size": 0,
    "ytick.major.size": 0, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "svg.fonttype": "none",
    "legend.frameon": False,
})


def num(x, lang, dec=0):
    s = f"{x:,.{dec}f}"
    return s if lang == "en" else s.replace(",", " ").replace(".", ",")


def pct(x, lang, dec=2, sign=True):
    s = f"{x:+.{dec}f}" if sign else f"{x:.{dec}f}"
    s = s.replace("-", "−")
    return s + " %" if lang == "en" else s.replace(".", ",") + " %"


def thousands(ax, lang):
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: num(v, lang)))


def finish(fig, here, stem, lang, title, subtitle, note, bottom=0.2):
    fig.text(0.012, 0.975, title, fontsize=13, fontweight="bold", va="top")
    fig.text(0.012, 0.915, subtitle, fontsize=10, color=MUTED, va="top")
    fig.text(0.012, 0.012, note + "\n" + SRC[lang], fontsize=7.5, color=MUTED, va="bottom", wrap=True)
    fig.subplots_adjust(top=0.82, bottom=bottom, left=0.07, right=0.97)
    for ext in ("png", "svg"):
        fig.savefig(Path(here) / f"{stem}_{lang}.{ext}", dpi=200)
    plt.close(fig)


def released_inferred(ax, s, color, last_released=2022, label=None, inferred_label=None):
    """A yearly series whose points after `last_released` are inferred: hollow markers, dashed link."""
    a, b = s.loc[:last_released], s.loc[last_released:]
    ax.plot(a.index, a.values, color=color, lw=2, marker="o", ms=4.5, label=label)
    if len(b) > 1:
        ax.plot(b.index, b.values, color=color, lw=1.6, ls=(0, (3, 2)))
        ax.plot(b.index[1:], b.values[1:], ls="none", marker="o", ms=6, mfc=SURFACE, mec=color, mew=1.8, label=inferred_label)
