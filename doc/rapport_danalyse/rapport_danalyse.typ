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
  toc_title: [Table des matières],
  toc_depth: 3,
  doc,
)

#let accent = rgb("#1f3554")
#let mutedgray = rgb("#5a5a5a")

#set text(lang: "fr", font: "Libertinus Serif", size: 11pt)
#set par(justify: true, leading: 0.68em, first-line-indent: 0pt)
#set list(marker: text(fill: accent, size: 0.85em)[●])
#set enum(numbering: "1.")
#set heading(numbering: "1.1")

#show heading.where(level: 1): it => {
  block(above: 1.6em, below: 1.1em)[
    #text(size: 20pt, weight: "bold", fill: accent)[
      #if it.numbering != none [#counter(heading).display() #h(0.4em)]
      #it.body
    ]
    #v(0.2em)
    #line(length: 100%, stroke: 0.5pt + accent)
  ]
}
#show heading.where(level: 2): it => {
  block(above: 1.4em, below: 0.7em)[
    #text(size: 13pt, weight: "bold")[
      #counter(heading).display() #h(0.4em) #it.body
    ]
  ]
}
#show heading.where(level: 3): it => {
  block(above: 1.1em, below: 0.5em)[
    #text(size: 11.5pt, weight: "bold", style: "italic")[#it.body]
  ]
}

// ------------------------------------------------------------
// Bloc image standardisé : centré, encadré sobrement, légende
// stylée en italique grise sous un fin trait d'accent.
// ------------------------------------------------------------
#let fig_counter = counter("figures")

#let figure_block(path, caption, w: 8cm, h: auto) = {
  fig_counter.step()
  align(center)[
    #box(
      stroke: 0.6pt + mutedgray.lighten(55%),
      radius: 3pt,
      inset: 12pt,
      fill: rgb("#fafafa"),
    )[
      #image(path, width: w)
    ]
    #v(0.6em)
    #line(length: 2.2cm, stroke: 0.6pt + accent)
    #v(0.35em)
    #context text(size: 9.5pt, fill: mutedgray, style: "italic")[
      #text(fill: accent, weight: "bold", style: "normal")[Fig. #fig_counter.display()] — #caption
    ]
    #v(0.4em)
  ]
}

// ------------------------------------------------------------
// Page de titre
// ------------------------------------------------------------
#set page(header: none, footer: none, numbering: none)

#align(center)[
  #v(0.3cm)
  #image("images/ensai_logo_1.png", width: 8cm)
  #v(1.4cm)
  #text(size: 12pt, tracking: 1.8pt)[Projet informatique --- 2#super[e] année]
  #v(2.4cm)
  #line(length: 100%, stroke: 0.7pt + accent)
  #v(0.10cm)
  #text(size: 23pt, weight: "bold")[LaborScope]
  #v(0.10cm)
  #text(size: 13pt, style: "italic", fill: mutedgray)[Dossier d'analyse]
  #v(0.10cm)
  #line(length: 100%, stroke: 0.7pt + accent)
]

#v(2.6cm)

#grid(
  columns: (1fr, 1fr),
  column-gutter: 1cm,
  align(left)[
    #text(style: "italic", fill: mutedgray)[Étudiant·e·s]
    #v(0.5em)
    Jade #smallcaps[Colin] \
    Sidy Mohamed Salim #smallcaps[Diallo] \
    Alexandre #smallcaps[Fratter-Bardy] \
    Adam Ouangko #smallcaps[Haïwè] \
    Vicram #smallcaps[Raveendiran]
  ],
  align(right)[
    #text(style: "italic", fill: mutedgray)[Responsable]
    #v(0.35em)
    Ludovic #smallcaps[Deneuville]

    #v(1.2cm)

    #text(style: "italic", fill: mutedgray)[Encadrant]
    #v(0.35em)
    Anas #smallcaps[Knefati]
  ]
)

#v(1fr)

#align(center)[
  #text(size: 10pt)[
    École nationale de la statistique et de l'analyse de l'information \
    2026 -- 2027
  ]
]

#pagebreak()

