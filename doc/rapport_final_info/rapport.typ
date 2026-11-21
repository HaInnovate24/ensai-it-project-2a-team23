// Simple numbering for non-book documents
#let equation-numbering = "(1)"
#let callout-numbering = "1"
#let subfloat-numbering(n-super, subfloat-idx) = {
  numbering("1a", n-super, subfloat-idx)
}

// Theorem configuration for theorion
// Simple numbering for non-book documents (no heading inheritance)
#let theorem-inherited-levels = 0

// Theorem numbering format (can be overridden by extensions for appendix support)
// This function returns the numbering pattern to use
#let theorem-numbering(loc) = "1.1"

// Default theorem render function
#let theorem-render(prefix: none, title: "", full-title: auto, body) = {
  if full-title != "" and full-title != auto and full-title != none {
    strong[#full-title.]
    h(0.5em)
  }
  body
}
// Some definitions presupposed by pandoc's typst output.
#let content-to-string(content) = {
  if content.has("text") {
    content.text
  } else if content.has("children") {
    content.children.map(content-to-string).join("")
  } else if content.has("body") {
    content-to-string(content.body)
  } else if content == [ ] {
    " "
  }
}

#let horizontalrule = line(start: (25%,0%), end: (75%,0%))

#let endnote(num, contents) = [
  #stack(dir: ltr, spacing: 3pt, super[#num], contents)
]

#show terms.item: it => block(breakable: false)[
  #text(weight: "bold")[#it.term]
  #block(inset: (left: 1.5em, top: -0.4em))[#it.description]
]

// Some quarto-specific definitions.

#show raw.where(block: true): set block(
    fill: luma(230),
    width: 100%,
    inset: 8pt,
    radius: 2pt
  )

#let block_with_new_content(old_block, new_content) = {
  let fields = old_block.fields()
  let _ = fields.remove("body")
  if fields.at("below", default: none) != none {
    // TODO: this is a hack because below is a "synthesized element"
    // according to the experts in the typst discord...
    fields.below = fields.below.abs
  }
  block.with(..fields)(new_content)
}

#let empty(v) = {
  if type(v) == str {
    // two dollar signs here because we're technically inside
    // a Pandoc template :grimace:
    v.matches(regex("^\\s*$")).at(0, default: none) != none
  } else if type(v) == content {
    if v.at("text", default: none) != none {
      return empty(v.text)
    }
    for child in v.at("children", default: ()) {
      if not empty(child) {
        return false
      }
    }
    return true
  }

}

// Subfloats
// This is a technique that we adapted from https://github.com/tingerrr/subpar/
#let quartosubfloatcounter = counter("quartosubfloatcounter")

#let quarto_super(
  kind: str,
  caption: none,
  label: none,
  supplement: str,
  position: none,
  subcapnumbering: "(a)",
  body,
) = {
  context {
    let figcounter = counter(figure.where(kind: kind))
    let n-super = figcounter.get().first() + 1
    set figure.caption(position: position)
    [#figure(
      kind: kind,
      supplement: supplement,
      caption: caption,
      {
        show figure.where(kind: kind): set figure(numbering: _ => {
          let subfloat-idx = quartosubfloatcounter.get().first() + 1
          subfloat-numbering(n-super, subfloat-idx)
        })
        show figure.where(kind: kind): set figure.caption(position: position)

        show figure: it => {
          let num = numbering(subcapnumbering, n-super, quartosubfloatcounter.get().first() + 1)
          show figure.caption: it => block({
            num.slice(2) // I don't understand why the numbering contains output that it really shouldn't, but this fixes it shrug?
            [ ]
            it.body
          })

          quartosubfloatcounter.step()
          it
          counter(figure.where(kind: it.kind)).update(n => n - 1)
        }

        quartosubfloatcounter.update(0)
        body
      }
    )#label]
  }
}

// callout rendering
// this is a figure show rule because callouts are crossreferenceable
#show figure: it => {
  if type(it.kind) != str {
    return it
  }
  let kind_match = it.kind.matches(regex("^quarto-callout-(.*)")).at(0, default: none)
  if kind_match == none {
    return it
  }
  let kind = kind_match.captures.at(0, default: "other")
  kind = upper(kind.first()) + kind.slice(1)
  // now we pull apart the callout and reassemble it with the crossref name and counter

  // when we cleanup pandoc's emitted code to avoid spaces this will have to change
  let old_callout = it.body.children.at(1).body.children.at(1)
  let old_title_block = old_callout.body.children.at(0)
  let children = old_title_block.body.body.children
  let old_title = if children.len() == 1 {
    children.at(0)  // no icon: title at index 0
  } else {
    children.at(1)  // with icon: title at index 1
  }

  // TODO use custom separator if available
  // Use the figure's counter display which handles chapter-based numbering
  // (when numbering is a function that includes the heading counter)
  let callout_num = it.counter.display(it.numbering)
  let new_title = if empty(old_title) {
    [#kind #callout_num]
  } else {
    [#kind #callout_num: #old_title]
  }

  let new_title_block = block_with_new_content(
    old_title_block,
    block_with_new_content(
      old_title_block.body,
      if children.len() == 1 {
        new_title  // no icon: just the title
      } else {
        children.at(0) + new_title  // with icon: preserve icon block + new title
      }))

  align(left, block_with_new_content(old_callout,
    block(below: 0pt, new_title_block) +
    old_callout.body.children.at(1)))
}

// 2023-10-09: #fa-icon("fa-info") is not working, so we'll eval "#fa-info()" instead
#let callout(body: [], title: "Callout", background_color: rgb("#dddddd"), icon: none, icon_color: black, body_background_color: white) = {
  block(
    breakable: false, 
    fill: background_color, 
    stroke: (paint: icon_color, thickness: 0.5pt, cap: "round"), 
    width: 100%, 
    radius: 2pt,
    block(
      inset: 1pt,
      width: 100%, 
      below: 0pt, 
      block(
        fill: background_color,
        width: 100%,
        inset: 8pt)[#if icon != none [#text(icon_color, weight: 900)[#icon] ]#title]) +
      if(body != []){
        block(
          inset: 1pt, 
          width: 100%, 
          block(fill: body_background_color, width: 100%, inset: 8pt, body))
      }
    )
}


// syntax highlighting functions from skylighting:
/* Function definitions for syntax highlighting generated by skylighting: */
#let EndLine() = raw("\n")
#let Skylighting(fill: none, number: false, start: 1, sourcelines) = {
   let blocks = []
   let lnum = start - 1
   let bgcolor = rgb("#f1f3f5")
   for ln in sourcelines {
     if number {
       lnum = lnum + 1
       blocks = blocks + box(width: if start + sourcelines.len() > 999 { 30pt } else { 24pt }, text(fill: rgb("#aaaaaa"), [ #lnum ]))
     }
     blocks = blocks + ln + EndLine()
   }
   block(fill: bgcolor, width: 100%, inset: 8pt, radius: 2pt, blocks)
}
#let AlertTok(s) = text(fill: rgb("#ad0000"),raw(s))
#let AnnotationTok(s) = text(fill: rgb("#5e5e5e"),raw(s))
#let AttributeTok(s) = text(fill: rgb("#657422"),raw(s))
#let BaseNTok(s) = text(fill: rgb("#ad0000"),raw(s))
#let BuiltInTok(s) = text(fill: rgb("#003b4f"),raw(s))
#let CharTok(s) = text(fill: rgb("#20794d"),raw(s))
#let CommentTok(s) = text(fill: rgb("#5e5e5e"),raw(s))
#let CommentVarTok(s) = text(style: "italic",fill: rgb("#5e5e5e"),raw(s))
#let ConstantTok(s) = text(fill: rgb("#8f5902"),raw(s))
#let ControlFlowTok(s) = text(weight: "bold",fill: rgb("#003b4f"),raw(s))
#let DataTypeTok(s) = text(fill: rgb("#ad0000"),raw(s))
#let DecValTok(s) = text(fill: rgb("#ad0000"),raw(s))
#let DocumentationTok(s) = text(style: "italic",fill: rgb("#5e5e5e"),raw(s))
#let ErrorTok(s) = text(fill: rgb("#ad0000"),raw(s))
#let ExtensionTok(s) = text(fill: rgb("#003b4f"),raw(s))
#let FloatTok(s) = text(fill: rgb("#ad0000"),raw(s))
#let FunctionTok(s) = text(fill: rgb("#4758ab"),raw(s))
#let ImportTok(s) = text(fill: rgb("#00769e"),raw(s))
#let InformationTok(s) = text(fill: rgb("#5e5e5e"),raw(s))
#let KeywordTok(s) = text(weight: "bold",fill: rgb("#003b4f"),raw(s))
#let NormalTok(s) = text(fill: rgb("#003b4f"),raw(s))
#let OperatorTok(s) = text(fill: rgb("#5e5e5e"),raw(s))
#let OtherTok(s) = text(fill: rgb("#003b4f"),raw(s))
#let PreprocessorTok(s) = text(fill: rgb("#ad0000"),raw(s))
#let RegionMarkerTok(s) = text(fill: rgb("#003b4f"),raw(s))
#let SpecialCharTok(s) = text(fill: rgb("#5e5e5e"),raw(s))
#let SpecialStringTok(s) = text(fill: rgb("#20794d"),raw(s))
#let StringTok(s) = text(fill: rgb("#20794d"),raw(s))
#let VariableTok(s) = text(fill: rgb("#111111"),raw(s))
#let VerbatimStringTok(s) = text(fill: rgb("#20794d"),raw(s))
#let WarningTok(s) = text(style: "italic",fill: rgb("#5e5e5e"),raw(s))



#let article(
  title: none,
  subtitle: none,
  authors: none,
  keywords: (),
  date: none,
  abstract-title: none,
  abstract: none,
  thanks: none,
  cols: 1,
  lang: "en",
  region: "US",
  font: none,
  fontsize: 11pt,
  title-size: 1.5em,
  subtitle-size: 1.25em,
  heading-family: none,
  heading-weight: "bold",
  heading-style: "normal",
  heading-color: black,
  heading-line-height: 0.65em,
  mathfont: none,
  codefont: none,
  linestretch: 1,
  sectionnumbering: none,
  linkcolor: none,
  citecolor: none,
  filecolor: none,
  toc: false,
  toc_title: none,
  toc_depth: none,
  toc_indent: 1.5em,
  doc,
) = {
  // Set document metadata for PDF accessibility
  set document(title: title, keywords: keywords)
  set document(
    author: authors.map(author => content-to-string(author.name)).join(", ", last: " & "),
  ) if authors != none and authors != ()
  set par(
    justify: true,
    leading: linestretch * 0.65em
  )
  set text(lang: lang,
           region: region,
           size: fontsize)
  set text(font: font) if font != none
  show math.equation: set text(font: mathfont) if mathfont != none
  show raw: set text(font: codefont) if codefont != none

  set heading(numbering: sectionnumbering)

  show link: set text(fill: rgb(content-to-string(linkcolor))) if linkcolor != none
  show ref: set text(fill: rgb(content-to-string(citecolor))) if citecolor != none
  show link: this => {
    if filecolor != none and type(this.dest) == label {
      text(this, fill: rgb(content-to-string(filecolor)))
    } else {
      text(this)
    }
   }

  let has-title-block = title != none or (authors != none and authors != ()) or date != none or abstract != none
  if has-title-block {
    place(
      top,
      float: true,
      scope: "parent",
      clearance: 4mm,
      block(below: 1em, width: 100%)[

        #if title != none {
          align(center, block(inset: 2em)[
            #set par(leading: heading-line-height) if heading-line-height != none
            #set text(font: heading-family) if heading-family != none
            #set text(weight: heading-weight)
            #set text(style: heading-style) if heading-style != "normal"
            #set text(fill: heading-color) if heading-color != black

            #text(size: title-size)[#title #if thanks != none {
              footnote(thanks, numbering: "*")
              counter(footnote).update(n => n - 1)
            }]
            #(if subtitle != none {
              parbreak()
              text(size: subtitle-size)[#subtitle]
            })
          ])
        }

        #if authors != none and authors != () {
          let count = authors.len()
          let ncols = calc.min(count, 3)
          grid(
            columns: (1fr,) * ncols,
            row-gutter: 1.5em,
            ..authors.map(author =>
                align(center)[
                  #author.name \
                  #author.affiliation \
                  #author.email
                ]
            )
          )
        }

        #if date != none {
          align(center)[#block(inset: 1em)[
            #date
          ]]
        }

        #if abstract != none {
          block(inset: 2em)[
          #text(weight: "semibold")[#abstract-title] #h(1em) #abstract
          ]
        }
      ]
    )
  }

  if toc {
    let title = if toc_title == none {
      auto
    } else {
      toc_title
    }
    block(above: 0em, below: 2em)[
    #outline(
      title: toc_title,
      depth: toc_depth,
      indent: toc_indent
    );
    ]
  }

  doc
}

