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
  v(1.2cm)
  if it.numbering != none {
    block(above: 0pt, below: 0pt, text(size: 46pt, fill: ocean.lighten(10%), font: sans)[#counter(heading).display()])
    v(7pt)
  }
  block(above: 0pt, below: 0pt, text(size: 19pt, weight: "bold", fill: brand, font: sans)[#it.body])
  v(0.3em)
  line(length: 100%, stroke: 1.2pt + ocean)
  v(0.8em)
}
#show heading.where(level: 2): it => block(above: 1.6em, below: 0.9em)[
  #text(size: 12.5pt, weight: "bold", fill: brand, font: sans)[
    #if it.numbering != none [#text(fill: ocean)[#counter(heading).display()] #h(0.3em)]#it.body]]
#show heading.where(level: 3): it => block(above: 1.2em, below: 0.9em)[
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
    #text(style: "italic", fill: muted)[Étudiant.e.s :] \ #v(0.3em)
    Adam Ouangko #smallcaps[Haïwè] \
    Alexandre #smallcaps[Fratter-Bardy] \
    Jade #smallcaps[Colin] \
    Vicram #smallcaps[Raveendiran] \
    Sidy Mohamed Salim #smallcaps[Diallo]],
  align(right)[
    #text(style: "italic", fill: muted)[Responsable :] \ #v(0.3em)
    Ludovic #smallcaps[Deneuville] \ #v(0.8cm)
    #text(style: "italic", fill: muted)[Encadrant :] \ #v(0.3em)
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

#let synthese(chap, body) = block(width: 100%, fill: ocean.lighten(88%), stroke: (left: 2.5pt + ocean),
  inset: (left: 9pt, rest: 6pt), above: 0.9em, below: 0pt, breakable: false)[
  #set text(size: 9.5pt)
  #set par(leading: 0.55em, justify: true)
  #text(weight: "bold", fill: ocean, font: sans)[Synthèse du chapitre #chap] — #body]
#heading(level: 1, numbering: none)[Remerciements]
<remerciements>
Nous tenons à remercier chaleureusement notre encadrant, Anas Knefati, pour sa disponibilité, la clarté de ses retours et la confiance accordée tout au long du projet. Ses remarques lors de notre première présentation en direct, pendant les journées d'immersion, nous ont permis d'améliorer concrètement l'application et de mieux structurer notre démarche. Nos remerciements vont aussi à Ludovic Deneuville, responsable du projet, et à l'équipe enseignante de l'ENSAI pour les ressources mises à notre disposition, ainsi que pour les cours qui nous ont donné les bases nécessaires à la conception et à la réalisation de cette application.

Nous remercions également l'Organisation Internationale du Travail, dont les données ouvertes, accessibles via ILOSTAT, ont rendu ce projet possible, ainsi que les communautés open source qui développent et documentent les outils sur lesquels repose LaborScope : Python, FastAPI, Streamlit, PostgreSQL, pandas, Docker et bien d'autres.

Enfin, nous tenons à nous remercier mutuellement : chacun des cinq membres de l'équipe a porté la solidité de sa propre couche technique, partagé ses connaissances et pris le temps de relire et de corriger le travail des autres. C'est cette entraide, nourrie par les revues de code et les journées de travail en présentiel, qui a permis d'assembler un produit cohérent dans les délais impartis.

#pagebreak()
#heading(level: 1, numbering: none)[Table des matières]
<table-des-matières>
#outline(title: none, depth: 2, indent: 1.4em)
#v(1.2em)
#text(size: 14pt, weight: "bold", fill: brand, font: sans)[Table des figures]
#v(0.4em)
#outline(title: none, target: figure.where(kind: image))
#pagebreak()
#heading(level: 1, numbering: none)[Introduction]
<introduction>
Le marché du travail mondial traverse une période de mutations sans précédent. Plusieurs facteurs sont à l'origine de celle-ci : transition écologique, vieillissement démographique et bien évidemment la croissance exponentielle de l'intelligence artificielle. Dans ce contexte, les acteurs du marché du travail, dans le secteur public ou privé, ont besoin d'un accès aux données relatives au travail. Ces données permettraient d'accéder à des indicateurs d'emploi pour anticiper les tendances, pour comparer la situation entre différents pays et influencer les politiques publiques.

Pourtant, il est encore difficile d'exploiter ces données. En effet, l'ILOSTAT, la plateforme de données statistiques du travail de l'Organisation Internationale du Travail, rend ces données accessibles de manière brute. On ne peut donc pas réellement voir l'évolution de certains indicateurs ou tout simplement interpréter la valeur des indicateurs. La question se pose aussi sur la visualisation, comment permettre à l'utilisateur d'obtenir directement les informations qu'il recherche ? Comment peut-on alors rendre les données relatives au marché du travail accessibles et exploitables ? #NormalTok("LaborScope"); est une application web qui automatise la collecte d'indicateurs d'emploi depuis ILOSTAT. Elle stocke ces données dans une base PostgreSQL (une base de données centralisée), puis les restitue sous forme d'analyses interactives (évolutions temporelles, comparaisons entre pays, visualisations géographiques). Notre objectif est clair : faciliter la prise de décision en rendant les statistiques de l'emploi plus lisibles, visuelles et accessibles à tous. Ce rapport s'organise en cinq parties, allant de l'analyse des besoins métier jusqu'aux choix d'implémentation technique, pour s'achever sur le bilan qualité et organisationnel du projet. Nous présenterons d'abord le contexte métier, les besoins identifiés, les données mobilisées et les enjeux qui ont défini le développement de #NormalTok("LaborScope");. Nous enchaînerons avec l'architecture générale, qui détaille la structure de l'application et les technologies nécessaires. Nous entrerons ensuite dans la conception orientée objet, en montrant comment le modèle de classes répond concrètement aux besoins fonctionnels. La quatrième partie est consacrée au système de stockage et à la persistance des données. Enfin, nous terminerons par une synthèse de la gestion du projet, des outils utilisés et de l'assurance qualité mise en place tout au long du développement.

= Contexte métier, besoins et données
<contexte-métier-besoins-et-données>
== Besoins métier et cahier des charges fonctionnel
<besoins-métier-et-cahier-des-charges-fonctionnel>
#block[
#callout(
body: 
[
Prenons l'exemple d'une chargée d'études économiques souhaitant comparer l'évolution du taux d'emploi des jeunes entre la France, l'Allemagne et l'Espagne sur les dix dernières années. Sur la plateforme brute de l'OIT, elle doit alors télécharger plusieurs fichiers volumineux, filtrer manuellement les codes techniques et construire ses propres graphiques, ce qui peut être assez laborieux. Avec #NormalTok("LaborScope");, il lui suffit de sélectionner ses critères à l'écran pour obtenir instantanément une courbe comparative fiable et prête à être exploitée.

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
- #strong[Automatisation du flux de données (F1)] : À la demande d'un administrateur (bouton d'import dans l'interface ou commande #NormalTok("make db-import");), l'application récupère les indicateurs ciblés depuis ILOSTAT ou depuis les fichiers CSV déjà archivés localement. Les fichiers bruts obtenus sont triés et nettoyés pour ne conserver que les champs utiles au projet. Ces données prêtes à l'emploi sont ensuite sauvegardées dans la base de données locale.
- #strong[Filtrage et consultation (F2)] : L'utilisateur peut explorer les données de la base en appliquant divers filtres d'analyse (pays, sexe, tranche d'âge, profession).
- #strong[Analyse temporelle (F3)] : À partir d'un indicateur et d'une fenêtre de temps définis par l'utilisateur, l'API calcule l'évolution de la métrique et le frontend l'affiche sous forme de graphique pour observer les dynamiques du marché.
- #strong[Comparaison entre pays (F4)] : Sur la période la plus récente disponible en base, l'application permet de comparer un même indicateur sur une sélection de pays. Les valeurs extrêmes (les plus hautes et les plus basses) sont mises en évidence sur l'interface.
- #strong[Croisement d'indicateurs (F5)] : L'outil permet de superposer plusieurs indicateurs sur un même graphique et une même échelle de temps, facilitant ainsi l'identification de potentielles corrélations.
- #strong[Authentification et gestion des droits (F6)] : L'accès est sécurisé par mot de passe avec deux profils d'utilisateurs. Les profils standards disposent d'un accès en consultation, tandis que les administrateurs ont les droits de gestion sur les données stockées. Toute modification en base est par ailleurs tracée dans un journal de suivi des activités (logs).

=== Fonctionnalités additionnelles
<fonctionnalités-additionnelles>
- #strong[Cartographie interactive (FO1)] : Les données d'un indicateur sélectionné sont projetées sur un planisphère, avec un code couleur par pays, pour offrir une vue géographique globale des tendances.
- #strong[Génération de rapports PDF (FO2)] : À partir d'une sélection utilisateur (pays, période, indicateurs), l'application compile les graphiques et génère un export PDF contenant un résumé statistique et une conclusion de synthèse automatisée.

#table(
  columns: (8.45%, 74.65%, 16.9%),
  align: (left,left,left,),
  table.header([Réf.], [Fonctionnalité], [Nature],),
  table.hline(),
  [$F_1$], [Automatiser le flux de données], [Obligatoire],
  [$F_2$], [Filtrer et consulter les données], [Obligatoire],
  [$F_3$], [Suivre l'évolution d'un indicateur dans le temps], [Obligatoire],
  [$F_4$], [Comparer plusieurs pays sur un même indicateur], [Obligatoire],
  [$F_5$], [Comparer plusieurs indicateurs], [Obligatoire],
  [$F_6$], [S'authentifier et gérer les niveaux d'accès], [Obligatoire],
  [$F O_1$], [Cartographie interactive], [Optionnelle],
  [$F O_2$], [Génération automatique de rapports], [Optionnelle],
)
== Profils des utilisateurs
<profils-des-utilisateurs>
Afin de répondre aux différents besoins d'exploration et de sécurisation des données, l'application #NormalTok("LaborScope"); a été pensée autour d'une approche progressive des droits d'accès. L'architecture distingue trois profils d'acteurs, allant de la simple découverte à la gestion complète du système :

- #strong[Le visiteur (Utilisateur non connecté)] : Ce profil correspond à un utilisateur découvrant la plateforme. Dans une logique de démonstration de la valeur de l'outil, le visiteur bénéficie d'un accès libre mais restreint à la fonctionnalité d'analyse temporelle. Il peut interroger la base, générer un graphique d'évolution pour un indicateur donné, mais doit s'inscrire pour débloquer les analyses croisées et les exports. Son objectif est exploratoire.
- #strong[L'utilisateur standard (Connecté)] : Il s'agit du cœur de cible de l'application. Une fois authentifié, ce profil accède à l'intégralité du socle analytique et visuel. Outre l'analyse temporelle, il débloque la comparaison géographique, le croisement multi-indicateurs, ainsi que les outils avancés de cartographie et de génération de rapports PDF. Ses droits sont strictement limités à la lecture et à la consultation \; il ne peut en aucun cas altérer les données stockées.
- #strong[L'administrateur] : Ce profil technique est chargé de la maintenance de l'application. L'administrateur hérite de toutes les fonctionnalités de consultation de l'utilisateur standard, auxquelles s'ajoute un accès exclusif à l'espace d'administration. Il dispose des droits de gestion sur les données (lancement des mises à jour, modifications, suppressions) et sur les utilisateurs (suppression de comptes, promotion de rôles). Pour garantir la sécurité et la traçabilité, toute action sensible effectuée par un administrateur est automatiquement consignée dans un journal de suivi des activités.

#figure(caption: [Diagramme de cas d'utilisation de LaborScope.])[
  #let profil(titre, body) = block(width: 100%, stroke: (left: 3pt + ocean), fill: ocean.lighten(92%),
    inset: (left: 9pt, rest: 7pt), above: 8pt, below: 0pt)[
    #text(weight: "bold", fill: brand, font: sans, size: 9.5pt)[#titre] \ #body]
  #grid(columns: (7cm, 1fr), column-gutter: 16pt, align: horizon,
    block(stroke: 0.6pt + brand.lighten(60%), radius: 3pt, inset: 7pt, fill: white,
      image("images/diagramme_cas_utilisation_drawio.png", width: 100%)),
    [
      #set align(left)
      #set text(size: 9pt)
      #set par(justify: false, leading: 0.55em)
      #text(size: 8pt, tracking: 1pt, fill: muted, font: sans)[LECTURE PAR PROFIL]
      #profil([Visiteur], [Analyse l'évolution temporelle, en accès libre mais restreint.])
      #profil([Utilisateur connecté], [Après authentification : comparer les pays, comparer plusieurs indicateurs, afficher la cartographie, générer un rapport PDF.])
      #profil([Administrateur], [Hérite de tous les cas de l'utilisateur ; met à jour les données, gère les utilisateurs et suit leurs activités.])
    ])
] <fig-cas>
#table(
  columns: 4,
  align: (left,center,center,center,),
  table.header([Action], [Visiteur], [Inscrit], [Admin],),
  table.hline(),
  [Analyser l'évolution temporelle d'un indicateur], [✓], [✓], [✓],
  [Comparer des pays ou des indicateurs, afficher la carte], [--], [✓], [✓],
  [Exporter les données, générer un rapport PDF], [--], [✓], [✓],
  [Gérer les comptes, rafraîchir les données], [--], [--], [✓],
)
== Les données au cœur de l'application
<les-données-au-cœur-de-lapplication>
=== Source et format des données
<source-et-format-des-données>
Le fonctionnement de #NormalTok("LaborScope"); repose sur la capacité à automatiser la collecte et le traitement de données macro-économiques brutes afin de les rendre exploitables pour l'analyse. Cette section détaille la source de ces données, leur structure, ainsi que les opérations de nettoyage nécessaires pour garantir leur fiabilité.

Toutes les données statistiques utilisées par l'application proviennent de l'Organisation Internationale du Travail (OIT), via sa plateforme publique ILOSTAT. Cette source officielle fournit des indicateurs trimestriels et annuels couvrant la majorité des pays du monde.

Bien que le système de l'OIT propose plusieurs formats de réponse, nous avons fait le choix de récupérer les données au format CSV. Ce format sous forme de tableau texte s'intègre de manière simple avec les outils d'analyse disponibles en Python (par exemple la bibliothèque pandas). Ce choix a grandement facilité toute la phase de tri et de nettoyage des données avant leur insertion dans notre base de données locale.

=== Variables clés et concepts métiers
<variables-clés-et-concepts-métiers>
Les données brutes retournées par ILOSTAT sont décomposées puis stockées selon un modèle optimisé pour l'analyse. La table centrale de notre base, l'observation, contient la valeur statistique mesurée. Elle est rattachée à cinq dimensions que sont les concepts métiers, qui forment les axes de nos futurs graphiques.

Le tableau ci-dessous présente les variables clés stockées et manipulées par l'application :

#table(
  columns: (22.22%, 10%, 67.78%),
  align: (left,left,left,),
  table.header([Nom de la variable], [Type], [Description métier],),
  table.hline(),
  [#NormalTok("code_indicateur");], [Chaîne], [Identifiant de la métrique mesurée (ex : #NormalTok("EMP_TEMP_SEX_OCU_NB"); pour l'emploi par profession).],
  [#NormalTok("code_pays");], [Chaîne], [Code géographique du pays concerné par la mesure (ex : FRA, USA).],
  [#NormalTok("periode");], [Chaîne], [Période de la mesure (ex : 2024-Q1 pour le 1er trimestre 2024, ou 2023).],
  [#NormalTok("sexe");], [Chaîne], [Répartition démographique de l'indicateur (homme, femme, total).],
  [#NormalTok("code_classification");], [Chaîne], [Classification de la population ciblée (tranche d'âge ou catégorie socio-professionnelle).],
  [#NormalTok("valeur");], [Décimal], [La valeur quantitative de l'indicateur pour le croisement des cinq dimensions précédentes.],
)
=== Difficultés des données et nettoyage
<difficultés-des-données-et-nettoyage>
La donnée issue d'ILOSTAT, bien qu'officielle, présente de nombreuses irrégularités qui empêchent son exploitation directe. Nous avons donc mis en place un processus de nettoyage strict pour transformer ce flux brut en données fiables et prêtes à l'emploi :

- #strong[Standardisation des noms de variables] : Les colonnes fournies par l'OIT sont souvent multiples ou non explicites. Des variables nommées différemment selon les fichiers ont toutes été unifiées sous une appellation interne stricte pour faciliter notre traitement.
- Pour ce qui est du #strong[traitement des valeurs aberrantes et manquantes], la plateforme remonte ponctuellement des données non numériques (textes inattendus, cases vides, valeurs « … ») ou des valeurs infinies. Ces anomalies sont détectées et purgées automatiquement, garantissant que seules des observations quantitatives mathématiquement valides entrent dans notre système.
- #strong[Normalisation des nomenclatures hétérogènes] :
  - #strong[Le sexe] : Les différentes variations textuelles remontées (ex : m, male, homme, sex\_m) sont nettoyées et strictement transformées pour correspondre à notre référentiel unique (homme, femme, total).
  - #strong[L'âge] : Les noms des catégories d'âge, parfois redondants ou modifiés dans le temps par ILOSTAT, sont harmonisés pour rester cohérents d'une année sur l'autre.
- Parfois, les données reçues contiennent des statistiques liées à des #strong[régions ou des classements que nous ne gérons pas]. Pour éviter que ces anomalies ne bloquent le système, notre outil les détecte et les écarte d'office.
- Pour pallier les éventuelles redondances lors du téléchargement, les données sont d'abord #strong[filtrées en mémoire] pour ne conserver que la valeur la plus récente. Lors de l'enregistrement final, une règle de mise à jour spécifique garantit qu'une nouvelle collecte actualise proprement les données existantes sans jamais créer de doublons.

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
== Structure de l'application
<structure-de-lapplication>
#NormalTok("LaborScope"); repose sur une architecture client-serveur découplée, articulée autour de deux applications communiquant exclusivement par requêtes HTTP au format JSON. Le backend (API REST FastAPI) centralise la logique métier, les calculs d'indicateurs, le contrôle des droits d'accès, les requêtes vers PostgreSQL ainsi que la collecte et le nettoyage des flux externes ILOSTAT. Le frontend (application web Streamlit) constitue l'interface utilisateur, gère la navigation et la session, produit les visualisations interactives et assemble les rapports PDF téléchargeables sans jamais accéder directement à la base de données.

Le diagramme de packages #std.link(<fig-packages>)[#text(fill: ocean, weight: "bold")[#underline[(voir l'annexe A)]]] illustre la manière dont les différentes couches de l'application interagissent entre elles. La première couche correspond au frontend, qui permet à l'utilisateur de se connecter, de naviguer dans l'interface et d'afficher les visualisations graphiques. La deuxième couche est l'API (controller et model), qui réceptionne et valide les requêtes de l'utilisateur avant de les transmettre au serveur. La couche de services (#NormalTok("service"); et #NormalTok("business_object");) prend ensuite le relais pour appliquer les règles métier et effectuer les calculs statistiques demandés. Enfin, elle s'appuie sur la couche d'accès aux données (#NormalTok("client"); et #NormalTok("dao");). Les flux externes sont récupérés et normalisés, puis transmis aux DAO afin d'être stockés et interrogés dans la base PostgreSQL avant d'être renvoyés sous forme de résultats JSON au frontend.

== Stack technologique et justification des choix
<stack-technologique-et-justification-des-choix>
Développé en #strong[Python], le projet utilise le gestionnaire #strong[uv] (#NormalTok("pyproject.toml"); et #NormalTok("uv.lock");) afin de garantir une résolution rapide des dépendances et une stricte reproductibilité entre postes locaux et conteneurs.

#table(
  columns: (18.37%, 20.41%, 61.22%),
  align: (left,left,left,),
  table.header([Couche / Domaine], [Technologies], [Justification au regard des besoins de LaborScope],),
  table.hline(),
  [#strong[API & Validation]], [#strong[FastAPI], #strong[Uvicorn], #strong[Pydantic]], [Création d'une API rapide, documentée automatiquement et qui vérifie le format des données échangées.],
  [#strong[Interface, DataViz & Export]], [#strong[Streamlit], #strong[Plotly], #strong[Kaleido], #strong[FPDF2]], [Développement d'une interface interactive (courbes et cartes avec Plotly), export des graphiques en images (Kaleido) et génération de rapports PDF téléchargeables (FPDF2)],
  [#strong[Base de données]], [#strong[PostgreSQL 16], #strong[psycopg2]], [Base de données relationnelle adaptée au stockage structuré des indicateurs, des référentiels géographiques et des comptes utilisateurs.],
  [#strong[Traitement & Flux]], [#strong[Pandas], #strong[Requests], #strong[HTTPX]], [Nettoyage et mise en forme des fichiers CSV d'ILOSTAT, requêtes vers l'API externe et tests de l'API.],
  [#strong[Sécurité & Déploiement]], [#strong[PyJWT], #strong[python-dotenv], #strong[PyYAML], #strong[Docker]], [Gestion des connexions par jetons sécurisés, conservation des identifiants en dehors du code source et déploiement simplifié et identique sur n'importe quelle machine.],
)
Des outils d'assurance qualité (pytest, coverage, ruff, mypy, bandit) complètent cette stack pour vérifier les tests, le typage statique et la conformité du code (détaillés en Partie 5).

== Communication, sécurité et déploiement
<communication-sécurité-et-déploiement>
=== Communication client-serveur et accès aux données
<communication-client-serveur-et-accès-aux-données>
Les échanges entre l'interface et le serveur reposent exclusivement sur des requêtes HTTP au format JSON. Côté frontend, l'ensemble des appels vers l'API est centralisé dans une classe dédiée (#NormalTok("APIClient");) qui s'appuie sur une session persistante, cela évite de disperser la logique réseau dans les différentes pages et permet de gérer uniformément les délais d'attente ou les erreurs de connexion.

Côté serveur, l'API FastAPI organise ses points d'entrée autour de routeurs thématiques (#NormalTok("/auth");, #NormalTok("/referentiels");, #NormalTok("/analyses");, #NormalTok("/admin"); et #NormalTok("/journal");). Pour interagir avec PostgreSQL, la classe #NormalTok("DBConnection"); implémente le patron de conception #strong[Singleton] afin de partager une unique connexion sur tout le cycle de vie du backend, évitant ainsi le coût d'ouvertures répétées lors des requêtes analytiques.

=== Sécurisation des accès
<sécurisation-des-accès>
Afin de protéger les comptes utilisateurs et de restreindre l'accès aux fonctionnalités d'administration, aucun mot de passe n'est stocké en clair en base de données, ils sont protégés par un algorithme de hachage sécurisé associé à un sel aléatoire unique. Une fois l'utilisateur connecté, le serveur lui délivre un jeton temporaire (JWT) que l'interface conserve le temps de la session et transmet automatiquement à chaque requête vers une ressource protégée.

=== Conteneurisation et déploiement
<conteneurisation-et-déploiement>
L'application est conteneurisée avec #strong[Docker] et orchestrée via #NormalTok("docker-compose.yml"); autour de trois services isolés communiquant sur le réseau interne créé par Docker Compose :

- #strong[#NormalTok("postgres"); (port 5432) :] base de données PostgreSQL 16 dotée d'un volume persistant \; les scripts SQL du dossier #NormalTok("data/"); y sont montés et exécutés par #NormalTok("make go"); (mode Docker) pour créer le schéma et charger les référentiels \;
- #strong[#NormalTok("backend"); (port 5000) :] serveur API FastAPI exécuté sous Python 3.13 \;
- #strong[#NormalTok("frontend"); (port 8000) :] application web Streamlit dialoguant directement avec le backend via le réseau interne Docker.

#let svc(nom, techno, port, col) = box(width: 4.1cm, radius: 4pt, clip: true, stroke: 0.8pt + col)[
  #block(width: 100%, fill: col, inset: 6pt, spacing: 0pt)[#align(center)[
    #text(fill: white, weight: "bold", size: 10pt, font: sans)[#nom]]]
  #block(width: 100%, fill: white, inset: 7pt, spacing: 0pt)[#align(center)[
    #text(size: 8.5pt)[#techno] \ #text(size: 8pt, fill: muted, font: sans)[port #port]]]
]
#figure(caption: [Les trois services Docker de LaborScope et leur réseau interne.])[
  #block(width: 100%, stroke: (dash: "dashed", paint: ocean, thickness: 1pt), radius: 6pt, inset: (x: 10pt, top: 16pt, bottom: 10pt))[
    #place(top + left, dx: 0pt, dy: -12pt, text(size: 7.5pt, fill: ocean, weight: "bold", font: sans)[RÉSEAU INTERNE DOCKER])
    #align(center)[
      #grid(columns: (4.1cm, 1fr, 4.1cm, 1fr, 4.1cm), align: horizon + center,
        svc([frontend], [Streamlit \ application web], [8000], ocean),
        text(fill: brand, size: 14pt)[⟷],
        svc([backend], [FastAPI \ Python 3.13], [5000], brand),
        text(fill: brand, size: 14pt)[⟷],
        svc([postgres], [PostgreSQL 16 \ volume persistant], [5432], ocean.darken(15%)))
    ]
  ]
]
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
=== Architecture en couches
<architecture-en-couches>
LaborScope est organisé selon une architecture en quatre couches, où chaque couche n'appelle que la couche inférieure. Ce découpage garantit que la logique métier reste indépendante du framework web, et que l'accès aux données est encapsulé.

#figure(caption: [Architecture en couches : chaque flèche est une dépendance autorisée.])[
  #let lay(titre, sous, col: brand, w: 9cm) = box(width: w, fill: col, radius: 3pt, inset: (x: 6pt, y: 5pt))[
    #align(center)[#text(fill: white, weight: "bold", size: 9pt, font: sans)[#titre] \ #text(fill: white, size: 7pt)[#sous]]]
  #let fl = box(height: 11pt, text(fill: brand, size: 9pt)[↓])
  #let ext(w, body, st, fond, r) = box(width: w, stroke: st, fill: fond, radius: r, inset: (x: 6pt, y: 4pt))[
    #align(center, text(size: 8pt, font: sans)[#body])]
  #align(center, stack(dir: ttb, spacing: 2pt,
    ext(3cm, [Utilisateur], 0.6pt + brand, mist, 3pt), fl,
    lay([Présentation], [documentation interactive (Swagger), JSON], col: ocean), fl,
    lay([Contrôleurs], [routes, validation des entrées, authentification]), fl,
    lay([Services], [logique métier, calcul des indicateurs, droits], col: brand.lighten(15%)), fl,
    grid(columns: (4.4cm, 4.4cm), column-gutter: 6pt,
      lay([Client API], [accès à ILOSTAT], col: ocean.darken(10%), w: 4.4cm),
      lay([DAO], [accès à la base], col: ocean.darken(10%), w: 4.4cm)),
    grid(columns: (4.4cm, 4.4cm), column-gutter: 6pt, align(center, fl), align(center, fl)),
    grid(columns: (4.4cm, 4.4cm), column-gutter: 6pt,
      ext(4.4cm, [API ILOSTAT (OIT)], (dash: "dashed", paint: sun, thickness: 1pt), sun.lighten(85%), 3pt),
      ext(4.4cm, [PostgreSQL], 1pt + brand, sun.lighten(70%), 8pt))))
] <fig-archi>
== Zoom détaillé sur un processus central : la collecte de données (F1)
<zoom-détaillé-sur-un-processus-central-la-collecte-de-données-f1>
La collecte est le processus le plus riche de l'application car il traverse toutes les couches et interagit avec trois systèmes externes : l'API ILOSTAT (HTTP), le système de fichiers local (cache CSV) et la base PostgreSQL.

=== Ce que fait l'administrateur
<ce-que-fait-ladministrateur>
L'administrateur clique sur un bouton « Importer les données » dans l'interface. Il peut choisir :

- l'indicateur à collecter (ou tous les indicateurs actifs du référentiel) \;
- la période de temps, comprise entre 2014 et 2026 (l'interface présélectionne 2015-2025).

=== Ce que fait l'application étape par étape
<ce-que-fait-lapplication-étape-par-étape>
#let etape(titre) = block(width: 100%, above: 1.3em, below: 0.6em, fill: ocean.lighten(90%),
  stroke: (left: 3pt + ocean), inset: (left: 10pt, y: 6pt, right: 8pt))[
  #text(weight: "bold", fill: brand, font: sans, size: 10.5pt)[#titre]]
#etape[Étape 1 - Création de la trace d'import]
Dès le lancement de la collecte, l'application enregistre immédiatement une trace de l'opération en base de données avec le statut « en cours ». Cette entrée fait office de journal de suivi. Ainsi, même si le processus venait à échouer en cours de route, l'administrateur pourra toujours consulter l'historique pour savoir quel indicateur a été demandé, à quelle date et pour quel motif l'import n'a pas abouti.

#etape[Étape 2 - Téléchargement sélectif via le cache]
Plutôt que de télécharger systématiquement l'intégralité de la période demandée, l'application commence par vérifier les fichiers déjà archivés localement pour l'indicateur concerné. En identifiant les années déjà couvertes, elle isole uniquement les périodes manquantes et les regroupe par plages consécutives afin de limiter le nombre de requêtes envoyées à l'API d'ILOSTAT. Chaque fichier récupéré est d'abord écrit de façon temporaire avant d'être validé définitivement, ce qui évite de conserver un fichier corrompu en cas de coupure. L'ensemble des fichiers de la période est ensuite rassemblé en mémoire en éliminant les lignes en double. Grâce à ce mécanisme de cache, seul le premier import nécessite de télécharger tout l'historique tandis que les mises à jour suivantes ne récupèrent que les nouvelles données manquantes.

#etape[Étape 3 - Parsing]
Une fois le fichier CSV consolidé, l'application en analyse le contenu ligne par ligne pour le transformer en données exploitables. Pour chaque enregistrement, elle extrait les informations essentielles, c'est-à-dire l'indicateur, le code pays, la période (année ou trimestre) et la valeur numérique, tout en identifiant le sexe (homme, femme ou total) ainsi que la classification éventuelle (tranche d'âge ou profession). Les valeurs non numériques, notamment les données manquantes codées « ... » par ILOSTAT, sont quant à elles détectées et traitées comme des valeurs vides afin de ne pas fausser les analyses.

#etape[Étape 4 - Filtrage par référentiels connus]
Avant d'enregistrer les données, l'application vérifie leur cohérence en écartant toutes les observations rattachées à un pays ou à une classification absents de nos référentiels locaux. ILOSTAT renvoie en effet parfois des zones géographiques ou des codes inconnus qui, sans ce filtrage préalable, seraient rejetés par la base de données pour préserver l'intégrité des informations.

#etape[Étape 5 - Déduplication et upsert]
Avant l'enregistrement, l'application élimine en mémoire les éventuels doublons en vérifiant chaque combinaison unique d'indicateur, de pays, de période, de sexe et de classification, afin d'éviter tout conflit lors de l'envoi groupé. Les données sont ensuite transmises en bloc à la base de données via une opération qui insère les nouvelles observations et met à jour celles déjà existantes. Ce fonctionnement permet de relancer un import sur une même période, ne crée aucun doublon et se contente d'actualiser les valeurs déjà enregistrées.

#etape[Étape 6 - Mise à jour de la trace d'import]
Quelle que soit l'issue de la collecte, l'application clôture le suivi en mettant à jour la trace d'import avec son statut final (succès ou échec), le nombre de lignes traitées, la date de fin et, le cas échéant, le message d'erreur. Si un incident survient durant l'enregistrement des données, l'opération en cours est immédiatement annulée afin de laisser la base de données dans un état sain, ce qui permet ensuite de consigner l'échec dans l'historique.

#figure(caption: [Diagramme de séquence de la collecte de données.])[
  #align(center, block(width: 100%, stroke: 0.6pt + brand.lighten(55%), radius: 3pt, clip: true, inset: 0pt, fill: white)[
    #image("images/diagramme_sequence_collecte.png", width: 100%)])
]
=== Points clés de conception dans ce processus
<points-clés-de-conception-dans-ce-processus>
Le processus d'import est conçu pour être idempotent c'est-à-dire que relancer une collecte sur les mêmes données ne crée ni doublons ni effets indésirables, les enregistrements existants étant simplement mis à jour. Pour éviter de re-télécharger l'intégralité des fichiers à chaque mise à jour, #NormalTok("IlostatClient"); ne récupère que les données manquantes (par exemple l'année 2025 si la période 2020-2024 est déjà présente). En ce qui concerne la tolérance aux erreurs, une valeur invalide dans les données sources ne fait pas échouer l'ensemble de l'import, elle est simplement ignorée tandis que le reste des données est traité normalement. Par ailleurs, si un import échoue à mi-chemin, la base de données est remise dans un état propre afin qu'aucune transaction ne reste bloquée. Enfin, chaque opération est journalisée via #NormalTok("ImportDonnees"); avec sa date, son volume et son statut (succès ou échec), permettant à l'administrateur de consulter l'historique complet.

== Aperçu synthétique des autres fonctionnalités
<aperçu-synthétique-des-autres-fonctionnalités>
=== F2 - Filtrage et consultation
<f2---filtrage-et-consultation>
La consultation des données repose sur un mécanisme de recherche qui s'adapte aux critères sélectionnés par l'utilisateur (pays, indicateur, période, etc.). Afin de garantir la sécurité de la base de données et de prévenir tout risque d'injection SQL, seuls les critères de filtrage explicitement autorisés sont acceptés, toute demande non reconnue étant immédiatement rejetée. De plus, les valeurs recherchées sont transmises de manière sécurisée et isolée, sans jamais être insérées directement dans le texte des requêtes envoyées à la base.

=== F3 - Analyse temporelle
<f3---analyse-temporelle>
L'analyse temporelle permet d'observer l'évolution d'un indicateur au fil des années pour un pays ou un ensemble de pays donné. L'utilisateur sélectionne l'indicateur, le pays et la période qui l'intéressent, et le système lui présente la série de valeurs collectées, année après année. On peut également visualiser l'évolution du taux d'emploi et la variation de celui-ci aux cours des années.

=== F4 - Comparaison entre pays
<f4---comparaison-entre-pays>
La comparaison entre pays s'appuie sur la même logique de récupération des données que la fonctionnalité F3, mais est adaptée à une vue d'ensemble : plutôt que d'extraire tout l'historique d'un pays, le système ne récupère que la donnée la plus récente pour chacun des pays sélectionnés. Les résultats sont classés par ordre décroissant, ce qui permet à l'interface de mettre en évidence les valeurs extrêmes sans nécessiter de traitement supplémentaire lors de l'affichage. Ainsi, le pays le plus élevé figure en tête et le plus bas en fin de liste. L'utilisateur peut également comparer le taux d'emploi et sa variation au cours du temps, entre les pays.

=== F5 - Croisement d'indicateurs
<f5---croisement-dindicateurs>
La comparaison de plusieurs indicateurs consiste à construire une série de données distincte pour chacun des indicateurs sélectionnés, avant de les regrouper au sein d'un même groupe pour une meilleure visualisation. Comme les indicateurs comparés reposent sur des échelles différentes, l'unité de mesure est intégrée dans le titre de chaque série afin d'en assurer une lecture claire. Enfin, si aucune donnée n'est disponible pour un indicateur sur le pays choisi, celui-ci est automatiquement écarté pour éviter d'afficher des courbes vides sur le graphique.

=== F6 - Authentification et gestion des droits
<f6---authentification-et-gestion-des-droits>
L'accès à l'application est sécurisé par un système de jetons de connexion signés, tandis que les mots de passe ne sont jamais conservés en clair mais protégés par un hachage sécurisé avec sel aléatoire. Le contrôle des droits repose sur deux vérifications. La première est de s'assurer que l'utilisateur est bien authentifié. La seconde est de vérifier qu'il dispose du statut d'administrateur pour les opérations sensibles. Un choix de conception important a été de recontrôler le rôle et l'état du compte en base de données à chaque requête plutôt que de se fier uniquement aux informations contenues dans le jeton : ainsi, la promotion ou la désactivation d'un compte prend effet immédiatement, sans avoir à attendre l'expiration du jeton (60 minutes par défaut, durée réglable via la variable #NormalTok("JWT_DUREE_MINUTES");).

En parallèle, un mécanisme de traçabilité enregistre chaque action significative réalisée sur la plateforme (connexion, lancement d'une collecte, modification ou suppression de données). Chaque entrée consignée associe l'auteur de l'opération, l'horodatage, la nature de l'action et un descriptif qui permet aux administrateurs de consulter l'historique et de suivre précisément qui a effectué quelle action.

=== FO1 - Cartographie interactive
<fo1---cartographie-interactive>
La vue cartographique récupère les données d'une période unique pour l'ensemble des pays disponibles, afin d'associer une seule valeur à chaque pays. L'interface utilise ensuite ces résultats pour colorer dynamiquement une carte interactive selon un dégradé de couleurs proportionnel aux valeurs observées. Enfin, la réutilisation de la même structure de données que celle des comparaisons entre pays (F4) simplifie la conception de l'interface. Une seule logique d'affichage permet ainsi de gérer à la fois les graphiques en barres et la carte.

=== FO2 - Génération de rapports PDF
<fo2---génération-de-rapports-pdf>
La création d'un rapport automatisé repose sur un processus en trois temps. Le système commence par récupérer les séries de données via les modules d'analyse existants (F3 et F4), génère ensuite les graphiques correspondants sous forme d'images, puis assemble l'ensemble dans un document PDF réunissant ces visuels, un tableau récapitulatif et une synthèse automatique des principaux résultats. Le document est assemblé directement par l'interface (bibliothèque FPDF2, graphiques exportés avec Kaleido) puis proposé immédiatement au téléchargement \; il n'est pas conservé en base de données.

== Cas d'utilisation concret (Démonstration)
<cas-dutilisation-concret-démonstration>
#block[
#callout(
body: 
[
#strong[Contexte :] Marie, chargée d'études économiques à l'INSEE, doit alimenter son rapport sur les mesures exceptionnelles prises par le Luxembourg pendant la pandémie du Covid-19. Elle souhaite analyser l'évolution du taux d'emploi des 15-24 ans au Luxembourg sur la période 2016-2025, afin de quantifier l'impact de la pandémie sur le marché du travail luxembourgeois et le comparer à celui de pays voisins (France, Italie, Royaume-Uni).

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
#let etape(titre) = block(width: 100%, above: 1.3em, below: 0.6em, fill: ocean.lighten(90%),
  stroke: (left: 3pt + ocean), inset: (left: 10pt, y: 6pt, right: 8pt))[
  #text(weight: "bold", fill: brand, font: sans, size: 10.5pt)[#titre]]
#let capture(chemin, legende, w: 100%) = figure(caption: legende)[
  #align(center, block(width: w, stroke: 0.6pt + brand.lighten(55%), radius: 3pt, clip: true, inset: 0pt)[
    #image(chemin, width: 100%)])
]
#etape[Étape 1 - Connexion]
Marie se connecte à l'application après avoir créé un compte.

#capture("images/capture_connexion.png", [Page de connexion de LaborScope.], w: 85%)
#etape[Étape 2 - Analyse temporelle (F3)]
Marie sélectionne dans l'interface :

#capture("images/capture_filtres.png", [Sélection des filtres de l'analyse temporelle.])
Le graphique ci-dessous est affiché :

#capture("images/capture_evolution_luxembourg.png", [Évolution temporelle du taux d'emploi au Luxembourg.])
On observe un ralentissement de l'évolution du taux d'emploi en 2020 (confinement) suivi d'une reprise progressive. La période 2019 sert de référence « pré-pandémie ».

#capture("images/capture_variations_luxembourg.png", [Variations annuelles du taux d'emploi au Luxembourg.])
Comme la majorité des pays, le Luxembourg a connu une baisse du taux d'emploi avec une diminution de 0,5% en 2020. Cependant, la réaction est très rapide : le taux d'emploi évolue en 2021 de 2% par rapport à 2020. Marie se demande si la tendance est la même pour les autres pays.

#etape[Étape 3 - Comparaison entre pays (F4)]
Marie passe en mode « Comparaison pays » et sélectionne le Luxembourg, la France, le Royaume-Uni et l'Italie. Elle décide de comparer les taux d'emploi entre les pays :

#capture("images/capture_comparaison_pays.png", [Comparaison du taux d'emploi entre les quatre pays.])
La plupart des pays ont connu une baisse ou une stagnation du taux d'emploi de 2019 à 2021. Cependant le Luxembourg voit une nette augmentation de 2020 à 2021. Marie souhaite illustrer cette nette différence en passant sur le mode “Variations” :

#capture("images/capture_variations_pays.png", [Variations annuelles du taux d'emploi par pays.])
La différence est claire, une augmentation de 2% sur une année, la plus haute variation parmi les pays cités. Marie peut désormais retranscrire ses informations dans son rapport.

#block[
#callout(
body: 
[
Une conception en couches, appuyée sur l'héritage (classifications d'âge et de profession) et un singleton (connexion à la base), qui isole la logique métier du reste \; le processus de collecte illustre le rôle de chaque couche.

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
== Modèle physique des données (MPD) et relations
<modèle-physique-des-données-mpd-et-relations>
=== Schéma relationnel
<schéma-relationnel>
Le modèle physique de données traduit le diagramme de classes en schéma relationnel. Il réunit l'ensemble des tables et met en évidence les clés primaires, les clés étrangères et les relations entre elles.

#let mpd-hh = 0.62cm
#let mpd-rh = 0.39cm
#let mpd-h(n) = mpd-hh + n * mpd-rh
#let mpd-line(x1, y1, x2, y2) = place(top + left, line(start: (x1, y1), end: (x2, y2), stroke: 0.8pt + muted))
#let mpd-lab(x, y, t) = place(top + left, dx: x, dy: y, text(size: 6pt, weight: "bold", fill: brand, font: sans)[#t])
#let mpd-row(nom, typ, flags) = {
  let pk = flags.contains("PK")
  let fk = flags.contains("FK")
  let uq = flags.contains("UQ")
  grid(columns: (1fr, auto), column-gutter: 3pt,
    [#text(weight: if pk { "bold" } else { "regular" })[#nom]#if pk [#text(fill: sun.darken(25%), size: 5.5pt, weight: "bold")[ PK]]#if fk [#text(fill: ocean, size: 5.5pt, weight: "bold")[ FK]]#if uq [#text(fill: brand, size: 5.5pt, weight: "bold")[ UQ]]],
    text(fill: muted, size: 6pt)[#typ])
}
#let mpd-table(nom, col, x, y, w, rows) = place(top + left, dx: x, dy: y,
  block(width: w, height: mpd-h(rows.len()), clip: true, stroke: 0.7pt + col, radius: 2.5pt, fill: white)[
    #block(width: 100%, height: mpd-hh, fill: col, inset: (x: 6pt), spacing: 0pt)[
      #align(left + horizon, text(fill: white, weight: "bold", size: 8pt, font: sans)[#nom])]
    #for (i, r) in rows.enumerate() {
      block(width: 100%, height: mpd-rh, spacing: 0pt, inset: (x: 6pt),
        fill: if calc.odd(i) { mist } else { white },
        align(horizon, text(size: 6.5pt)[#mpd-row(r.at(0), r.at(1), r.at(2))]))
    }
  ])
#figure(caption: [Modèle physique des données de LaborScope.])[
  #block(width: 100%, height: 13.2cm, breakable: false)[
    // --- connecteurs (dessinés d'abord, sous les tables) ---
    // Indicateur -> Observation
    #mpd-line(7.7cm, 2.57cm, 7.7cm, 3.7cm)
    // Pays -> Observation
    #mpd-line(4.6cm, 4.315cm, 5.0cm, 4.315cm)
    #mpd-line(5.0cm, 4.315cm, 5.0cm, 5.295cm)
    #mpd-line(5.0cm, 5.295cm, 5.4cm, 5.295cm)
    // Classification -> Observation
    #mpd-line(4.6cm, 6.515cm, 5.0cm, 6.515cm)
    #mpd-line(5.0cm, 6.515cm, 5.0cm, 6.855cm)
    #mpd-line(5.0cm, 6.855cm, 5.4cm, 6.855cm)
    // Import_donnees -> Observation
    #mpd-line(10.8cm, 3.215cm, 10.4cm, 3.215cm)
    #mpd-line(10.4cm, 3.215cm, 10.4cm, 7.245cm)
    #mpd-line(10.4cm, 7.245cm, 10.0cm, 7.245cm)
    // Indicateur -> Import_donnees
    #mpd-line(10.0cm, 0.815cm, 13.1cm, 0.815cm)
    #mpd-line(13.1cm, 0.815cm, 13.1cm, 2.4cm)
    // Utilisateur -> Import_donnees
    #mpd-line(9.6cm, 9.7cm, 9.6cm, 8.96cm)
    #mpd-line(9.6cm, 8.96cm, 13.1cm, 8.96cm)
    #mpd-line(13.1cm, 8.96cm, 13.1cm, 6.53cm)
    // Utilisateur -> Journal_activite
    #mpd-line(4.6cm, 10.515cm, 5.4cm, 10.515cm)
    // Utilisateur -> Rapport
    #mpd-line(10.0cm, 10.515cm, 10.8cm, 10.515cm)
    // --- cardinalités ---
    #mpd-lab(7.8cm, 2.6cm, [1])
    #mpd-lab(7.8cm, 3.35cm, [N])
    #mpd-lab(4.62cm, 3.98cm, [1])
    #mpd-lab(5.12cm, 4.96cm, [N])
    #mpd-lab(4.62cm, 6.18cm, [1])
    #mpd-lab(5.12cm, 6.52cm, [N])
    #mpd-lab(10.45cm, 2.88cm, [1])
    #mpd-lab(10.03cm, 6.93cm, [N])
    #mpd-lab(10.05cm, 0.48cm, [1])
    #mpd-lab(13.2cm, 2.05cm, [N])
    #mpd-lab(9.7cm, 9.35cm, [1])
    #mpd-lab(13.2cm, 6.58cm, [N])
    #mpd-lab(5.15cm, 10.18cm, [1])
    #mpd-lab(4.62cm, 10.18cm, [N])
    #mpd-lab(10.2cm, 10.18cm, [1])
    #mpd-lab(10.62cm, 10.18cm, [N])
    // --- référentiels ---
    #mpd-table("Indicateur", ocean, 5.4cm, 0cm, 4.6cm, (
      ("code_indicateur", "varchar(50)", "PK"), ("description", "varchar(255)", ""), ("unite", "varchar(50)", ""),
      ("source", "varchar(100)", ""), ("actif", "boolean", "")))
    #mpd-table("Pays", ocean, 0cm, 3.5cm, 4.6cm, (
      ("code_pays", "varchar(10)", "PK"), ("nom_pays", "varchar(100)", "")))
    #mpd-table("Classification", ocean, 0cm, 5.7cm, 4.6cm, (
      ("code", "varchar(50)", "PK"), ("libelle", "varchar(255)", ""), ("type", "varchar(20)", ""),
      ("age_min", "integer", ""), ("age_max", "integer", ""), ("valeur", "varchar(100)", "")))
    // --- données collectées ---
    #mpd-table("Observation", brand, 5.4cm, 3.7cm, 4.6cm, (
      ("id", "bigserial", "PK"), ("code_indicateur", "varchar(50)", "FK"), ("code_pays", "varchar(10)", "FK"),
      ("periode", "varchar(20)", ""), ("valeur", "numeric", ""), ("sexe", "varchar(10)", ""),
      ("code_classification", "varchar(50)", "FK"), ("import_id", "integer", "FK"),
      ("source", "varchar(100)", ""), ("date_import", "timestamp", "")))
    #mpd-table("Import_donnees", brand, 10.8cm, 2.4cm, 4.6cm, (
      ("id", "serial", "PK"), ("indicateur_code", "varchar(50)", "FK"), ("utilisateur_id", "integer", "FK"),
      ("date_debut", "timestamp", ""), ("date_fin", "timestamp", ""), ("statut", "varchar(20)", ""),
      ("nombre_lignes", "integer", ""), ("fichier_source", "varchar(255)", ""), ("message_erreur", "text", "")))
    // --- comptes et traçabilité ---
    #mpd-table("Utilisateur", sun.darken(20%), 5.4cm, 9.7cm, 4.6cm, (
      ("id", "serial", "PK"), ("nom_utilisateur", "varchar(50)", "UQ"), ("mot_de_passe_hash", "varchar(256)", ""),
      ("role", "varchar(20)", ""), ("actif", "boolean", ""), ("date_creation", "timestamp", ""), ("derniere_connexion", "timestamp", "")))
    #mpd-table("Journal_activite", sun.darken(20%), 0cm, 9.31cm, 4.6cm, (
      ("id", "bigserial", "PK"), ("utilisateur_id", "integer", "FK"), ("action", "varchar(100)", ""),
      ("cible", "varchar(255)", ""), ("details", "text", ""), ("date_heure", "timestamp", "")))
    #mpd-table("Rapport", sun.darken(20%), 10.8cm, 9.31cm, 4.6cm, (
      ("id", "serial", "PK"), ("utilisateur_id", "integer", "FK"), ("titre", "varchar(255)", ""),
      ("description", "text", ""), ("date_creation", "timestamp", ""), ("fichier_path", "varchar(255)", ""), ("statut", "varchar(20)", "")))
    // --- légende ---
    #place(top + left, dx: 0cm, dy: 0cm, block(width: 4.6cm, stroke: 0.6pt + brand.lighten(60%), radius: 3pt, inset: 7pt, fill: mist)[
      #set text(size: 7pt)
      #set par(leading: 0.5em, justify: false)
      #text(size: 6.5pt, tracking: 0.8pt, fill: muted, font: sans)[LÉGENDE] \
      #box(width: 7pt, height: 7pt, fill: ocean, radius: 1pt, baseline: 1pt) #h(3pt) Référentiels \
      #box(width: 7pt, height: 7pt, fill: brand, radius: 1pt, baseline: 1pt) #h(3pt) Données collectées \
      #box(width: 7pt, height: 7pt, fill: sun.darken(20%), radius: 1pt, baseline: 1pt) #h(3pt) Comptes et traçabilité \
      #v(2pt)
      #text(fill: sun.darken(25%), weight: "bold")[PK] clé primaire · #text(fill: ocean, weight: "bold")[FK] clé étrangère \
      #text(fill: brand, weight: "bold")[UQ] unique])
  ]
]
=== Justification des choix de modélisation
<justification-des-choix-de-modélisation>
Le modèle physique de #NormalTok("LaborScope"); repose sur une table centrale #NormalTok("observation"); qui joue le rôle de table d'association, elle relie simultanément #NormalTok("Indicateur");, #NormalTok("Pays"); et #NormalTok("Classification"); (âge ou profession), le sexe étant porté directement comme attribut de l'observation. Cette approche évite de créer des tables de jointure séparées pour chaque relation N à N, car une observation est portée par cette table uniquement. Par exemple, l'observation du taux d'emploi des femmes de 25-34 ans en France en 2023 se retrouve dans une seule ligne qui référence à la fois l'indicateur, le pays et la classification d'âge, et précise le sexe, sans duplication des attributs de ces entités dans d'autres tables.