// ------------------------------------------------------------
// Réglages communs — table des matières et corps du rapport
// ------------------------------------------------------------
#set page(
  header: context {
    if counter(page).get().first() >= 1 [
      #set text(size: 8.5pt, fill: mutedgray, style: "italic")
      #grid(columns: (1fr, 1fr))[
        Projet LaborScope
      ][
        #align(right)[ENSAI --- 2026 -- 2027]
      ]
      #v(-0.55em)
      #line(length: 100%, stroke: 0.4pt + mutedgray)
    ]
  },
  footer: context [
    #align(center)[#text(size: 9pt, fill: mutedgray)[#counter(page).display()]]
  ],
  numbering: "1",
)
#counter(page).update(1)

#heading(numbering: none, outlined: false)[Table des matières]
#v(-0.6em)
#line(length: 100%, stroke: 0.5pt + accent)
#v(1em)
#outline(title: none, depth: 2, indent: 1.4em)

#pagebreak()
= Introduction
<introduction>
Le marché du travail occupe une place centrale dans nos sociétés. Que ce soit pour suivre l'évolution de l'emploi, comprendre les différences entre les pays ou encore analyser les inégalités entre les catégories de population, les statistiques liées au travail constituent une source d'information essentielle. En effet, l'emploi peut être influencé par de nombreux facteurs tels que l'âge, le sexe, la profession ou encore la situation économique d'un pays. L'analyse de ces données permet ainsi de mieux comprendre les évolutions du marché du travail et les différentes tendances qui peuvent apparaître au fil du temps. Cependant, la quantité de données disponibles peut rendre leur utilisation assez complexe. Les statistiques sont régulièrement mises à jour et peuvent être classées selon de nombreux critères. Il peut alors être difficile de retrouver une information précise, de comparer plusieurs pays ou encore de suivre l'évolution d'un indicateur sur une période donnée. Disposer d'un outil capable de regrouper ces données, de les traiter et de les présenter de manière simple permettrait donc de faciliter leur analyse. C'est dans cette idée que s'inscrit notre projet LaborScope. Son objectif est de développer une API permettant d'exploiter et d'analyser des statistiques mondiales sur le marché du travail, en utilisant notamment les données ouvertes de l'Organisation Internationale du Travail disponibles via l'API ILOSTAT. Ces données permettent par exemple d'étudier l'emploi en fonction du sexe et de la profession, mais aussi la population en âge de travailler selon le sexe et l'âge, pour de nombreux pays et régions du monde.

Le projet intégrera également une gestion des utilisateurs avec différents niveaux d'accès. Des fonctionnalités complémentaires pourront être ajoutées, comme une cartographie interactive ou la génération automatique de rapports. L'objectif de LaborScope est de proposer une solution simple et évolutive pour faciliter l'analyse des données du marché du travail. Dans ce rapport, nous présenterons le cahier des charges, la conception et l'architecture de l'application, les choix techniques ainsi que la réalisation des principales fonctionnalités.

= Cahier des charges
<cahier-des-charges>
Notre application doit comporter plusieurs fonctionnalités essentielles. L'utilisateur devra ainsi pouvoir accéder :

- à la récupération et à la mise à jour des données provenant de l'API ILOSTAT \;
- à la consultation des données concernant différents pays, sexes, tranches d'âge et professions \;
- à l'analyse de l'évolution d'un indicateur sur une période donnée \;
- à la comparaison d'un indicateur entre plusieurs pays \;
- à la comparaison de plusieurs indicateurs sur une même période \;
- à des graphiques permettant de visualiser clairement les résultats \;
- à un système d'authentification avec différents niveaux d'accès (utilisateurs et administrateurs)

Les administrateurs disposent également de fonctionnalités supplémentaires leur permettant de gérer les données stockées et de suivre les activités de l'application. Par ailleurs, plusieurs fonctionnalités optionnelles sont envisagées afin d'enrichir l'expérience utilisateur, telles que :

- l'affichage des indicateurs sur une carte interactive du monde \;
- la génération automatique de rapports d'analyse au format PDF \;

Ces fonctionnalités supplémentaires pourront être développées en fonction de l'avancement du projet et seront détaillées davantage dans le dossier final si elles sont retenues.

