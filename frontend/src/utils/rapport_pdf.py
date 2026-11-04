"""Génération de rapports PDF côté frontend (identité LaborScope).

Rapport sobre et éditorial : en-tête de marque, bloc de contexte, chiffres clés,
tableau de données et note de lecture. Produit avec fpdf2 (polices latin-1 : le
texte est assaini pour éviter les caractères non supportés).
"""

from datetime import date
from io import BytesIO

from fpdf import FPDF
from fpdf.enums import XPos, YPos

# Palette (reprise du système de design).
VERT = (46, 114, 87)
ENCRE = (31, 42, 38)
TEXTE = (57, 68, 63)
DOUX = (138, 147, 141)
BORDURE = (225, 224, 214)
CREME = (244, 243, 238)

_REMPLACEMENTS = {
    "—": "-", "–": "-", "−": "-",      # — – −
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "…": "...", "•": "-", " ": " ",
}


def _s(texte: object) -> str:
    """Rend une chaîne compatible avec les polices latin-1 de fpdf2."""
    s = str(texte if texte is not None else "")
    for cible, remplacement in _REMPLACEMENTS.items():
        s = s.replace(cible, remplacement)
    return s.encode("latin-1", "replace").decode("latin-1")


class _RapportPDF(FPDF):
    """Document A4 avec pied de page LaborScope."""

    def footer(self) -> None:
        self.set_y(-15)
        self.set_draw_color(*BORDURE)
        self.set_line_width(0.2)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_y(-12)
        self.set_font("Helvetica", size=8)
        self.set_text_color(*DOUX)
        self.cell(0, 6, _s("Source : OIT - ILOSTAT  ·  Genere par LaborScope"),
                  align="L")
        self.cell(0, 6, _s(f"Page {self.page_no()}/{{nb}}"), align="R")


def _ajuster(pdf: FPDF, texte: str, largeur: float) -> str:
    """Tronque proprement (avec « ... ») un texte trop large pour sa cellule."""
    t = _s(texte)
    dispo = largeur - 2
    if pdf.get_string_width(t) <= dispo:
        return t
    while t and pdf.get_string_width(t + "...") > dispo:
        t = t[:-1]
    return (t + "...") if t else "..."


def construire_rapport_pdf(
    titre: str,
    sous_titre: str,
    contexte: list[tuple[str, str]],
    colonnes: list[str],
    lignes: list[list[str]],
    chiffres: list[tuple[str, str]] | None = None,
    note: str = "",
    image_png: bytes | None = None,
    legende_graphique: str = "",
    eyebrow: str = "Explorateur de donnees - ILOSTAT",
) -> bytes:
    """Construit le rapport et renvoie le PDF en octets."""
    pdf = _RapportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(16, 16, 16)
    pdf.alias_nb_pages()
    pdf.add_page()
    largeur = pdf.w - pdf.l_margin - pdf.r_margin

    # --- En-tête ---
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*VERT)
    pdf.cell(0, 5, _s(eyebrow.upper()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*ENCRE)
    pdf.cell(0, 11, _s(titre), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if sous_titre:
        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(*DOUX)
        pdf.cell(0, 7, _s(sous_titre), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*DOUX)
    pdf.cell(0, 6, _s(f"Extrait du {date.today():%d/%m/%Y}"),
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.set_draw_color(*VERT)
    pdf.set_line_width(0.6)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(6)

    # --- Contexte ---
    if contexte:
        _titre_section(pdf, "Contexte")
        pdf.set_font("Helvetica", "", 10)
        for label, valeur in contexte:
            pdf.set_text_color(*DOUX)
            pdf.cell(42, 6, _s(label), new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_text_color(*TEXTE)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, _s(valeur), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 10)
        pdf.ln(4)

    # --- Chiffres clés ---
    if chiffres:
        _titre_section(pdf, "Chiffres cles")
        n = len(chiffres)
        espace = 4
        bloc = (largeur - espace * (n - 1)) / n
        y0 = pdf.get_y()
        x = pdf.l_margin
        for label, valeur in chiffres:
            pdf.set_xy(x, y0)
            pdf.set_draw_color(*BORDURE)
            pdf.set_line_width(0.2)
            pdf.rect(x, y0, bloc, 20, round_corners=True, corner_radius=2)
            pdf.set_xy(x + 3, y0 + 3)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*DOUX)
            pdf.cell(bloc - 6, 4, _s(label), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_xy(x + 3, y0 + 9)
            pdf.set_font("Helvetica", "B", 15)
            pdf.set_text_color(*ENCRE)
            pdf.cell(bloc - 6, 8, _s(valeur))
            x += bloc + espace
        pdf.set_y(y0 + 20)
        pdf.ln(6)

    # --- Graphique (image exportée de Plotly) ---
    if image_png:
        _titre_section(pdf, "Graphique")
        pdf.image(BytesIO(image_png), x=pdf.l_margin, w=largeur)
        if legende_graphique:
            pdf.ln(1)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*DOUX)
            pdf.cell(0, 5, _s(legende_graphique), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)

    # --- Tableau de données ---
    if colonnes and lignes:
        _titre_section(pdf, "Donnees")
        n_col = len(colonnes)
        # Première colonne plus large, les autres réparties.
        premiere = largeur * 0.40 if n_col > 1 else largeur
        autres = (largeur - premiere) / (n_col - 1) if n_col > 1 else 0
        larg = [premiere] + [autres] * (n_col - 1)

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(*VERT)
        pdf.set_text_color(255, 255, 255)
        for i, col in enumerate(colonnes):
            aligne = "L" if i == 0 else "R"
            pdf.cell(larg[i], 8, _ajuster(pdf, col, larg[i]), border=0, align=aligne, fill=True)
        pdf.ln(8)

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*TEXTE)
        pdf.set_draw_color(*BORDURE)
        for r, ligne in enumerate(lignes):
            pdf.set_fill_color(249, 249, 245) if r % 2 == 1 else pdf.set_fill_color(255, 255, 255)
            for i, cellule in enumerate(ligne):
                aligne = "L" if i == 0 else "R"
                pdf.cell(larg[i], 7, _ajuster(pdf, cellule, larg[i]),
                         border="B", align=aligne, fill=True)
            pdf.ln(7)
        pdf.ln(5)

    # --- Note de lecture ---
    if note:
        _titre_section(pdf, "A retenir")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*TEXTE)
        pdf.multi_cell(0, 5.5, _s(note))

    sortie = pdf.output()
    return bytes(sortie)


def figure_png(fig, largeur: int = 1100, hauteur: int = 460) -> bytes | None:
    """Exporte une figure Plotly en PNG (via kaleido). None si l'export échoue."""
    try:
        return fig.to_image(format="png", width=largeur, height=hauteur, scale=2)
    except Exception:
        return None


def _titre_section(pdf: FPDF, texte: str) -> None:
    """Petit intitulé de section (capitales vertes)."""
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*VERT)
    pdf.cell(0, 5, _s(texte.upper()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)