Les contraintes SQL mises en place garantissent la cohérence des données sans surcharger le modèle. Les clés étrangères assurent qu'une “observation” ne peut exister que si l'indicateur, le pays et, lorsqu'elle est renseignée, la classification qu'elle cite sont effectivement présents dans leurs tables respectives \; le sexe est quant à lui limité à #NormalTok("homme");, #NormalTok("femme"); ou #NormalTok("total"); par une contrainte #NormalTok("CHECK");. Les contraintes #NormalTok("CHECK"); bornent les valeurs possibles à un ensemble connu (par exemple, le #NormalTok("statut"); d'un import est limité à #NormalTok("'en_cours'");, #NormalTok("'succes'"); ou #NormalTok("'echec'");), ce qui élimine les données incohérentes. Enfin, la contrainte d'unicité #NormalTok("(code_indicateur, code_pays, periode, sexe, code_classification)"); sur #NormalTok("observation"); garantit qu'une même mesure n'est jamais enregistrée deux fois.

== Stockage des données
<stockage-des-données>
Les données de référence (pays, indicateurs, classifications) sont chargées une seule fois en base au démarrage du système, ce sont des référentiels immuables qui servent de dictionnaires à l'ensemble de l'application. En revanche, les observations (les valeurs mesurées) sont écrites en base PostgreSQL lors d'une action de collecte déclenchée par l'utilisateur. Puis elles sont mises à jour par un upsert si de nouvelles valeurs arrivent pour la même combinaison indicateur#NormalTok("/pays/période/sexe/classification");.