= Questionnements et choix
<questionnements-et-choix>
Lors de la phase de conception de LaborScope, plusieurs réflexions ont été menées afin de définir les orientations techniques et fonctionnelles du projet. Le premier choix décisif a concerné l'architecture globale de l'outil. Bien que le cahier des charges laisse la possibilité de se limiter au développement de l'API, nous avons pris le parti de développer la solution la plus complète : une API couplée à une interface graphique (front-end). Cette approche nous paraît indispensable pour répondre à l'objectif principal du projet, c'est-à-dire rendre des volumes importants de statistiques accessibles, exploitables et visuellement clair pour l'utilisateur final. Une autre réflexion majeure a porté sur le système d'authentification et la répartition des droits d'accès. Plutôt que d'imposer la création d'un compte de manière stricte dès l'ouverture de l'application, nous avons opté pour une approche progressive. L'objectif est de démontrer l'utilité de notre outil dès la première visite. Ainsi, nous avons décidé de laisser la fonctionnalité d'analyse temporelle de l'emploi (F3) en accès libre. Un visiteur non connecté pourra donc interroger la base de données, générer un graphique et observer l'évolution d'un indicateur sans restriction. En revanche, l'accès aux fonctionnalités d'analyse plus avancées (comparaison géographique, croisement multi-indicateurs, cartographie ou génération de rapports) nécessitera obligatoirement une authentification. Ce choix stratégique permet d'offrir un aperçu concret des capacités de l'application pour susciter l'intérêt de l'utilisateur, tout en l'incitant à s'inscrire pour bénéficier d'une expérience complète. Nous avons fait le choix d'orienter l'application vers une logique marketing et commerciale afin d'attirer et de fidéliser de potentiels clients comme dans une vraie application . Cette dynamique permet d'enrichir notre base de données clients et s'intègre parfaitement avec le système de gestion des rôles (Utilisateurs et Administrateurs) mis en place pour administrer l'application.

= Description des fonctionnalités
<description-des-fonctionnalités>
Le projet comporte différentes fonctionnalités qui se répartissent entre fonctionnalités obligatoires et fonctionnelles. Il y a 6 fonctionnalités obligatoires ainsi que 2 fonctionnalités. La première fonctionnalité de cette application consiste en la récupération et le stockage automatisés des données. Ainsi, l'application interroge automatiquement et de façon périodique l'API ILOSTAT et récupère les indicateurs souhaités sur plusieurs pays. Ensuite vient le traitement des données, les fichiers bruts sont triés pour ne conserver que les champs jugés essentiels au bon fonctionnement de l'application. Ces données nettoyées sont ensuite sauvegardées dans la base de données locale et deviennent enfin prêtes à être analysées. Une autre fonctionnalité doit permettre l'analyse temporelle des données extraites et stockées. L'utilisateur pourra sélectionner un indicateur, définir une fenêtre de temps et afficher les résultats sous forme graphique. Concrètement, après la sélection des paramètres, l'API calcule cette évolution temporelle et l'interface affiche permet d'observer les dynamiques du marché du travail. Outre la comparaison temporelle d'un indicateur, cette fonctionnalité propose à l'utilisateur, pour la période la plus récente possible présente dans la base de données, de comparer un indicateur entre plusieurs pays. L'utilisateur peut choisir une liste de pays ainsi qu' un indicateur et l'application met en évidence les pays présentant les valeurs les plus hautes et les plus basses concernant cet indicateur. La fonctionnalité de comparaison multi-indicateurs doit permettre à l'utilisateur de croiser plusieurs jeux de données. L'utilisateur pourra superposer plusieurs indicateurs sur un même graphique ainsi qu'une échelle de temps. Cela permet de dégager visuellement des liens entre les indicateurs sur une période donnée et ainsi de comprendre quels mécanismes régissent le monde du travail. La dernière fonctionnalité obligatoire consiste en la gestion des utilisateurs et de la sécurité. Ainsi, l'accès à l'application sera sécurisé par une authentification vérifiant les mots de passe et le système devra gérer deux niveaux de droits d'accès. Les utilisateurs standard consultent les analyses et les visualisations tandis que les administrateurs possèdent en plus de la consultation des droits de gestion sur les données. De plus, chaque modification sur les bases de données entraîne une actualisation du journal de suivi des activités. La première fonctionnalité optionnelle est une cartographie interactive où l'utilisateur choisit un indicateur et les données sont ensuite projetées sur une carte du monde. Chaque pays est colorié selon la valeur de l'indicateur choisi. Cela permet donc de visualiser des tendances mondiales sur un indicateur précis. L'application intègre également une fonctionnalité permettant de générer un rapport d'analyse au format PDF. L'utilisateur sélectionne des indicateurs, une période de temps ainsi que des pays et l'outil en fera un résumé statistique contenant des graphiques et une conclusion synthétique générée automatiquement à partir des données observées.