#set table(
  inset: 6pt,
  stroke: none
)
#import "@preview/fontawesome:0.5.0": *
#let brand-color = (:)
#let brand-color-background = (:)
#let brand-logo = (:)

#set page(
  paper: "a4",
  margin: (bottom: 2.8cm,left: 2.8cm,right: 2.8cm,top: 3cm,),
  numbering: "1",
  columns: 1,
)

#show: doc => article(
  lang: "fr",
  font: ("Libertinus Serif",),
  fontsize: 11pt,
  sectionnumbering: "1.1.a",
  toc_title: [Table des matières],
  toc_depth: 3,
  doc,
)

// =====================================================================
//  LaborScope — Rapport final (Quarto / Typst)
//  Les zones orange « [ … ] » sont à compléter. Pour les masquer à la
//  remise finale : show-todo = false
// =====================================================================
#let show-todo = true
#let brand = rgb("#1f3554")
#let ocean = rgb("#1b8a9a")
#let sun = rgb("#e0a33e")
#let mist = rgb("#f4f6f9")
#let muted = rgb("#5a5a5a")
#let sans = ("Libertinus Sans", "Libertinus Serif")
#let numero-equipe = "23"   // <- numéro d'équipe

#let todo(body) = if show-todo {
  text(fill: rgb("#c2570c"), weight: "bold", font: sans)[\[#body\]]
}

#set text(lang: "fr", font: "Libertinus Serif", size: 11pt)
#set par(justify: true, leading: 0.68em, first-line-indent: 0pt)
#set list(marker: text(fill: ocean, size: 0.8em)[■])
#set enum(numbering: n => text(fill: ocean, weight: "bold")[#n.])
#set heading(numbering: "1.1")
#set figure(gap: 0.9em)
#show figure.caption: it => text(size: 9.5pt, fill: muted, style: "italic")[
  #text(fill: brand, weight: "bold", style: "normal")[#it.supplement #context it.counter.display(it.numbering)] — #it.body]
#show raw.where(block: true): it => block(width: 100%, fill: mist, stroke: (left: 2pt + brand),
  inset: (left: 10pt, rest: 7pt), radius: 1pt)[#set text(size: 8.5pt); #it]
#show table: set text(size: 10pt)
#set table(stroke: (x, y) => (top: if y == 0 { 1pt + brand } else if y == 1 { 0.6pt + brand } else { none }, bottom: 1pt + brand),
  inset: (x: 6pt, y: 5pt))
#show table.cell.where(y: 0): set text(weight: "bold", fill: brand, font: sans)