Le système met en place un mécanisme pour éviter de sur-solliciter l'ILOSTAT. D'abord, au niveau fichier, les CSV téléchargés sont archivés localement. Avant de faire une requête réseau, le système vérifie quelles années sont déjà couvertes par les fichiers existants (seules les années manquantes sont demandées à l'API). Ensuite, au niveau base de données, une fois les données parsées et insérées, toutes les lectures ultérieures (analyses, graphiques, calculs de taux) se font directement avec la base, sans aucun appel à ILOSTAT. L'API n'est donc contactée qu'au moment de la collecte, uniquement pour les données réellement manquantes.

== Normalisation et formes normales
<normalisation-et-formes-normales>
Notre schéma a été conçu en respectant les trois premières formes normales. Ci-dessous, chaque forme est illustrée par un exemple concret tiré de notre modèle.

- #strong[1FN (atomicité)] : La table observation respecte la première forme normale, elle possède une clé primaire id (#NormalTok("BIGSERIAL");), chaque cellule ne contient qu'une seule valeur atomique et il n'y a pas de groupe répété ni de liste dans un attribut. Par exemple, l'attribut valeur de type #NormalTok("NUMERIC"); stocke un unique chiffre par ligne (ex. 24.5300), et l'attribut #NormalTok("sexe"); ne prend qu'une seule valeur parmi #NormalTok("homme");, #NormalTok("femme"); ou #NormalTok("total");. Chaque table du schéma suit ce principe : pays a #NormalTok("code_pays"); comme clé, indicateur a #NormalTok("code_indicateur");, et aucun attribut ne contient un ensemble de valeurs multiples.

- #strong[2FN] : Toutes les clés primaires du schéma sont simples (un seul attribut), ce qui fait que la 2FN est formellement respectée puisqu'il n'existe pas de dépendance partielle possible (un attribut non-clé ne peut pas dépendre d'une partie d'une clé composite). Par exemple, dans la table observation, la clé primaire est #NormalTok("id"); et tous les autres attributs (#NormalTok("code_indicateur");, #NormalTok("code_pays");, #NormalTok("periode");, #NormalTok("valeur");, etc.) dépendent entièrement de cette clé. Cependant, la table classification présente une différence : les attributs #NormalTok("age_min");, #NormalTok("age_max"); et #NormalTok("valeur"); ne sont pas tous pertinents pour chaque ligne (si #NormalTok("type"); = #NormalTok("age");, seule #NormalTok("valeur"); est nulle \; si #NormalTok("type"); = #NormalTok("occupation");, seuls #NormalTok("age_min"); et #NormalTok("age_max"); sont nuls). C'est un attribut conditionnel qui permet de séparer la classification pour les deux indicateurs (#NormalTok("occupation"); pour emploi par sexe et profession, et #NormalTok("âge"); pour population en âge de travailler par sexe et âge). Cette table respecte tout de même la 2FN.

- #strong[3FN] : La 3FN impose qu'aucun attribut non-clé ne dépende d'un autre attribut non-clé (dépendance transitive). La table utilisateur en est un bon exemple de respect, #NormalTok("mot_de_passe_hash");, #NormalTok("role");, #NormalTok("actif"); dépendent tous directement de #NormalTok("id"); sans passer par un autre attribut. Le modèle physique des données respecte donc les 3 formes normales.

#block[
#callout(
body: 
[
Un schéma relationnel de huit tables, organisé autour d'une table centrale d'observations reliée à trois référentiels (indicateur, pays, classification d'âge ou de profession), le sexe étant contrôlé par une contrainte #NormalTok("CHECK");, et protégé par des clés étrangères, des contraintes #NormalTok("CHECK"); et une contrainte d'unicité. La base sert aussi de cache entre l'application et l'API ILOSTAT, celle-ci n'est contactée qu'au moment de la collecte, et uniquement pour les données manquantes.

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

Plutôt que de diviser le travail par fonctionnalité où un membre développe une feature de bout en bout, nous avons opté pour une répartition du travail par couche technique. Chaque membre est ainsi devenu garant de la solidité et de la logique de son propre composant. Si ce choix a permis à chacun de monter rapidement en compétence sur sa technologie (PostgreSQL, FastAPI, Streamlit), il a également exigé une communication et une rigueur en matière d'organisation, les formats de données et les interfaces entre la DAO, les Services et l'API devaient être parfaitement définis en amont pour que les couches s'emboîtent sans erreur.

=== Planification
<planification>
Le suivi de notre avancement s'est appuyé sur le diagramme de Gantt initialement construit lors de la phase d'analyse. Face à la réalité du développement, notamment la complexité de l'intégration entre les couches développées en parallèle, nous n'avons pas pu tenir toutes les grandes lignes prévisionnelles au jour près. Certains modules ont nécessité plus de temps de débogage ou d'appropriation que prévu.

Cependant, ces décalages ont été totalement maîtrisés et résorbés grâce aux trois journées d'immersion. Ce temps de travail intensif, réunissant toute l'équipe en présentiel, a agi comme un véritable catalyseur. Il nous a permis de réaliser l'intégration finale des différentes couches, de lever les points bloquants de communication entre l'API et le Front-end, et de stabiliser l'application pour livrer un produit fonctionnel dans les délais imposés. Par ailleurs, lors de ces jours d'immersion, nous avons eu l'occasion de faire une première présentation en direct du projet. Cela nous a permis de recevoir des remarques constructives de la part de notre encadrant que nous avons ensuite pris en compte afin d'améliorer l'application.

#let jx(j, m) = if m == 8 { j - 30 } else if m == 9 { j + 1 } else if m == 10 { j + 31 } else { j + 62 }
#let gantt-jours = 84
#let gantt-jalons = ((16, 9, "J1"), (2, 10, "J2"), (8, 10, "J3"), (22, 10, "J4"), (5, 11, "J5"), (15, 11, "J6"), (20, 11, "J7"))
#let gantt-phases = (
  ([Phase 1 · Dossier d'analyse (1 – 16 septembre)], (
    ([Contexte, besoins et utilisateurs], "P1", (1, 9, 5, 9), 5),
    ([Exploration de l'API ILOSTAT], "P2", (1, 9, 8, 9), 8),
    ([Diagramme de cas d'utilisation], "P4", (4, 9, 9, 9), 6),
    ([Diagramme de classes métier], "P4", (8, 9, 12, 9), 5),
    ([Modèle de données et script SQL], "P3", (7, 9, 12, 9), 6),
    ([Architecture en couches], "P1", (8, 9, 12, 9), 5),
    ([Maquettes et diagramme de séquence], "P5", (8, 9, 13, 9), 6),
    ([Liste des composants et charges], "P1", (10, 9, 13, 9), 4),
    ([Diagramme de Gantt], "P5", (11, 9, 13, 9), 3),
    ([Export PDF et dépôt du dossier], "P1", (13, 9, 16, 9), 4))),
  ([Phase 2 · Développement (17 septembre – 5 novembre)], (
    ([Partage des responsabilités techniques], "P1", (17, 9, 18, 9), 2),
    ([Socle technique : dépôt, CI, base], "P1", (17, 9, 23, 9), 7),
    ([Récupération des données ILOSTAT], "P2", (24, 9, 7, 10), 14),
    ([Parsing et nettoyage], "P2", (30, 9, 8, 10), 9),
    ([Couche d'accès et chargement en base], "P3", (24, 9, 8, 10), 15),
    ([Tests du parser et des accès aux données], "P1", (1, 10, 8, 10), 8),
    ([Analyse temporelle], "P4", (9, 10, 17, 10), 9),
    ([Comparaison entre pays], "P4", (14, 10, 22, 10), 9),
    ([Interface et graphiques], "P5", (9, 10, 22, 10), 14),
    ([Tests des services d'analyse], "P1", (19, 10, 23, 10), 5),
    ([Comparaison multi-indicateurs], "P4", (23, 10, 30, 10), 8),
    ([Authentification et rôles], "P3", (23, 10, 2, 11), 11),
    ([Cartographie choroplèthe], "P5", (23, 10, 30, 10), 8),
    ([Administration et journal d'activité], "P5", (30, 10, 5, 11), 7),
    ([Prévision de tendance], "P2", (28, 10, 5, 11), 9))),
  ([Phase 3 · Tests et rapport final (6 – 20 novembre)], (
    ([Génération automatique de rapports PDF], "P5", (6, 11, 12, 11), 7),
    ([Tests d'intégration], "P1", (6, 11, 13, 11), 8),
    ([Temps de traitement et optimisation], "P2", (6, 11, 12, 11), 7),
    ([Rédaction du rapport final], "P1", (6, 11, 18, 11), 13),
    ([Corrections, refactoring, documentation], "P1", (11, 11, 15, 11), 5),
    ([Diagrammes et captures d'écran], "P5", (16, 11, 18, 11), 3),
    ([Relecture et mise en forme], "P1", (18, 11, 19, 11), 2),
    ([Archive du code et dépôt], "P3", (19, 11, 20, 11), 2))),
)
#let gantt-ms = gantt-jalons.map(j => jx(j.at(0), j.at(1)))
#let gantt-wk(d) = calc.rem(d, 7) == 6 or calc.rem(d, 7) == 0
#let gantt-fmt(j, m) = [#if j < 10 [0]#j/#if m < 10 [0]#m]
#page(flipped: true, margin: (x: 1.5cm, top: 2.2cm, bottom: 1.6cm))[
  #figure(kind: image, supplement: [Figure], caption: [Diagramme de Gantt du projet (31 août – 22 novembre 2026).])[
    #set text(size: 7.2pt, font: sans)
    #show table: set text(size: 7.2pt, font: sans)
    #table(
      columns: (6.2cm, 0.95cm, 1.05cm, 1.05cm, 0.85cm) + (1fr,) * gantt-jours,
      align: (left + horizon, center + horizon, center + horizon, center + horizon, center + horizon) + (center + horizon,) * gantt-jours,
      inset: (x: 0pt, y: 2.9pt),
      stroke: (x, y) => (
        bottom: 0.25pt + muted.lighten(65%),
        right: if x >= 4 and gantt-ms.contains(x - 4) { (paint: sun, thickness: 0.5pt, dash: "dashed") } else { none }),
      // ---- en-tête : mois ----
      table.cell(fill: brand, inset: (x: 4pt, y: 3pt))[#text(fill: white, weight: "bold")[Tâche]],
      table.cell(fill: brand)[#text(fill: white, weight: "bold")[Resp.]],
      table.cell(fill: brand)[#text(fill: white, weight: "bold")[Début]],
      table.cell(fill: brand)[#text(fill: white, weight: "bold")[Fin]],
      table.cell(fill: brand)[#text(fill: white, weight: "bold")[Jours]],
      table.cell(colspan: 31, fill: brand)[#text(fill: white, weight: "bold", size: 7.5pt)[SEPTEMBRE]],
      table.cell(colspan: 31, fill: brand.lighten(12%))[#text(fill: white, weight: "bold", size: 7.5pt)[OCTOBRE]],
      table.cell(colspan: 22, fill: brand)[#text(fill: white, weight: "bold", size: 7.5pt)[NOVEMBRE]],
      // ---- en-tête : jours ----
      ..range(0, 5).map(_ => table.cell(fill: brand)[]),
      ..range(1, gantt-jours + 1).map(d => {
        let j = if d == 1 { 31 } else if d <= 31 { d - 1 } else if d <= 62 { d - 31 } else { d - 62 }
        table.cell(fill: if gantt-wk(d) { brand.lighten(18%) } else { brand })[#text(fill: white, size: 4.6pt)[#j]]
      }),
      // ---- jalons ----
      table.cell(colspan: 5, align: left + horizon, inset: (x: 4pt, y: 2.9pt))[#text(weight: "bold", fill: muted)[Jalons]],
      ..range(1, gantt-jours + 1).map(d => {
        let k = gantt-ms.position(m => m == d)
        if k != none { table.cell(fill: sun)[#text(fill: white, weight: "bold", size: 4pt)[#gantt-jalons.at(k).at(2)]] }
        else { table.cell(fill: if gantt-wk(d) { mist } else { none })[] }
      }),
      // ---- phases et tâches ----
      ..gantt-phases.map(ph => (
        table.cell(colspan: 5 + gantt-jours, fill: ocean.lighten(86%), align: left + horizon, inset: (x: 4pt, y: 3.0pt))[
          #text(weight: "bold", fill: brand, size: 7.8pt)[#ph.at(0)]],
        ..ph.at(1).map(t => {
          let d0 = jx(t.at(2).at(0), t.at(2).at(1))
          let d1 = jx(t.at(2).at(2), t.at(2).at(3))
          (
            table.cell(align: left + horizon, inset: (x: 4pt, y: 2.9pt))[#t.at(0)],
            [#text(fill: muted, weight: "bold")[#t.at(1)]],
            [#text(fill: muted)[#gantt-fmt(t.at(2).at(0), t.at(2).at(1))]],
            [#text(fill: muted)[#gantt-fmt(t.at(2).at(2), t.at(2).at(3))]],
            [#text(fill: muted)[#t.at(3)]],
            ..range(1, gantt-jours + 1).map(d => table.cell(
              fill: if d >= d0 and d <= d1 { ocean } else if gantt-wk(d) { mist } else { none })[]),
          )
        }).flatten(),
      )).flatten(),
    )
    #v(4pt)
    #set text(size: 7.5pt, font: sans)
    #grid(columns: (auto, auto, auto, 1fr), column-gutter: 14pt, align: left + horizon,
      [#box(width: 8pt, height: 6pt, fill: ocean, radius: 0.5pt) #h(2pt) Tâche planifiée],
      [#box(width: 8pt, height: 6pt, fill: sun, radius: 0.5pt) #h(2pt) Jalon],
      [#box(width: 8pt, height: 6pt, fill: mist, stroke: 0.3pt + muted.lighten(50%), radius: 0.5pt) #h(2pt) Week-end],
      [*P1* Chef de projet & qualité · *P2* Data engineer · *P3* Base de données & DAO · *P4* Backend / API · *P5* Frontend / DataViz])
    #v(3pt)
    #grid(columns: (1fr, 1fr, 1fr), column-gutter: 10pt, row-gutter: 3pt, align: left,
      [*J1* · 16/09 — Dossier d'analyse figé, fin de la phase 1],
      [*J2* · 02/10 — Dépôt du dossier d'analyse sur Moodle],
      [*J3* · 08/10 — Base alimentée automatiquement],
      [*J4* · 22/10 — Analyses accessibles via l'API et le front],
      [*J5* · 05/11 — Application complète, fin de la phase 2],
      [*J6* · 15/11 — Gel du code],
      [*J7* · 20/11 — Dépôt final : rapport et code])
  ]
]
== Outils collaboratifs et normes de développement
<outils-collaboratifs-et-normes-de-développement>
=== Outils de communication et de suivi
<outils-de-communication-et-de-suivi>
Travailler à cinq sur une architecture découpée en couches techniques nécessitait une bonne synchronisation. Nous avons utilisé WhatsApp pour les échanges rapides au quotidien et Notion pour le suivi de l'avancement des tâches.

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
Afin de garantir la stabilité de l'application, nous avons mis en place une suite de tests unitaires avec le framework pytest, couvrant les trois couches du back-end. Nous avons ainsi testé la construction des requêtes SQL au niveau des DAO, la logique de nettoyage et de gestion des erreurs des services métier, ainsi que les codes de retour HTTP des contrôleurs de l'API. Pour garantir des tests rapides sans risquer de polluer notre base de données locale, nous avons isolé notre code grâce à l'utilisation de mocks via la bibliothèque #NormalTok("unittest.mock");. Cela consiste concrètement à simuler la base de données pour vérifier les requêtes des DAO sans les exécuter, et nous simulons le client HTTP pour tester les services sans déclencher de vrais téléchargements. Cette méthode permet de réduire le temps d'exécution des tests ainsi que de tester des cas aux limites difficiles à reproduire manuellement, comme une perte de connexion réseau ou la réception d'un fichier corrompu. Chaque test suit le canevas #emph[given / when / then].

#table(
  columns: 3,
  align: (left,center,left,),
  table.header([Couche testée], [Couverture], [Remarque],),
  table.hline(),
  [DAO], [100 %], [Base simulée (mocks)],
  [Services], [96 %], [API externe simulée],
  [Contrôleurs], [85 %], [Routes et validation],
  [#strong[Total]], [95 %], [460 tests],
)
=== Gestion des temps de traitement longs
<gestion-des-temps-de-traitement-longs>
Pour éviter les problèmes de performances liés à l'extraction et l'insertion de millions de lignes via l'API ILOSTAT nous avons fait en sorte que le script vérifie les fichiers déjà présents sur la base de données locale pour ne télécharger que les données manquantes, ce qui réduit considérablement le temps d'exécution. En ce qui concerne la base de données, une insertion ligne par ligne des observations aurait été beaucoup trop lourde. Nous avons donc utilisé une fonction qui permet de faire des insertions en lot avec une seule requête, tout en traitant également les doublons.

=== Résilience face au changement de source de données
<résilience-face-au-changement-de-source-de-données>
Si l'API ILOSTAT venait à fermer demain ou devait être remplacée, nous avons fait en sorte que l'impact sur notre code serait le plus minime possible. Cela est rendu possible par notre découpage en couches et la séparation des responsabilités. Dans notre architecture, l'intégralité du programme, que ce soit la base de données, l'API ou encore les contrôleurs, ignore l'existence d'ILOSTAT. Le traitement de cette source est centralisé dans deux scripts : le script #NormalTok("ilostat_client.py"); gère l'URL et les requêtes, tandis que #NormalTok("parser_service.py"); adapte les données brutes d'ILOSTAT et les transforme en nos objets Python génériques. En cas de changement de source des données, il suffirait de créer un nouveau fichier client et d'ajuster le dictionnaire de renommage. Ainsi, les tables PostgreSQL, les objets métiers et le reste de l'application n'auraient besoin d'aucune modification.

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
#strong[Bilan technique et fonctionnel.] LaborScope atteint son objectif qui est d'offrir un accès simple, sécurisé et comparable aux statistiques mondiales du marché du travail. Le socle obligatoire (F1 à F6) couvre toute la chaîne, de la collecte automatisée des données ILOSTAT à leur visualisation dans l'interface, en passant par l'authentification à deux profils et la traçabilité des actions sensibles. Il est complété par les deux fonctionnalités additionnelles : la cartographie interactive (FO1) et la génération de rapports PDF (FO2). Les tests unitaires, écrits avec pytest sur les trois couches du back-end (DAO, services et contrôleurs), couvrent 95 % du code (100 % des DAO).

#strong[Apports pédagogiques.] Le projet nous a appris à concevoir une application en couches, à justifier des choix techniques, à tester de manière isolée et à travailler à cinq sur un même dépôt. Répartir le travail par couche technique nous a permis de monter rapidement en compétence sur PostgreSQL, FastAPI et Streamlit, mais nous a aussi montré combien les formats de données et les interfaces entre les couches doivent être définis en amont. C'est lors de leur intégration que sont apparus nos principaux retards. Les trois journées d'immersion en présentiel ont été décisives pour les résorber, et la première démonstration en direct du projet nous a apporté des remarques constructives de notre encadrant. Nous avons également été confrontés à d'autres imprévus, comme les données ILOSTAT irrégulières (valeurs manquantes, nomenclatures hétérogènes) qui ont exigé un nettoyage rigoureux, les évolutions de périmètre et les arbitrages entre fonctionnalités.

#strong[Perspectives.] Grâce au découpage en couches, LaborScope peut évoluer sans être reconstruit, l'ajout d'une nouvelle source de données ne demanderait que d'écrire un nouveau client et d'ajuster le dictionnaire de renommage, tandis que de nouveaux indicateurs, de nouvelles analyses statistiques ou de nouveaux profils d'utilisateurs s'inséreraient dans les services et les routeurs existants, sans toucher au reste de l'application.

#heading(level: 1, numbering: none)[Notes individuelles]
<notes-individuelles>
#heading(level: 2, numbering: none)[Jade Colin]
<jade-colin>
Durant ce projet, j'ai pris en charge le développement de l'intégralité du frontend sous Streamlit. Concrètement, j'ai conçu les différentes pages de l'interface, intégré les graphiques interactifs et assuré la liaison entre le frontend et le backend afin de faire circuler les requêtes et l'authentification de bout en bout.

Le travail en équipe s'est révélé très enrichissant pour moi, puisque que je partais avec de réelles lacunes en développement informatique et peu d'aisance sur ce type de projet. Le niveau de chacun était assez varié et pouvoir m'appuyer sur des membres plus expérimentés dans le groupe m'a énormément aidée à débloquer mes problèmes et à monter en compétence.

Ce projet m'a permis de progresser bien plus que je ne l'aurais imaginé, avec un vrai déclic durant les trois jours d'immersion : travailler tous ensemble en continu m'a permis de comprendre la logique globale de l'application et de finaliser l'intégration. Mon conseil aux futurs 2A qui appréhendent le projet informatique est de ne pas rester bloqués seuls face à leurs difficultés, d'oser solliciter les membres plus à l'aise du groupe et de communiquer régulièrement surtout lorsque chacun travaille sur une brique différente.

#heading(level: 2, numbering: none)[Sidy Mohamed Salim Diallo]
<sidy-mohamed-salim-diallo>
#strong[Mon rôle et mes réalisations.] J'ai été chef d'équipe : coordination du projet, répartition des responsabilités et suivi de l'avancement de chacun. En gardant une vision d'ensemble, j'ai veillé à la cohérence des interfaces entre les couches (base, services, API, frontend) et touché à toutes les parties de l'application : architecture en couches, base de données et DAO, logique métier, sécurité (authentification par jeton et rôles) et lien avec le frontend. J'ai aussi porté l'outillage qui simplifie l'installation et la démonstration : une commande unique de lancement (#NormalTok("make go");), un import de données reproductible et hors ligne, et une suite de tests entièrement simulée (#emph[mocking]) exécutable sans base.

#strong[Mon vécu du travail en groupe.] Diriger une équipe de cinq aux niveaux variés a été l'aspect le plus formateur : répartir les tâches selon les forces de chacun, faire le lien entre les personnes et anticiper les blocages à l'intégration, là où les couches s'emboîtent. Les trois jours d'immersion en présentiel ont été décisifs pour résorber rapidement les points de friction entre l'API, la base et le frontend.

#strong[Enseignements et conseils aux futurs 2A.] J'ai retenu qu'organiser et suivre le travail d'une équipe compte autant que la technique, et qu'un projet ne vaut que s'il se lance et se teste facilement. Mon conseil : désigner clairement un coordinateur, définir tôt les interfaces entre les couches, versionner proprement et communiquer en continu.

#heading(level: 2, numbering: none)[Alexandre Fratter-Bardy]
<alexandre-fratter-bardy>
Au sein du projet, j'ai pris en charge le développement de la couche base de données et des DAO, tout en apportant ponctuellement mon aide sur d'autres parties du code selon les besoins. Pour la rédaction du rapport, nous avons réparti les sections en fonction des sujets sur lesquels chacun se sentait le plus à l'aise, en cohérence avec le travail réalisé par chacun.

Le travail en groupe s'est bien passé, avec une bonne entente générale. Les niveaux en informatique étant variés au sein de l'équipe, j'en ai profité pour poser régulièrement des questions aux membres les plus à l'aise sur certains points techniques afin de débloquer mes problèmes et d'apprendre davantage. Cette entraide a permis de garder un bon rythme tout au long du projet.

Ce projet m'a permis de gagner en assurance sur la conception de bases de données et sur les méthodes de développement en équipe. Mon principal conseil aux futurs 2A est de miser sur la communication surtout lorsqu'on répartit le travail par couches techniques. En effet, échanger régulièrement sur ses avancées et ses blocages est indispensable pour travailler efficacement en équipe.

#heading(level: 2, numbering: none)[Adam Ouangko Haïwè]
<adam-ouangko-haïwè>
Au sein de l'équipe, j'ai principalement travaillé dans la couche #NormalTok("service"); sur la partie backend, où j'ai développé la logique métier des analyses, avec une contribution à la couche #NormalTok("controller");. Ce rôle m'a appris à traduire un besoin fonctionnel (analyser une évolution, comparer des pays ou des indicateurs) en règles claires, indépendantes de la base de données comme de l'interface. Placé entre la DAO et l'API, j'ai surtout mesuré l'importance de définir en amont les formats de données échangés, c'est à cet endroit que les couches doivent s'emboîter sans erreur. J'ai aussi appris à développer le réflexe d'écrire un code testable, en isolant mes services grâce aux mocks, et à respecter des conventions communes (typage explicite, Ruff, revue de code avant fusion). Les journées d'immersion ont montré que la communication entre l'API et le frontend se règle plus vite à plusieurs, autour d'un même écran. \
#strong[Mon conseil aux futurs 2A] : séparer strictement la logique métier de l'accès aux données, tester tôt et documenter les interfaces entre couches.

#heading(level: 2, numbering: none)[Vicram Raveendiran]
<vicram-raveendiran>
Durant le projet, j'ai occupé le rôle de data engineer. Mon rôle était de gérer la collecte de données : extraction des données depuis l'API ILOSTAT, parsing pour les structurer, puis nettoyage des données. Mon objectif était de fournir des données exploitables aux autres membres de l'équipe.

Travailler en équipe m'a permis d'en apprendre plus sur le fonctionnement au sein d'un groupe de projet. En effet, dans les précédents projets, nous n'avions pas de rôles répartis, ce qui causait un peu de désordre. Dans ce projet, chacun travaillait sur un aspect du code et sur différentes branches. De plus, certains membres m'ont aidé à progresser en code, de par leur expérience.

Une des choses fondamentales que je retiens de ce projet est qu'il est toujours possible d'en apprendre plus sur les différents aspects de la programmation. Un conseil que j'aurais à donner à un futur 2A serait de bien organiser et répartir les rôles et les tâches au sein d'un groupe, car c'est essentiel dans un projet d'équipe et dans le monde du travail.

#heading(level: 1, numbering: none)[Annexes]
<annexes>
#heading(level: 2, numbering: none)[Annexe A --- Diagrammes de packages et de classes]
<annexe-a-diagrammes-de-packages-et-de-classes>
=== Diagramme de packages
<diagramme-de-packages>
#figure(caption: [Diagramme de packages de LaborScope.])[
  #align(center, block(width: 100%, stroke: 0.6pt + brand.lighten(55%), radius: 3pt, clip: true, inset: 0pt, fill: white)[
    #image("images/diagramme_packages.png", width: 100%)])
] <fig-packages>
=== Diagramme de classes --- domaine de l'emploi
<diagramme-de-classes-domaine-de-lemploi>
#figure(caption: [Diagramme de classes : indicateurs, pays, classifications (âge / occupation par héritage), observations et imports, avec constructeurs et associations.])[
  #align(center, block(width: 100%, stroke: 0.6pt + brand.lighten(55%), radius: 3pt, clip: true, inset: 0pt, fill: white)[
    #image("images/diag_class_emploi.png", width: 100%)])
] <fig-classes-emploi>
=== Diagramme de classes --- utilisateurs, journal d'activité et rapports
<diagramme-de-classes-utilisateurs-journal-dactivité-et-rapports>
#figure(caption: [Diagramme de classes : utilisateurs, journal d'activité et rapports, avec constructeurs et associations.])[
  #align(center, block(width: 100%, stroke: 0.6pt + brand.lighten(55%), radius: 3pt, clip: true, inset: 0pt, fill: white)[
    #image("images/diag_class_user.png", width: 100%)])
] <fig-classes-user>