= Organisation du groupe
<organisation-du-groupe>
#NormalTok("ICI mettre diagramme de Gantt"); (SALIM)

= Organisation du travail
<organisation-du-travail>
Concernant l'organisation du travail, notre équipe s'appuie sur plusieurs outils collaboratifs afin d'assurer une communication fluide et une répartition efficace des tâches. Pour nos échanges quotidiens, nous disposons d'un groupe de discussion sur WhatsApp, ce qui nous permet de débattre de nos idées et de faire des points réguliers sur l'avancement du projet. En parallèle, nous utilisons Google Docs pour la rédaction et le partage de nos documents communs garantissant ainsi à chaque membre un accès simultané pour la lecture et la modification des fichiers. La gestion de projet et le suivi des tâches sont quant à eux centralisés sur la plateforme Notion. Cet espace de travail nous permet de répertorier l'intégralité des actions à mener. Chaque tâche y est qualifiée selon plusieurs critères : son statut (à faire, en cours ou terminé), la phase du projet à laquelle elle se rattache, son niveau d'importance, ainsi que le membre du groupe qui en est responsable. Cette méthode structure notre organisation, offre une vision claire de la progression globale et permet à chacun de savoir précisément ce qu'il doit accomplir. Enfin, concernant la partie développement, nous codons notre application sur VSCode et nous nous appuyons sur GitHub pour centraliser notre travail. Ce répertoire commun est très utile : il sécurise notre collaboration, nous permet de coder en parallèle, de conserver tout l'historique de nos modifications et de résoudre facilement les éventuels conflits de versions.

= Modèle de conception
<modèle-de-conception>
Cette phase de conception est très importante dans la mesure où elle pose les jalons du projet. En effet, cela nous permet de savoir ce que nous allons faire ainsi que les méthodes que nous allons utiliser pour y parvenir. Cette partie utilise des outils de modélisation UML pour définir tous les aspects de l'application. Par ailleurs, cette phase préparatoire de modélisation permet une meilleure répartition des tâches entre les membres du groupe concernant les travaux à mener. Ainsi, chacun sait où en est rendu le projet et ce qu'il reste à faire pour le compléter. Toutefois, cette phase de conception peut être amenée à être modifiée au cours du projet car de nouveaux éléments peuvent toujours être considérés. Il est néanmoins de la plus haute importance de présenter dès le début du projet un cadre clair que nous nous efforcerons de suivre.

== Diagramme de cas d'utilisation
<diagramme-de-cas-dutilisation>
Ce diagramme de cas d'utilisation permet d'illustrer les différentes actions que les utilisateurs de l'application peuvent réaliser. Ainsi, le but de ce diagramme est de visualiser toutes les actions possibles et de les attribuer aux bons acteurs.

Il existe dans ce diagramme deux acteurs différents.

Le profil “Utilisateur” est le rôle standard. Il est strictement limité à l'authentification ainsi qu'à la consultation des analyses et des visualisations telles que l'analyse temporelle, la comparaison géographique ou encore la comparaison multi-indicateurs. Il bénéficie également d'outils tels que la cartographie et la génération de rapports. Les limites du profil “Utilisateur” s'opposent donc aux compétences du profil “Administrateur” qui a un rôle dédié aux tâches de gestion de l'application. Il est le seul à pouvoir modifier ou supprimer certaines données et à gérer l'accès des profils “Utilisateur”. De plus, la flèche d'héritage reliant l'Administrateur à l'Utilisateur indique que l'Administrateur hérite automatiquement des toutes les fonctionnalités dont l'Utilisateur a accès.

#figure_block("images/diagramme_cas_utilisation.drawio.png", "Diagramme de cas d'utilisation", w: 11cm, h: auto)
== Diagramme d'activité
<diagramme-dactivité>
Le diagramme présenté permet de caractériser les choix offerts à l'utilisateur lorsqu'il se ouvre l'application. Dans un premier temps, il va soit se connecter, soit créer un compte s'il n'en a pas.

S'il est connecté en tant qu'utilisateur, il aura la possibilité d'accéder aux trois fonctionnalités principales :

- Calculer l'évolution d'un indicateur
- Comparer un indicateur entre pays
- Comparer simultanément l'évolution de plusieurs indicateurs