// ---------- Titres ----------
#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  v(0.4cm)
  if it.numbering != none {
    block(above: 0pt, below: 0pt, text(size: 46pt, fill: ocean.lighten(10%), font: sans)[#counter(heading).display()])
    v(7pt)
  }
  block(above: 0pt, below: 0pt, text(size: 19pt, weight: "bold", fill: brand, font: sans)[#it.body])
  v(0.3em)
  line(length: 100%, stroke: 1.2pt + ocean)
  v(0.8em)
}
#show heading.where(level: 2): it => block(above: 1.6em, below: 0.7em)[
  #text(size: 12.5pt, weight: "bold", fill: brand, font: sans)[
    #if it.numbering != none [#text(fill: ocean)[#counter(heading).display()] #h(0.3em)]#it.body]]
#show heading.where(level: 3): it => block(above: 1.2em, below: 0.5em)[
  #text(size: 11.5pt, weight: "bold", fill: brand, font: sans)[
    #if it.numbering != none [#text(fill: ocean)[#counter(heading).display()] #h(0.25em)]#it.body]]

// ---------- Composants de schéma (Typst natif, sans extension) ----------
#let cls(name, body, w: 3.7cm, tag: none) = box(width: w, stroke: 0.7pt + brand, radius: 2pt, clip: true)[
  #block(width: 100%, fill: brand.lighten(85%), inset: 4pt, spacing: 0pt)[#align(center)[
    #if tag != none [#text(size: 7pt, style: "italic")[«#tag»] \ ]#text(size: 8.5pt, weight: "bold", font: sans)[#name]]]
  #block(width: 100%, inset: 5pt, spacing: 0pt)[#set align(left); #set par(leading: 0.45em, justify: false); #set text(size: 7.5pt); #body]
]
#let layer(title, sub, col: brand, w: 9cm) = align(center, box(width: w, fill: col, radius: 4pt, inset: 7pt)[
  #align(center)[#text(fill: white, weight: "bold", size: 10pt, font: sans)[#title] \
  #text(fill: white, size: 8pt)[#sub]]])
#let down = align(center, text(fill: brand, size: 13pt)[↓])
#let link(body) = align(center + horizon, text(size: 8pt, fill: ocean, weight: "bold", font: sans)[#body])

// ---------- Cadre « à retenir » ----------
#let retenir(titre: "À retenir", body) = block(width: 100%, fill: ocean.lighten(88%),
  stroke: (left: 3pt + ocean), inset: (left: 12pt, rest: 9pt), above: 1.2em, below: 1.2em)[
  #text(weight: "bold", fill: ocean, font: sans)[#titre] \ #body]

// =====================================================================
//  PAGE DE GARDE
// =====================================================================
#set page(header: none, footer: none, numbering: none)
#align(center)[
  #v(0.2cm)
  #image("images/ensai_logo_1.png", width: 8cm)
  #v(0.8cm)
  #text(size: 12pt, tracking: 1.8pt, fill: muted, font: sans)[PROJET INFORMATIQUE — 2#super[e] ANNÉE]
  #v(0.9cm)
  #line(length: 100%, stroke: 0.5pt + brand)
  #v(0.15cm)
  #text(size: 40pt, weight: "bold", fill: brand, font: sans)[Labor#text(fill: ocean)[Scope]]
  #v(-0.1cm)
  #text(size: 15pt, style: "italic", fill: muted)[Rapport final]
  #v(-0.15cm)
  #text(size: 10.5pt, fill: muted)[Une plateforme pour explorer le marché du travail mondial]
  #v(0.15cm)
  #line(length: 100%, stroke: 0.5pt + brand)
  #v(0.6cm)
  #box(fill: sun, radius: 50%, inset: (x: 15pt, y: 13pt))[
    #text(fill: white, weight: "bold", size: 8pt, font: sans)[ÉQUIPE] \
    #text(fill: white, weight: "bold", size: 28pt, font: sans)[#numero-equipe]]
]
#v(0.6cm)
#grid(columns: (1fr, 1fr), column-gutter: 1cm,
  align(left)[
    #text(style: "italic", fill: muted)[Étudiants] \ #v(0.3em)
    Jade #smallcaps[Colin] \
    Sidy Mohamed Salim #smallcaps[Diallo] \
    Alexandre #smallcaps[Fratter-Bardy] \
    Adam Ouangko #smallcaps[Haïwè] \
    Vicram #smallcaps[Raveendiran]],
  align(right)[
    #text(style: "italic", fill: muted)[Responsable] \ #v(0.3em)
    Ludovic #smallcaps[Deneuville] \ #v(0.8cm)
    #text(style: "italic", fill: muted)[Encadrant] \ #v(0.3em)
    Anas #smallcaps[Knefati]])
#v(1.2cm)
#v(1fr)
#align(center)[#text(size: 10pt)[École nationale de la statistique et de l'analyse de l'information \ *2026 -- 2027*]]
#pagebreak()

// =====================================================================
//  RÉGLAGES COMMUNS
// =====================================================================
#set page(
  header: context {
    set text(size: 8.5pt, fill: muted, style: "italic")
    grid(columns: (1fr, 1fr))[Projet LaborScope][#align(right)[ENSAI --- 2026 -- 2027]]
    v(-0.55em)
    line(length: 100%, stroke: 0.4pt + muted)
  },
  footer: context align(center, text(size: 9pt, fill: brand, font: sans)[#counter(page).display()]),
  numbering: "1")
#counter(page).update(1)
#heading(level: 1, numbering: none)[Remerciements]
<remerciements>
Nous tenons à remercier chaleureusement notre encadrant, Anas Knefati, pour sa disponibilité, la clarté de ses retours et la confiance accordée tout au long du projet. Nos remerciements vont aussi à Ludovic Deneuville, responsable du projet, et à l'équipe enseignante de l'ENSAI pour les ressources mises à notre disposition (modèles de rapport, corrections), ainsi qu'à l'Organisation internationale du Travail, dont les données ouvertes ont rendu ce projet possible. #todo[on doit compléter]

#heading(level: 1, numbering: none)[Table des matières]
<table-des-matières>
#outline(title: none, depth: 2, indent: 1.4em)
#v(1.2em)
#text(size: 14pt, weight: "bold", fill: brand, font: sans)[Table des figures]
#v(0.4em)
#outline(title: none, target: figure.where(kind: image))
#heading(level: 1, numbering: none)[Introduction]
<introduction>
Le marché du travail mondial traverse une période de mutations sans précédent. Plusieurs facteurs sont à l'origine de celle-ci : transition écologique, vieillissement démographique et bien évidemment la croissance exponentielle de l'intelligence artificielle. Dans ce contexte, les acteurs du marché du travail, dans le secteur public ou privé, ont besoin d'un accès aux données relatives au travail. Ces données permettraient d'accéder à des indicateurs d'emploi pour anticiper les tendances, pour comparer la situation entre différents pays et influencer les politiques publiques.

Pourtant, il est encore difficile d'exploiter ces données. En effet, l'ILOSTAT, la plateforme de données statistiques du travail de l'Organisation Internationale du Travail, rend ces données visibles de manière brute. On ne peut donc pas réellement voir l'évolution de certains indicateurs ou tout simplement interpréter la valeur des indicateurs. La question se pose aussi sur la visualisation, comment permettre à l'utilisateur d'obtenir directement les informations qu'il recherche. Comment peut-on alors rendre les données relatives au marché du travail accessibles et exploitables ? LaborScope est une application web qui automatise la collecte d'indicateurs d'emploi depuis ILOSTAT. Elle stocke ces données dans une base PostgreSQL (une base de données centralisée), puis les restitue sous forme d'analyses interactives (évolutions temporelles, comparaisons entre pays, visualisations géographiques). Notre objectif est clair: faciliter la prise de décision en rendant les statistiques de l'emploi plus lisibles, visuelles et accessibles à tous. Ce rapport s'organise en cinq parties, allant de l'analyse des besoins métier jusqu'aux choix d'implémentation technique, pour s'achever sur le bilan qualité et organisationnel du projet. Nous présenterons d'abord le contexte métier : les besoins identifiés, les données mobilisées et les enjeux qui ont défini le développement de LaborScope. Nous enchaînerons avec l'architecture générale, qui détaille la structure de l'application et les technologies nécessaires. Nous entrerons ensuite dans la conception orientée objet, en montrant comment le modèle de classes répond concrètement aux besoins fonctionnels. La quatrième partie est consacrée au système de stockage et à la persistance des données. Enfin, nous terminerons par une synthèse de la gestion du projet, des outils utilisés et de l'assurance qualité mise en place tout au long du développement. .

#grid(columns: (1fr,) * 4, column-gutter: 6pt,
  ..(([3], [profils d'utilisateurs]), (todo[N], [pays couverts]),
     (todo[N], [points d'accès (endpoints)]), (todo[XX %], [couverture des tests])).map(k =>
    block(width: 100%, stroke: 0.6pt + brand.lighten(70%), radius: 3pt, inset: 7pt)[
      #align(center)[#text(size: 24pt, weight: "bold", fill: ocean, font: sans)[#k.at(0)] \
      #text(size: 8pt, fill: muted, font: sans)[#k.at(1)]]]))
= Contexte métier, besoins et données
<contexte-métier-besoins-et-données>
== Besoins métiers et cahier des charges fonctionnel
<besoins-métiers-et-cahier-des-charges-fonctionnel>
#block[
#callout(
body: 
[
Prenons l'exemple d'une chargée d'études économiques souhaitant comparer l'évolution du taux d'emploi des jeunes entre la France, l'Allemagne et l'Espagne sur les dix dernières années. Sur la plateforme brute de l'OIT, elle doit alors télécharger plusieurs fichiers volumineux, filtrer manuellement les codes techniques et construire ses propres graphiques ce qui peut être assez laborieux. Avec LaborScope, il lui suffit de sélectionner ses critères à l'écran pour obtenir instantanément une courbe comparative fiable et prête à être exploitée.

]
, 
title: 
[
Mise en situation
]
, 
background_color: 
rgb("#ccf1e3")
, 
icon_color: 
rgb("#00A047")
, 
icon: 
none
, 
body_background_color: 
white
)
]
Dans la continuité des enjeux soulevés en introduction, LaborScope a été pensé pour transformer des requêtes de données en visualisations claires. Pour répondre à ce besoin d'analyse, l'application repose sur un socle de six fonctionnalités obligatoires qui représente le cœur du traitement des données, complété par deux fonctionnalités optionnelles développées pour enrichir l'interface.

=== Fonctionnalités principales (Socle obligatoire)
<fonctionnalités-principales-socle-obligatoire>
- #strong[Automatisation du flux de données (F1)] : L'application interroge l'API ILOSTAT de manière périodique pour récupérer les indicateurs ciblés. Les fichiers bruts obtenus sont triés et nettoyés pour ne conserver que les champs utiles au projet. Ces données prêtes à l'emploi sont ensuite sauvegardées dans la base de données locale.
- #strong[Filtrage et consultation (F2)] : L'utilisateur peut explorer les données de la base en appliquant divers filtres d'analyse (pays, sexe, tranche d'âge, profession).
- #strong[Analyse temporelle (F3)] : À partir d'un indicateur et d'une fenêtre de temps définis par l'utilisateur, l'API calcule l'évolution de la métrique et le frontend l'affiche sous forme de graphique pour observer les dynamiques du marché.
- #strong[Comparaison entre pays (F4)] : Sur la période la plus récente disponible en base, l'application permet de comparer un même indicateur sur une sélection de pays. Les valeurs extrêmes (les plus hautes et les plus basses) sont mises en évidence sur l'interface.
- #strong[Croisement d'indicateurs (F5)] : L'outil permet de superposer plusieurs indicateurs sur un même graphique et une même échelle de temps, facilitant ainsi l'identification visuelle de potentielles corrélations.
- #strong[Authentification et gestion des droits (F6)] : L'accès est sécurisé par mot de passe avec deux profils d'utilisateurs. Les profils standards disposent d'un accès en consultation, tandis que les administrateurs ont les droits de gestion sur les données stockées. Toute modification en base est par ailleurs tracée dans un journal de suivi des activités (logs).

=== Fonctionnalités additionnelles
<fonctionnalités-additionnelles>
- #strong[Cartographie interactive (FO1)] : Les données d'un indicateur sélectionné sont projetées sur un planisphère, avec un code couleur par pays, pour offrir une vue géographique globale des tendances.
- #strong[Génération de rapports PDF (FO2)] : À partir d'une sélection utilisateur (pays, période, indicateurs), l'application compile les graphiques et génère un export PDF contenant un résumé statistique et une conclusion de synthèse automatisée

== Profils des utilisateurs
<profils-des-utilisateurs>
Afin de répondre aux différents besoins d'exploration et de sécurisation des données, l'application LaborScope a été pensée autour d'une approche progressive des droits d'accès. L'architecture distingue trois profils d'acteurs, allant de la simple découverte à la gestion complète du système :

- #strong[Le visiteur (Utilisateur non connecté)] : Ce profil correspond à un utilisateur découvrant la plateforme. Dans une logique de démonstration de la valeur de l'outil, le visiteur bénéficie d'un accès libre mais restreint à la fonctionnalité d'analyse temporelle. Il peut interroger la base, générer un graphique d'évolution pour un indicateur donné, mais doit s'inscrire pour débloquer les analyses croisées et les exports. Son objectif est exploratoire.
- #strong[L'utilisateur standard (Connecté)] : Il s'agit du cœur de cible de l'application. Une fois authentifié, ce profil accède à l'intégralité du socle analytique et visuel. Outre l'analyse temporelle, il débloque la comparaison géographique, le croisement multi-indicateurs, ainsi que les outils avancés de cartographie et de génération de rapports PDF. Ses droits sont strictement limités à la lecture et à la consultation \; il ne peut en aucun cas altérer les données stockées.
- #strong[L'administrateur] : Ce profil technique est chargé de la maintenance de l'application. L'administrateur hérite de toutes les fonctionnalités de consultation de l'utilisateur standard, auxquelles s'ajoute un accès exclusif à l'espace d'administration. Il dispose des droits de gestion sur les données (lancement des mises à jour, modifications, suppressions) et sur les utilisateurs (suppression de comptes, promotion de rôles). Pour garantir la sécurité et la traçabilité, toute action sensible effectuée par un administrateur est automatiquement consignée dans un journal de suivi des activités.

#figure(caption: [Diagramme de cas d'utilisation.])[
  #block(width: 100%, height: 6cm, fill: mist, stroke: 0.6pt + muted.lighten(40%), radius: 2pt)[
    #align(center + horizon, text(size: 9pt, fill: muted, font: sans)[*Diagramme de cas d'utilisation* — à insérer ici (ou à mettre en annexe)])]
]
== Les données au cœur de l'application
<les-données-au-cœur-de-lapplication>
=== Source et format des données
<source-et-format-des-données>
Le fonctionnement de LaborScope repose sur la capacité à automatiser la collecte et le traitement de données macro-économiques brutes afin de les rendre exploitables pour l'analyse. Cette section détaille la source de ces données, leur structure, ainsi que les opérations de nettoyage nécessaires pour garantir leur fiabilité.

Toutes les données statistiques utilisées par l'application proviennent de l'Organisation Internationale du Travail (OIT), via sa plateforme publique ILOSTAT. Cette source officielle fournit des indicateurs trimestriels et annuels couvrant la majorité des pays du monde.

Bien que le système de l'OIT propose plusieurs formats de réponse, nous avons fait le choix de récupérer les données au format CSV. Ce format sous forme de tableau texte s'intègre de manière simple avec les outils d'analyse disponibles en Python (par exemple la bibliothèque pandas). Ce choix a grandement facilité toute la phase de tri et de nettoyage des données avant leur insertion dans notre base de données locale.

=== Variables clés et concepts métiers
<variables-clés-et-concepts-métiers>
Les données brutes retournées par ILOSTAT sont décomposées puis stockées selon un modèle optimisé pour l'analyse. La table centrale de notre base, l'Observation, contient la valeur statistique mesurée. Elle est rattachée à cinq dimensions que sont les concepts métiers, qui forment les axes de nos futurs graphiques.

Le tableau ci-dessous présente les variables clés stockées et manipulées par l'application :

#table(
  columns: (22.22%, 10%, 67.78%),
  align: (left,left,left,),
  table.header([Nom de la variable], [Type], [Description métier],),
  table.hline(),
  [#NormalTok("code_indicateur");], [Chaîne], [Identifiant de la métrique mesurée (ex : #NormalTok("EMP_TEMP_SEX_OCU_NB"); pour l'emploi par profession).],
  [#NormalTok("code_pays");], [Chaîne], [Code géographique du pays concerné par la mesure (ex : FRA, USA).],
  [#NormalTok("periode");], [Chaîne], [Période de la mesure (ex : 2024-Q1 pour le 1er trimestre 2024, ou 2023).],
  [#NormalTok("sexe");], [Chaîne], [Répartition démographique de l'indicateur (HOMME, FEMME, TOTAL).],
  [#NormalTok("age"); / #NormalTok("occupation");], [Chaîne], [Classification de la population ciblée (tranche d'âge ou catégorie socio-professionnelle).],
  [#NormalTok("valeur");], [Décimal], [La valeur quantitative de l'indicateur pour le croisement des cinq dimensions précédentes.],
)
=== Difficultés des données et nettoyage
<difficultés-des-données-et-nettoyage>
La donnée issue d'ILOSTAT, bien qu'officielle, présente de nombreuses irrégularités qui empêchent son exploitation directe. Nous avons donc mis en place un processus de nettoyage strict pour transformer ce flux brut en données fiables et prêtes à l'emploi :

- #strong[Standardisation des noms de variables] : Les colonnes fournies par l'OIT sont souvent multiples ou non explicites. Des variables nommées différemment selon les fichiers ont toutes été unifiées sous une appellation interne stricte pour faciliter notre traitement.
- Pour ce qui est du #strong[traitement des valeurs aberrantes et manquantes], la plateforme remonte ponctuellement des données non numériques (textes inattendus, cases vides) ou des valeurs infinies. Ces anomalies sont détectées et purgées automatiquement, garantissant que seules des observations quantitatives mathématiquement valides entrent dans notre système.
- #strong[Normalisation des nomenclatures hétérogènes] :
  - #strong[Le sexe] : Les différentes variations textuelles remontées (ex : m, male, homme, sex\_m) sont nettoyées et strictement transformées pour correspondre à notre référentiel unique (HOMME, FEMME, TOTAL).
  - #strong[L'âge] : Les noms des catégories d'âge, parfois redondants ou modifiés dans le temps par ILOSTAT, sont harmonisés pour rester cohérents d'une année sur l'autre.
- Parfois, les données reçues contiennent des statistiques liées à des #strong[régions ou des classements que nous ne gérons pas]. Pour éviter que ces anomalies ne bloquent le système, notre outil les détecte et les écarte d'office.
- Pour pallier les éventuelles redondances lors du téléchargement, les données sont d'abord #strong[filtrées en mémoire] pour ne conserver que la valeur la plus récente. Lors de l'enregistrement final, une règle de mise à jour spécifique garantit qu'une nouvelle collecte actualise proprement les données existantes sans jamais créer de doublons.

== Les données au cœur de l'application
<les-données-au-cœur-de-lapplication-1>
Le fonctionnement de LaborScope repose sur la capacité à automatiser la collecte et le traitement de données macro-économiques brutes afin de les rendre exploitables pour l'analyse. Cette section détaille la source de ces données, leur structure, ainsi que les opérations de nettoyage nécessaires pour garantir leur fiabilité. Toutes les données statistiques utilisées par l'application proviennent de l'Organisation Internationale du Travail (OIT), via sa plateforme publique ILOSTAT. Cette source officielle fournit des indicateurs trimestriels et annuels couvrant la majorité des pays du monde. Bien que le système de l'OIT propose plusieurs formats de réponse, nous avons fait le choix de récupérer les données au format CSV. Ce format sous forme de tableau texte s'intègre de manière simple avec les outils d'analyse disponibles en Python (par exemple la bibliothèque pandas). Ce choix a grandement facilité toute la phase de tri et de nettoyage des données avant leur insertion dans notre base de données locale. Les données brutes retournées par ILOSTAT sont décomposées puis stockées selon un modèle optimisé pour l'analyse. La table centrale de notre base, l'Observation, contient la valeur statistique mesurée. Elle est rattachée à cinq dimensions que sont les concepts métiers, qui forment les axes de nos futurs graphiques.

== Genèse du projet et besoins fonctionnels
<genèse-du-projet-et-besoins-fonctionnels>
=== Un problème concret
<un-problème-concret>
#block[
#callout(
body: 
[
Camille travaille dans un observatoire régional de l'emploi. Avant une réunion, on lui demande de comparer la part des femmes parmi les cadres dirigeants dans cinq pays européens depuis 2010. Chaque pays a son propre tableau, chaque tableau ses filtres, et les années récentes manquent parfois. Elle passe sa matinée à copier des chiffres dans un tableur. Avec LaborScope, elle choisit les pays, la profession et la période \; la réponse arrive en quelques secondes, au même format pour tous les pays.

]
, 
title: 
[
Mise en situation
]
, 
background_color: 
rgb("#ccf1e3")
, 
icon_color: 
rgb("#00A047")
, 
icon: 
none
, 
body_background_color: 
white
)
]
=== Cahier des charges fonctionnel
<cahier-des-charges-fonctionnel>
Les fonctionnalités $F_i$ forment le socle obligatoire \; les fonctionnalités $F O_i$ sont les ajouts choisis par notre groupe.

#table(
  columns: (8.45%, 74.65%, 16.9%),
  align: (left,left,left,),
  table.header([Réf.], [Fonctionnalité], [Nature],),
  table.hline(),
  [$F_1$], [Consulter l'emploi selon le sexe et la profession], [Obligatoire],
  [$F_2$], [Consulter la population en âge de travailler selon le sexe et l'âge], [Obligatoire],
  [$F_3$], [Comparer plusieurs pays sur un même indicateur], [Obligatoire],
  [$F_4$], [Suivre l'évolution d'un indicateur dans le temps], [Obligatoire],
  [$F_5$], [Créer un compte, se connecter, se déconnecter], [Obligatoire],
  [$F_6$], [Gérer des niveaux d'accès], [Obligatoire],
  [$F O_1$], [Cartographie interactive], [Optionnelle],
  [$F O_2$], [Génération automatique de rapports], [Optionnelle],
  [$F O_3$], [Favoris], [Optionnelle],
)
== Profils des utilisateurs
<profils-des-utilisateurs-1>
#table(
  columns: 4,
  align: (left,center,center,center,),
  table.header([Action], [Visiteur], [Inscrit], [Admin],),
  table.hline(),
  [Consulter les statistiques de base], [✓], [✓], [✓],
  [Comparer des pays, suivre une évolution], [--], [✓], [✓],
  [Enregistrer des favoris, exporter], [--], [✓], [✓],
  [Gérer les comptes, rafraîchir les données], [--], [--], [✓],
)
- #strong[Visiteur non connecté] : découvre le service et consulte les indicateurs essentiels, sans compte.
- #strong[Utilisateur inscrit] (chargé d'études, étudiant, journaliste) : exploite pleinement les statistiques, compare et conserve ses recherches.
- #strong[Administrateur] : garantit le bon fonctionnement du service, gère les comptes et la fraîcheur des données.

== Les données au cœur de l'application
<les-données-au-cœur-de-lapplication-2>
=== La source : ILOSTAT
<la-source-ilostat>
Les données proviennent d'#strong[ILOSTAT], la base statistique ouverte de l'Organisation internationale du Travail, accessible par une API. Elle fournit, pour de nombreux pays et régions, des séries annuelles sur l'emploi, le chômage ou la population en âge de travailler, ventilées par sexe, âge et profession, en tableaux (CSV) ou en format structuré (JSON). #todo[On doit préciser les endpoints interrogés, le format retenu, les limites de requêtage]

=== Dictionnaire des variables
<dictionnaire-des-variables>
#table(
  columns: (22.67%, 12%, 65.33%),
  align: (left,left,left,),
  table.header([Variable], [Type], [Signification métier],),
  table.hline(),
  [#NormalTok("ref_area");], [texte], [Pays ou région (code à trois lettres)],
  [#NormalTok("indicator");], [texte], [Code de l'indicateur statistique],
  [#NormalTok("sex");], [texte], [Sexe : femmes, hommes ou total],
  [#NormalTok("classif1");], [texte], [Classification : profession ou tranche d'âge],
  [#NormalTok("time");], [entier], [Année de la mesure],
  [#NormalTok("obs_value");], [réel], [Valeur observée (milliers de personnes ou pourcentage)],
  [#NormalTok("obs_status");], [texte], [Qualité de la valeur (estimée, provisoire…)],
)
=== Indicateurs calculés
<indicateurs-calculés>
$ upright("Taux d’emploi") = upright("Emploi") / upright("Population en âge de travailler") times 100 $

$ upright("Part des femmes") = upright("Emploi des femmes") / upright("Emploi total") times 100 $

#table(
  columns: (24.1%, 61.45%, 14.46%),
  align: (left,left,left,),
  table.header([Indicateur], [Interprétation], [Intervalle],),
  table.hline(),
  [Taux d'emploi], [Part de la population en âge de travailler qui occupe un emploi], [$\[0 thin\;100\]$],
  [Part des femmes], [Féminisation d'une profession (50 = parité)], [$\[0 thin\;100\]$],
  [Variation annuelle], [Évolution relative d'un indicateur d'une année à l'autre], [$\]- 100 thin\;+ oo\[$],
)
=== Difficultés liées aux données
<difficultés-liées-aux-données>
- #strong[Valeurs manquantes] : certains pays ne publient pas toutes les années \; l'application l'indique explicitement plutôt que d'inventer une valeur.
- #strong[Formats hétérogènes] : dates, codes pays et unités sont harmonisés avant toute comparaison.
- #strong[Limites de requêtage] : interroger la source à chaque demande serait lent et fragile \; d'où la mise en cache décrite au chapitre 4.

#block[
#callout(
body: 
[
LaborScope simplifie l'accès aux statistiques de l'OIT pour trois profils d'utilisateurs, avec des données harmonisées et des indicateurs comparables d'un pays à l'autre.

]
, 
title: 
[
Synthèse du chapitre 1
]
, 
background_color: 
rgb("#dae6fb")
, 
icon_color: 
rgb("#0758E5")
, 
icon: 
none
, 
body_background_color: 
white
)
]
= Architecture générale et choix technologiques
<architecture-générale-et-choix-technologiques>
== Nature de l'application et découpage en couches
<nature-de-lapplication-et-découpage-en-couches>
== Structure de l'application
<structure-de-lapplication>
LaborScope repose sur une architecture client-serveur découplée, articulée autour de deux applications communiquant exclusivement par requêtes HTTP au format JSON : Le backend (API REST FastAPI) : centralise la logique métier, les calculs d'indicateurs, le contrôle des droits d'accès, les requêtes vers PostgreSQL ainsi que la collecte et le nettoyage des flux externes ILOSTAT. Le frontend (application web Streamlit) : constitue l'interface utilisateur, gère la navigation et la session, produit les visualisations interactives et assemble les rapports PDF téléchargeables sans jamais accéder directement à la base de données.

#figure(caption: [Architecture en couches : chaque flèche est une dépendance autorisée.])[
  #block(width: 9.4cm, inset: 4pt)[
    #align(center, box(fill: mist, stroke: 0.6pt + brand, radius: 3pt, inset: 6pt)[#text(size: 9pt, font: sans)[Utilisateur]])
    #down
    #layer([Présentation], [documentation interactive (Swagger), JSON], col: ocean)
    #down
    #layer([Contrôleurs], [routes, validation des entrées, authentification])
    #down
    #layer([Services], [logique métier, calcul des indicateurs, droits], col: brand.lighten(15%))
    #down
    #grid(columns: (1fr, 1fr), column-gutter: 4pt,
      layer([Client API], [accès à ILOSTAT], col: ocean.darken(10%), w: 4.4cm),
      layer([DAO], [accès à la base], col: ocean.darken(10%), w: 4.4cm))
    #grid(columns: (1fr, 1fr), column-gutter: 4pt, down, down)
    #grid(columns: (1fr, 1fr), column-gutter: 4pt,
      align(center, box(width: 4.4cm, stroke: (dash: "dashed", paint: sun, thickness: 1pt), fill: sun.lighten(85%), radius: 3pt, inset: 7pt)[
        #align(center, text(size: 9pt, font: sans)[API ILOSTAT (OIT)])]),
      align(center, box(width: 4.4cm, stroke: 1pt + brand, fill: sun.lighten(70%), radius: 8pt, inset: 7pt)[
        #align(center, text(size: 9pt, font: sans)[PostgreSQL])]))
  ]
] <fig-archi>
Le diagramme de packages ci-dessus illustre la manière dont les différentes couches de l'application interagissent entre elles. La première couche correspond au frontend, qui permet à l'utilisateur de se connecter, de naviguer dans l'interface et d'afficher les visualisations graphiques. La deuxième couche est l'API (controller et model), qui réceptionne et valide les requêtes de l'utilisateur avant de les transmettre au serveur. La couche de services (service et business\_object) prend ensuite le relais pour appliquer les règles métier et effectuer les calculs statistiques demandés. Enfin, elle s'appuie sur la couche d'accès aux données (client et dao) : les flux externes sont récupérés et normalisés, puis transmis aux DAO afin d'être stockés et interrogés dans la base PostgreSQL avant d'être renvoyés sous forme de résultats JSON au frontend. Développé en Python, le projet utilise le gestionnaire uv (pyproject.toml et uv.lock) afin de garantir une résolution rapide des dépendances et une stricte reproductibilité entre postes locaux et conteneurs.

Des outils d'assurance qualité (pytest, coverage, ruff, mypy, bandit) complètent cette stack pour vérifier les tests, le typage statique et la conformité du code (détaillés en Partie 5).

== Communication, sécurité et déploiement
<communication-sécurité-et-déploiement>
=== Communication client-serveur et accès aux données
<communication-client-serveur-et-accès-aux-données>
Les échanges entre l'interface et le serveur reposent exclusivement sur des requêtes HTTP au format JSON. Côté frontend, l'ensemble des appels vers l'API est centralisé dans une classe dédiée (APIClient) qui s'appuie sur une session persistante : cela évite de disperser la logique réseau dans les différentes pages et permet de gérer uniformément les délais d'attente ou les erreurs de connexion. Côté serveur, l'API FastAPI organise ses points d'entrée autour de routeurs thématiques (/auth, /referentiels, /analyses, /admin et /journal). Pour interagir avec PostgreSQL, la classe DBConnection implémente le patron de conception Singleton afin de partager une unique connexion sur tout le cycle de vie du backend, évitant ainsi le coût d'ouvertures répétées lors des requêtes analytiques.

=== Sécurisation des accès
<sécurisation-des-accès>
Afin de protéger les comptes utilisateurs et de restreindre l'accès aux fonctionnalités d'administration, aucun mot de passe n'est stocké en clair en base de données : ils sont protégés par un algorithme de hachage sécurisé associé à un sel aléatoire unique. Une fois l'utilisateur connecté, le serveur lui délivre un jeton temporaire (JWT) que l'interface conserve le temps de la session et transmet automatiquement à chaque requête vers une ressource protégée. \#\#\# Conteneurisation et déploiement

L'application est conteneurisée avec Docker et orchestrée via docker-compose.yml autour de trois services isolés communiquant sur un réseau interne dédié : postgres (port 5432) : base de données PostgreSQL 16 dotée d'un volume persistant et initialisée automatiquement au démarrage via les scripts SQL du dossier data/ \; backend (port 5000) : serveur API FastAPI exécuté sous Python 3.13 \; frontend (port 8000) : application web Streamlit dialoguant directement avec le backend via le réseau interne Docker.

#block[
#callout(
body: 
[
Une API REST découpée en couches étanches, construite sur des outils standards de l'écosystème Python \; chaque choix répond à un besoin précis, validation, intégrité, reproductibilité, sécurité.

]
, 
title: 
[
Synthèse du chapitre 2
]
, 
background_color: 
rgb("#dae6fb")
, 
icon_color: 
rgb("#0758E5")
, 
icon: 
none
, 
body_background_color: 
white
)
]
= Conception orientée objet et réponse aux besoins
<conception-orientée-objet-et-réponse-aux-besoins>
== Modélisation objet et principes de conception
<modélisation-objet-et-principes-de-conception>
Plutôt qu'un diagramme unique et illisible, la conception est présentée couche par couche : objets métier, puis services, DAO et client externe. Que des exemples.

#figure(caption: [Diagramme de classes simplifié : objets métier.])[
  #align(center)[
    #grid(columns: (3.7cm, 1.9cm, 3.7cm, 1.9cm, 3.7cm), row-gutter: 14pt,
      cls([Pays], [code_iso3 : str \ nom : str \ region : str]),
      link[1 ◄──── \* \ concerne],
      cls([Observation], [annee : int \ sexe : str \ valeur : float]),
      link[\* ────► 1 \ mesure],
      cls([Indicateur], [code : str \ libelle : str \ unite : str]),
      cls([Administrateur], [gerer_comptes()]),
      link[──────▷ \ hérite],
      cls([Utilisateur], [id : int \ email : str \ peut(action) : bool], tag: "abstraite"),
      link[◁────── \ hérite],
      cls([UtilisateurInscrit], [favoris : list]))
  ]
]
#figure(caption: [Services, DAO et client externe (pointillés = dépendances, ▷ = héritage ou réalisation).])[
  #align(center)[
    #grid(columns: (3.8cm, 3.8cm, 3.8cm), column-gutter: 8pt, row-gutter: 6pt,
      cls([AuthService], [inscrire() \ connecter() \ verifier_jeton()], w: 3.8cm),
      cls([StatistiquesService], [obtenir_statistiques() \ comparer_pays()], w: 3.8cm),
      align(horizon, text(size: 8pt, fill: ocean)[◄ dépend aussi de \ l'interface SourceDonnees ↓]),
      link[⇣ utilise], link[⇣ utilise], [],
      cls([UtilisateurDAO], [trouver_par_email() \ creer()], w: 3.8cm),
      cls([ObservationDAO], [rechercher() \ enregistrer()], w: 3.8cm),
      cls([SourceDonnees], [telecharger(filtres)], w: 3.8cm, tag: "interface"),
      link[▽ hérite de], link[▽ hérite de], link[△ réalise],
      cls([AbstractDAO], [creer() \ supprimer()], w: 3.8cm, tag: "interface"),
      [],
      cls([ILOSTATClient], [telecharger(filtres)], w: 3.8cm))
  ]
]
=== Les concepts de programmation objet mobilisés
<les-concepts-de-programmation-objet-mobilisés>
…

== Zoom sur un processus central : consulter des statistiques
<zoom-sur-un-processus-central-consulter-des-statistiques>
La consultation d'un indicateur d'emploi traverse toutes les couches, de la requête de l'utilisateur jusqu'à la base de données.

#let xs = (1.3cm, 4.5cm, 7.7cm, 10.9cm, 14.1cm)
#let names = ([Utilisateur], [Contrôleur], [Service], [DAO], [Client ILOSTAT])
#let msg(i, j, y, label, ret: false) = {
  let x1 = xs.at(i)
  let x2 = xs.at(j)
  let col = if ret { muted } else { brand }
  let lx = if x1 < x2 { x1 } else { x2 }
  place(top + left, line(start: (x1, y), end: (x2, y),
    stroke: (paint: col, thickness: 0.8pt, dash: if ret { "dashed" } else { "solid" })))
  place(top + left, dx: if x2 > x1 { x2 - 2.2mm } else { x2 - 0.3mm }, dy: y - 1.7mm,
    text(size: 6pt, fill: col)[#if x2 > x1 [▶] else [◀]])
  place(top + left, dx: lx, dy: y - 3.8mm,
    box(width: calc.abs(x2 - x1), align(center, text(size: 7pt, fill: black)[#box(fill: white, inset: (x: 2pt))[#label]])))
}
#let selfmsg(i, y, label) = {
  let x = xs.at(i)
  place(top + left, dx: x, dy: y, rect(width: 5mm, height: 5mm, stroke: (top: 0.8pt + brand, right: 0.8pt + brand, bottom: 0.8pt + brand)))
  place(top + left, dx: x + 6.5mm, dy: y + 0.8mm, text(size: 7pt)[#label])
}
#figure(caption: [Diagramme de séquence de la consultation d'un indicateur.])[
  #block(width: 100%, height: 10.6cm, breakable: false)[
    #place(top + left, dx: xs.at(2) - 1.2cm, dy: 5.0cm,
      rect(width: 15.4cm - xs.at(2) + 1.2cm - 0.1cm, height: 2.7cm, fill: ocean.lighten(90%), stroke: 0.8pt + ocean))
    #place(top + left, dx: xs.at(2) - 1.2cm, dy: 5.0cm,
      box(fill: ocean, inset: 2pt)[#text(size: 6pt, fill: white, weight: "bold")[alt]])
    #place(top + left, dx: xs.at(2) - 0.7cm, dy: 5.05cm,
      text(size: 6pt, fill: ocean)[ cache absent ou périmé])
    #for k in range(5) {
      place(top + left, line(start: (xs.at(k), 0.75cm), end: (xs.at(k), 10.4cm), stroke: (paint: muted.lighten(30%), thickness: 0.6pt, dash: "dashed")))
      place(top + left, dx: xs.at(k) - 1.2cm, dy: 0pt,
        box(width: 2.4cm, fill: brand, radius: 2pt, inset: 4pt, align(center, text(size: 7.5pt, fill: white, weight: "bold")[#names.at(k)])))
    }
    #msg(0, 1, 1.5cm, [GET /stats/emploi])
    #selfmsg(1, 2.0cm, [valider, vérifier le jeton])
    #msg(1, 2, 3.3cm, [obtenir_statistiques(filtres)])
    #msg(2, 3, 4.1cm, [rechercher(filtres)])
    #msg(3, 2, 4.7cm, [observations (ou vide)], ret: true)
    #msg(2, 4, 5.9cm, [telecharger(filtres)])
    #msg(4, 2, 6.6cm, [données JSON], ret: true)
    #msg(2, 3, 7.3cm, [enregistrer(observations)])
    #selfmsg(2, 8.0cm, [calculer les indicateurs])
    #msg(2, 1, 9.2cm, [résultat], ret: true)
    #msg(1, 0, 9.9cm, [200 OK + JSON], ret: true)
  ]
] <fig-seq>
=== Déroulement pas à pas
<déroulement-pas-à-pas>
+ #strong[Que fait l'utilisateur ?] …
+ #strong[Validation et sécurité.] …
+ #strong[Traitement métier.] …
+ #strong[Accès aux données.] \..

=== Zoom sur l'authentification
<zoom-sur-lauthentification>
#todo[Précision de l'algorithme de hachage, de la durée de validité, l'invalidation des jetons et autres qu'on doit compléter]

== Aperçu synthétique des autres fonctionnalités
<aperçu-synthétique-des-autres-fonctionnalités>
#todo[...]

== Cas d'utilisation concret
<cas-dutilisation-concret>
Retour à Camille : elle ouvre la documentation interactive, s'authentifie, puis compare la part des femmes parmi les cadres dirigeants de cinq pays.

#figure(caption: [Parcours utilisateur illustré.])[
  #block(width: 100%, height: 3.4cm, fill: mist, stroke: 0.6pt + muted.lighten(40%), radius: 2pt)[
    #align(center + horizon, text(size: 9pt, fill: muted, font: sans)[*Capture 1* : authentification dans l'interface Swagger])]
  #v(6pt)
  #block(width: 100%, height: 3.4cm, fill: mist, stroke: 0.6pt + muted.lighten(40%), radius: 2pt)[
    #align(center + horizon, text(size: 9pt, fill: muted, font: sans)[*Capture 2* : requête de comparaison de pays et réponse JSON])]
]
#todo[On va remplacer les cadres gris par de vraies captures d'écran : ![](images/capture1.png)]

#block[
#callout(
body: 
[
Une conception en couches, appuyée sur l'héritage, les interfaces et un singleton, qui isole la logique métier du reste \; le processus de consultation illustre le rôle de chaque couche.

]
, 
title: 
[
Synthèse du chapitre 3
]
, 
background_color: 
rgb("#dae6fb")
, 
icon_color: 
rgb("#0758E5")
, 
icon: 
none
, 
body_background_color: 
white
)
]
= Système de stockage et persistance des données
<système-de-stockage-et-persistance-des-données>
== Modèle physique des données et relations
<modèle-physique-des-données-et-relations>
#figure(caption: [Modèle physique des données (version simplifiée).])[
  #align(center)[
    #grid(columns: (3.8cm, 1.8cm, 4.3cm), column-gutter: 4pt, row-gutter: 6pt,
      cls([utilisateur], [*id* (PK) \ email (UNIQUE) \ mot_de_passe_hash \ sel \ role], w: 3.8cm),
      link[1 ──── \* \ possède],
      cls([favori], [*id_utilisateur* (PK, FK) \ *code_pays* (PK, FK) \ *code_indicateur* (PK, FK)], w: 4.3cm))
    #v(2pt)
    #text(size: 8pt, fill: ocean, weight: "bold", font: sans)[↓ clés étrangères vers pays et indicateur ↓]
    #v(2pt)
    #grid(columns: (3.3cm, 1.7cm, 4.3cm, 1.7cm, 3.3cm), column-gutter: 2pt,
      cls([pays], [*code_iso3* (PK) \ nom \ region], w: 3.3cm),
      link[1 ── \* \ concerne],
      cls([observation], [*id* (PK) \ code_pays (FK) \ code_indicateur (FK) \ annee, sexe, classification \ valeur \ _UNIQUE (pays, indicateur, année, sexe, classification)_], w: 4.3cm),
      link[\* ── 1 \ mesure],
      cls([indicateur], [*code* (PK) \ libelle \ unite], w: 3.3cm))
  ]
]
#todo[Aligner sur la base réelle ; version complète en annexe B. C'est un exemple sur lequel on va s'appuyer]

== Normalisation et formes normales
<normalisation-et-formes-normales>
- #strong[1FN (atomicité)] : On va compléter
- #strong[2FN] : …
- #strong[3FN] : …

#block[
#callout(
body: 
[
#todo[Si une dénormalisation a été choisie pour la performance (table agrégée, résultats calculés stockés), on peut mettre la justifier ici. Sinon, on indique que le modèle reste en 3FN.]

]
, 
title: 
[
Dénormalisation volontaire
]
, 
background_color: 
rgb("#fcefdc")
, 
icon_color: 
rgb("#EB9113")
, 
icon: 
none
, 
body_background_color: 
white
)
]
#block[
#callout(
body: 
[
Ceci est juste un exemple que je mets : Un schéma relationnel normalisé, protégé par des contraintes d'intégrité, qui sert aussi de cache entre l'application et l'API ILOSTAT.

]
, 
title: 
[
Synthèse du chapitre 4
]
, 
background_color: 
rgb("#dae6fb")
, 
icon_color: 
rgb("#0758E5")
, 
icon: 
none
, 
body_background_color: 
white
)
]
= Gestion de projet, outils et assurance qualité
<gestion-de-projet-outils-et-assurance-qualité>
== Organisation de l'équipe et planification
<organisation-de-léquipe-et-planification>
=== Méthode de travail
<méthode-de-travail>
Dès la phase de conception, notre équipe, composée de cinq étudiants, a défini des périmètres de responsabilité stricts, qui ont été respectés tout au long du développement afin de faciliter des méthodes de travail communes (Chef de projet / Qualité, Data Engineer, BDD / DAO, Backend / API, et Frontend / DataViz).

Plutôt que de diviser le travail par fonctionnalité où un membre développe une feature de bout en bout, nous avons opté pour une répartition du travail par couche technique. Chaque membre est ainsi devenu garant de la solidité et de la logique de son propre composant. Si ce choix a permis à chacun de monter rapidement en compétence sur sa technologie (PostgreSQL, FastAPI, Streamlit), il a également exigé une communication et une rigueur en matière d'organisation : les formats de données et les interfaces entre la DAO, les Services et l'API devaient être parfaitement définis en amont pour que les couches s'emboîtent sans erreur.

=== Planification
<planification>
#let phases = (
  ([Cadrage], 1, 2), ([Conception], 2, 4), ([Développement par couche], 4, 9),
  ([Intégration (jours d'immersion)], 9, 10), ([Tests et qualité], 8, 13), ([Rapport], 11, 14))
#figure(kind: image, supplement: [Figure], caption: [Diagramme de Gantt du projet.])[
  #table(columns: (4.4cm,) + (1fr,) * 14, align: center + horizon,
    inset: (x: 2pt, y: 4pt),
    stroke: (x, y) => (bottom: 0.3pt + muted.lighten(50%)),
    table.cell(fill: none)[],
    ..range(1, 15).map(w => table.cell(fill: brand)[#text(size: 6.5pt, fill: white)[#w]]),
    ..phases.map(p => (
      table.cell(align: left)[#text(size: 8pt, font: sans)[#p.at(0)]],
      ..range(1, 15).map(w => table.cell(fill: if w >= p.at(1) and w <= p.at(2) { ocean } else { none })[]))).flatten(),
    table.cell(align: left)[#text(size: 8pt, font: sans, weight: "bold")[Soutenance]],
    ..range(1, 14).map(w => []),
    table.cell(fill: sun)[])
]
#todo[à remplacer avec le vrai diagramme (c'est juste un ex.)]

Le suivi de notre avancement s'est appuyé sur le diagramme de Gantt initialement construit lors de la phase d'analyse. Face à la réalité du développement, notamment la complexité de l'intégration entre les couches développées en parallèles, nous n'avons pas pu tenir toutes les grandes lignes prévisionnelles au jour près. Certains modules ont nécessité plus de temps de débogage ou d'appropriation que prévu.

Cependant, ces décalages ont été totalement maîtrisés et résorbés grâce aux trois journées d'immersion. Ce temps de travail intensif, réunissant toute l'équipe en présentiel, a agi comme un véritable catalyseur. Il nous a permis de réaliser l'intégration finale des différentes couches, de lever les points bloquants de communication entre l'API et le Front-end, et de stabiliser l'application pour livrer un produit fonctionnel dans les délais imposés. Par ailleurs, lors de ces jours d'immersion, nous avons eu l'occasion de faire une première présentation en direct du projet. Cela nous a permis de recevoir des remarques constructives de la part de notre encadrant que nous avons ensuite pris en compte afin d'améliorer l'application.

== Outils collaboratifs et normes de développement
<outils-collaboratifs-et-normes-de-développement>
=== Outils de communication et de suivi
<outils-de-communication-et-de-suivi>
Travailler à cinq sur une architecture découpée en couches techniques nécessitait une bonne synchronisation. Nous avons utilisé WhatsApp pour les échanges rapides au quotidien et Notion pour le suivi de l'avancement des tâches.

#figure(caption: [Suivi des tâches sur Notion.])[
  #block(width: 100%, height: 5.5cm, fill: mist, stroke: 0.6pt + muted.lighten(40%), radius: 2pt)[
    #align(center + horizon, text(size: 9pt, fill: muted, font: sans)[*Capture d'écran* du tableau Notion — à insérer ici])]
]
=== Gestion du code avec GitHub
<gestion-du-code-avec-github>
Pour la gestion du code, l'utilisation de GitHub était indispensable. Chacun développait ses composants sur des branches séparées. Une fois qu'un palier d'avancement était atteint, nous ne fusionnions pas le code de manière isolée. Nous organisions des réunions lors desquelles le responsable qualité effectuait une revue du code de chacun pour repérer d'éventuels problèmes ou conflits d'intégration. Ce n'est qu'après cette validation que le travail était fusionné sur la branche principale. Ce n'est qu'à l'issue de chaque fusion que l'ensemble de l'équipe mettait à jour son environnement local à partir de cette nouvelle branche principale pour poursuivre le développement sur une base commune.

=== Normes de codage
<normes-de-codage>
Puisque plusieurs membres intervenaient sur la même base de code, il a fallu fixer des règles communes pour garder un projet lisible :

- #strong[Typage explicite] : Le framework FastAPI reposant fortement sur le typage, nous avons utilisé systématiquement les type hints natifs de Python. Typer les arguments et les retours de nos fonctions a permis de sécuriser les flux de données entre les couches et d'éviter des bugs d'intégration.
- #strong[Linter et nettoyage automatisé] : Nous avons configuré l'outil Ruff directement dans le fichier #NormalTok("pyproject.toml"); pour uniformiser notre style et avons fixé la limite à 100 caractères par ligne et imposé les doubles guillemets. Par ailleurs, l'activation des règles strictes de Ruff nous a permis d'automatiser le tri des importations et d'éliminer le code inutile ou les variables non utilisées avant chaque commit.

== Démarche d'assurance qualité, performances et robustesse
<démarche-dassurance-qualité-performances-et-robustesse>
=== Stratégie de tests
<stratégie-de-tests>
Afin de garantir la stabilité de l'application, nous avons mis en place une suite de tests unitaires avec le framework pytest, couvrant les trois couches du back-end. Nous avons ainsi testé la construction des requêtes SQL au niveau des DAO, la logique de nettoyage et de gestion des erreurs des services métiers, ainsi que les codes de retour HTTP des contrôleurs de l'API. Pour garantir des tests rapides sans risquer de polluer notre base de données locale, nous avons isolé notre code grâce à l'utilisation de mocks via la bibliothèque #NormalTok("unittest.mock");. Cela consiste concrètement à simuler la base de données pour vérifier les requêtes des DAO sans les exécuter, et nous simulons le client HTTP pour tester les services sans déclencher de vrais téléchargements. Cette méthode permet de réduire le temps d'exécution des tests ainsi que de tester des cas aux limites difficiles à reproduire manuellement, comme une perte de connexion réseau ou la réception d'un fichier corrompu.

=== Gestion des temps de traitement longs
<gestion-des-temps-de-traitement-longs>
Pour éviter les problèmes de performances liés à l'extraction et l'insertion de millions de lignes via l'API ILOSTAT nous avons fait en sorte que le script vérifie les fichiers déjà présents sur la base de données locale pour ne télécharger que les données manquantes, ce qui réduit considérablement le temps d'exécution. En ce qui concerne la base de données, une insertion ligne par ligne des observations aurait été beaucoup trop lourde. Nous avons donc utilisé une fonction qui permet de faire des insertions en lot avec une seule requête, tout en traitant également les doublons.

=== Résilience face au changement de source de données
<résilience-face-au-changement-de-source-de-données>
Si l'API ILOSTAT venait à fermer demain ou devait être remplacée, nous avons fait en sorte que l'impact sur notre code serait le plus minime possible. Cela est rendu possible par notre découpage en couches et la séparation des responsabilités. Dans notre architecture, l'intégralité du programme, que ce soit la base de données, l'API ou encore les contrôleurs ignorent l'existence d'ILOSTAT. Le traitement de cette source est centralisé dans deux scripts : le script #NormalTok("ilostat_client.py"); gère l'URL et les requêtes, tandis que #NormalTok("parser_service.py"); adapte les données brutes d'ILOSTAT et les transforment en nos objets Python génériques. En cas de changement de source des données, il suffirait de créer un nouveau fichier client et d'ajuster le dictionnaire de renommage. Ainsi, les tables PostgreSQL, les objets métiers et le reste de l'application n'auraient besoin d'aucune modification.

=== Planification
<planification-1>
#let phases = (
  ([Cadrage], 1, 2), ([Conception], 2, 4), ([Socle (F1 à F6)], 4, 9),
  ([Fonctions optionnelles], 9, 11), ([Tests et qualité], 8, 13), ([Rapport], 11, 14))
#figure(kind: image, supplement: [Figure], caption: [Planification du projet.])[
  #table(columns: (3.6cm,) + (1fr,) * 14, align: center + horizon,
    inset: (x: 2pt, y: 4pt),
    stroke: (x, y) => (bottom: 0.3pt + muted.lighten(50%)),
    table.cell(fill: none)[],
    ..range(1, 15).map(w => table.cell(fill: brand)[#text(size: 6.5pt, fill: white)[#w]]),
    ..phases.map(p => (
      table.cell(align: left)[#text(size: 8pt, font: sans)[#p.at(0)]],
      ..range(1, 15).map(w => table.cell(fill: if w >= p.at(1) and w <= p.at(2) { ocean } else { none })[]))).flatten(),
    table.cell(align: left)[#text(size: 8pt, font: sans, weight: "bold")[Soutenance]],
    ..range(1, 14).map(w => []),
    table.cell(fill: sun)[])
]
#todo[On doit remplacer par le planning réel et commenter les écarts entre prévisionnel et réalité]

== Outils collaboratifs et normes de développement
<outils-collaboratifs-et-normes-de-développement-1>
- #strong[Environnement] : Git et GitHub (versionnage, revue de code), IDE de l'équipe, DBeaver pour explorer la base. #todo[Ajuster]
- #strong[Communication] : messagerie instantanée et réunions hebdomadaires. #todo[à ajuster]
- #strong[Rédaction] : Quarto, pour un rapport reproductible.
- #strong[Normes de codage] : conventions de nommage #strong[PEP 8], #strong[typage statique] systématique, #strong[docstrings] sur les classes et méthodes publiques.

== Démarche d'assurance qualité, performances et robustesse
<démarche-dassurance-qualité-performances-et-robustesse-1>
=== Stratégie de tests
<stratégie-de-tests-1>
Les DAO et les services sont testés isolément. Les tests de la couche DAO s'exécutent sur un #strong[schéma de base dédié], recréé avant et nettoyé après chaque test, de sorte qu'ils n'altèrent jamais les données réelles. L'API ILOSTAT est #strong[simulée] (#emph[mocking]) : les tests sont rapides, reproductibles et indépendants du réseau. Chaque test suit le canevas #emph[given / when / then].

\`\`\`

#table(
  columns: 3,
  align: (left,center,left,),
  table.header([Couche testée], [Couverture], [Remarque],),
  table.hline(),
  [DAO], [#todo[XX %]], [Schéma de test dédié],
  [Services], [#todo[XX %]], [API externe simulée],
  [Contrôleurs], [#todo[XX %]], [Routes et validation],
  [#strong[Total]], [#todo[XX %]], [],
)
=== Gestion des temps de traitement longs
<gestion-des-temps-de-traitement-longs-1>
Les principales lenteurs venaient de l'API distante et des requêtes volumineuses. Nous les avons réduites par trois leviers : mise en cache en base, pagination des résultats et requêtes ciblées sur les seuls indicateurs demandés. #todo[On doit citer des mesures avant/après si possible]

=== Résilience face au changement de source de données
<résilience-face-au-changement-de-source-de-données-1>
Si ILOSTAT venait à disparaître ou à changer de format, seul le #strong[client] qui implémente l'interface #NormalTok("SourceDonnees"); devrait être réécrit. Services, contrôleurs et base resteraient intacts, c'est l'intérêt direct du découpage en couches.

=== Évolutivité et fonctionnalités écartées
<évolutivité-et-fonctionnalités-écartées>
#todo[Listons ici les fonctionnalités mises de côté et expliquons, pour chacune, où elle s'insérerait, nouvelle route, nouveau service, nouvelle DAO]

#block[
#callout(
body: 
[
Une équipe organisée, des outils partagés, des tests isolés et un code robuste face au changement de source, de quoi faire évoluer LaborScope sans le reconstruire.

]
, 
title: 
[
Synthèse du chapitre 5
]
, 
background_color: 
rgb("#dae6fb")
, 
icon_color: 
rgb("#0758E5")
, 
icon: 
none
, 
body_background_color: 
white
)
]
#heading(level: 1, numbering: none)[Conclusion générale]
<conclusion-générale>
#strong[Bilan technique et fonctionnel.] LaborScope atteint son objectif qui est d'offrir un accès simple, sécurisé et comparable aux statistiques mondiales du marché du travail. Le socle obligatoire est #todo[(réalisé en totalité).. Je laisse Jade compléter] et les tests couvrent #todo[XX %] du code.

#strong[Apports pédagogiques.] Le projet nous a appris à concevoir une application en couches, à justifier des choix techniques, à tester de manière isolée et à travailler à cinq sur un même dépôt. Il nous a aussi confrontés aux imprévus, comme les données manquantes, évolutions de périmètre, arbitrages entre fonctionnalités. #todo[On doit personnaliser ici avec un exemple vécu pour que ce soit plus concret et répondra aux remarques du prof]

#strong[Perspectives.] Cartographie interactive, rapports automatiques et nouvelles sources de données s'intégreraient naturellement dans l'architecture actuelle.

#heading(level: 1, numbering: none)[Notes individuelles]
<notes-individuelles>
#heading(level: 2, numbering: none)[Jade Colin]
<jade-colin>
#strong[Mon rôle et mes réalisations.] #todo[Organisation et code : ce que j'ai concrètement produits]

#strong[Mon vécu du travail en groupe.] #todo[Écarts de niveau, tensions ou conflits Git, ajustements]

#strong[Enseignements et conseils aux futurs 2A.] #todo[Ce que je retiens, ce que je ferais autrement.]

#heading(level: 2, numbering: none)[Sidy Mohamed Salim Diallo]
<sidy-mohamed-salim-diallo>
#strong[Mon rôle et mes réalisations.] #todo[(inspires toi de ce qui est mis en crochet chez Jade…]

#strong[Mon vécu du travail en groupe.] #todo[…]

#strong[Enseignements et conseils aux futurs 2A.] #todo[…]

#heading(level: 2, numbering: none)[Alexandre Fratter-Bardy]
<alexandre-fratter-bardy>
#strong[Mon rôle et mes réalisations.] #todo[…]

#strong[Mon vécu du travail en groupe.] #todo[…]

#strong[Enseignements et conseils aux futurs 2A.] #todo[…]

#heading(level: 2, numbering: none)[Adam Ouangko Haïwè]
<adam-ouangko-haïwè>
#strong[Mon rôle et mes réalisations.] #todo[…]

#strong[Mon vécu du travail en groupe.] #todo[…]

#strong[Enseignements et conseils aux futurs 2A.] #todo[…]

#heading(level: 2, numbering: none)[Vicram Raveendiran]
<vicram-raveendiran>
#strong[Mon rôle et mes réalisations.] #todo[…]

#strong[Mon vécu du travail en groupe.] #todo[…]

#strong[Enseignements et conseils aux futurs 2A.] #todo[…]

#heading(level: 1, numbering: none)[Annexes]
<annexes>
#heading(level: 2, numbering: none)[Annexe A --- Diagramme de classes complet]
<annexe-a-diagramme-de-classes-complet>
#todo[Insérons le diagramme de classes complet en haute résolution]

#heading(level: 2, numbering: none)[Annexe B --- Modèle physique des données complet]
<annexe-b-modèle-physique-des-données-complet>
#todo[Insérons le MPD complet]

#heading(level: 2, numbering: none)[Annexe C --- Suivi hebdomadaire des tâches]
<annexe-c-suivi-hebdomadaire-des-tâches>
#todo[Je ne pense pas que cette partie est pertinente à insérer]

#heading(level: 2, numbering: none)[Annexe D --- Conception initiale et conception finale]
<annexe-d-conception-initiale-et-conception-finale>
#todo[Comparons la conception du rapport d'étape (dossier d'analyse) et celle du rapport final]