Ensuite l'utilisateur aura la possibilité en fonction des fonctionnalités choisies, de rédiger un rapport analytique ou de réaliser une carte choroplèthe.

S'il est connecté en tant qu'administrateur, il aura accès à toutes les fonctionnalités de l'utilisateur. Il pourra de plus :

- Suivre l'activité des utilisateurs
- Supprimer ou promouvoir un compte en admin
- Gérer les données

A la fin, l'utilisateur pourra se déconnecter.

#figure_block("images/Diagramme_dactivite.drawio.png", "Diagramme d'activité", w: 12cm, h: auto)
== Diagramme de classes
<diagramme-de-classes>
Cette partie présente le diagramme de classes. Notre modélisation comporte cinq classes, voici une liste de chaque classe avec une courte description pour chacune :

- Utilisateur : cette classe permet de gérer les connexions. Elle stocke les informations nécessaires à l'authentification et à la sécurité (identifiant, nom d'utilisateur et son mot de passe) ainsi que le rôle de la personne qui s'identifie \;
- Journal\_activite : cette classe répond à la fonctionnalité qui exige le suivi des activités de l'Administrateur s'il modifie ou supprime des données. Il s'agit donc d'un historique où chaque action réalisée est associée à l'Administrateur correspondant \;
- Pays : Cette classe sert à stocker les données géographiques. Elle contient le code du pays ainsi que son nom complet \;
- Indicateur : Cette classe sert à savoir de quel indicateur issu de l'API ILOSTAT on parle. Elle comprend le code de l'indicateur ainsi que sa description.
- Donnee\_emploi : Cette classe stocke la valeur chiffrée d'une statistique selon les paramètres choisis (période, sexe, tranche d'âge, pays).

== Diagramme de séquences
<diagramme-de-séquences>
Un diagramme de séquence permet de montrer comment les objets et les acteurs du projet interagissent entre eux selon un ordre chronologique dans le cadre d'une fonctionnalité du diagramme de cas d'utilisation.

#figure_block("images/diagramme_sequence_fonctionnnalité.drawio.png", "Diagramme de séquence - fonctionnalité", w: 12cm, h: auto)
== Diagramme de séquences : authentification
<diagramme-de-séquences-authentification>
On retrouve dans cette partie le diagramme de séquence concernant la fonctionnalité de l'authentification. Ce diagramme illustre l'ordre chronologique des interactions entre la personne qui tente de se connecter et les trois couches du système que sont l'interface, l'API ainsi que la base de données. L'objectif de ce diagramme est de visualiser comment l'application sépare, en fonction du profil renseigné, les droits de chaque profil (Utilisateur ou Administrateur). Le processus d'authentification est initié par une personne qui saisit son nom et son mot de passe directement sur l'interface. Afin de maintenir la sécurité de l'architecture, l'Interface ne communique jamais directement avec les données, elle formule une demande d'authentification qu'elle transmet au Serveur. C'est l'API qui porte le rôle de la vérification. En effet, le Serveur interroge la Base de données locale pour vérifier si les informations transmises correspondent à un compte existant. Si le compte existe, la Base de données retourne à l'API l'identité de la personne ainsi que son rôle exact, à savoir s'il est simple Utilisateur ou bien Administrateur. En fonction de la réponse de la Base de données, l'application fait face à trois scénarios distincts selon le niveau d'authentification. En effet, selon que le profil renseigné soit utilisateur ou Administrateur, le cahier des charges nous indique que l'utilisateur ne doit pas bénéficier de tous les accès. Voici la liste des trois scénarios :

- Si le rôle détecté est “Utilisateur”, l'API confirme la réussite de l'authentification à l'Interface et accorde ensuite un accès restreint à cet Utilisateur (consultation des analyses et des visualisations)
- Si le rôle détecté est “Administrateur”, l'API confirme la réussite de l'authentification à l'Interface et accorde ensuite tous les accès de l'application à ce profil
- Si la vérification échoue, l'API notifie le refus de connexion à l'Interface et bloque l'accès à l'application en affichant un message d'erreur.

#figure_block("images/diagramme_sequence_authentification.drawio.png", "Diagramme de séquence - authentification", w: 12cm, h: auto)
== Diagramme de séquences : données analytiques
<diagramme-de-séquences-données-analytiques>
Cette partie présente le diagramme de séquence qui regroupe les fonctionnalités d'analyse de l'application telles que l'analyse temporelle, la comparaison géographique d'un indicateur ou encore la comparaison multi-indicateurs. Même si les calculs statistiques cachés derrières ces fonctionnalités diffèrent, le cheminement informatique reste similaire entre ces fonctionnalités.

Ainsi, pour ces fonctionnalités, le processus est déclenché par l'utilisateur qui depuis l'Interface sélectionne les paramètres d'analyse : indicateur, pays, période de temps. Une fois la demande d'analyse validée, l'Interface formule une requête qu'elle envoie à l'API. À la réception de cette requête, l'API prend le relais concernant la gestion des données et interroge la Base de données locale avec les critères de filtrage renseignés par l'utilisateur. Ensuite la Base de données répond à cette requête en retournant les données correspondantes. La dernière étape consiste en la préparation et l'affichage des résultats. Pour cela, l'API nettoie les données brutes et calcule les statistiques demandées par l'utilisateur avant de renvoyer ces données formatées à l'Interface. À la réception de ces données finales, l'Interface les utilise pour construire le graphique approprié et l'affiche à l'utilisateur.

== Diagramme de packages
<diagramme-de-packages>
Le diagramme de packages nous permet de voir comment les différentes couches du code interagissent entre elles. La première couche est le frontend, et permet à l'utilisateur d'interagir avec l'application. Il pourra se connecter et ensuite naviguer dans l'application. La deuxième couche est l'API, qui va transmettre les demandes, commandes de l'utilisateur vers le programme. La couche de services va réceptionner ces demandes pour ensuite réaliser des calculs. Cette couche comprend tous les objets, classes relatives aux utilisateurs et calculs à effectuer. Elle interagit avec la dernière couche qui est la couche de données. Les données sont récupérées et parsées, pour être envoyées à la DAO. Les données seront alors traitées pour ensuite être stockées localement dans une base de données PostgreSQL. Ces données seront donc exploitées afin d'effectuer les calculs dans la couche de services. Enfin, on pourra réaliser des visuels graphiques dans la couche de services, qui apparaîtront directement dans le frontend.

#figure_block("images/Diagramme_de_packages.drawio.png", "Diagramme de packages", w: 12cm, h: auto)
= Liste des principaux composants
<liste-des-principaux-composants>
== Les DAO
<les-dao>
\(#NormalTok("se servir du cahier des charges pour écrire ce paragraphe");) Les DAO servent à récupérer les données de la base de données.

== La couche de services
<la-couche-de-services>
La couche de services contiendra les classes et objets métiers. C'est cette couche qui récupérera les requêtes via l'API et qui les traitera à l'aide des fonctions implémentées. Les principales fonctionnalités seront l'affichage de l'évolution d'indicateurs, la comparaison entre pays et la comparaison de plusieurs indicateurs. Elle interagit avec la DAO pour la récupération de données utiles aux calculs. Le temps de développement est estimé à 35H.

== L'API
<lapi>
L'API (Application Programming Interface) va nous permettre de lier le frontend et les couches métier. Elle reçoit les requêtes HTTP, les valide et communique avec les classes métier nécessaires. Elle ne sert pas à réaliser les calculs mais permet de gérer les appels du frontend, notamment sur l'authentification et l'exécution de fonctionnalités. Cette articulation sera faite à l'aide de contrôleurs. Une étape de validation est nécessaire sur l'authentification afin de valider ou refuser l'accès à un utilisateur. La couche API sera développée avec FastAPI et le temps de développement est estimé à 20H.

== Le frontend
<le-frontend>
Le dernier composant que nous allons développer est le frontend. Il correspond à la couche d'interaction entre l'utilisateur et le programme. C'est là-dessus que l'utilisateur pourra faire des demandes et obtenir des résultats (visualisation graphique, calculs de statistiques…). Le package streamlit sera utilisé afin de développer cette couche. Il affichera donc l'écran de connexion et les différentes fonctionnalités que l'utilisateur pourra choisir. Cette couche interagit avec le backend qui va effectuer les calculs. Le frontend dépend donc du backend pour obtenir les données, les commandes et les résultats. Le backend quant à lui aura besoin du frontend pour enregistrer les demandes de l'utilisateur et y répondre. Le temps estimé pour développer ce composant est de 15H.
