# ensai-it-project-2a-team23



src/
├── dao/                           
│   ├── emploi_dao.py
│   ├── activity_dao.py
│   ├── indicateur_dao.py
│   └── user_dao.py
│
├── services/                       # Logique métier / cas d'utilisation
│   ├── extraction_service.py       # F1
│   ├── parsing_service.py          # F2
│   ├── analyse_emploi_service.py   # F3
│   ├── comparaison_pays_service.py # F4
│   ├── user_service.py             # F6
│   ├── cartographie_service.py     # FO2 
│   └── rapport_pdf__service.py     # F03
│
├── controllers/                    # Entrée/sortie de l'application
│   ├── extraction_controller.py
│   ├── parsing_controller.py
│   ├── analyse_emploi_controller.py
│   ├── comparaison_pays_controller.py
│   ├── comparaison_indicateurs_controller.py
│   ├── cartographie_controller.py
│   ├── rapport_pdf_controller.py
│   └── user_controller.py
│
├── schema/                         # Données entrantes/sortantes de l'API
│   ├── emploi_model.py
│   ├── indicateur_model.py
│   ├── pays_model.py
│   └── user_model.py
│
└── bussiness_object/               # Objets métier
    ├── emploi.py
    ├── indicateur.py
    ├── pays.py
    └── user.py


# Modèle de données ou schema de l'application ?

# Je pense qu'on peut définir peut être un modèle de données, qui inclurait les entités principales telles que l'emploi, les indicateurs, les pays et les utilisateurs. Chaque entité aurait ses propres attributs et relations avec d'autres entités. Par exemple, un emploi pourrait avoir des attributs tels que le titre, la description, le salaire, etc., et être lié à un pays spécifique. Les indicateurs pourraient être liés à des emplois ou à des pays pour fournir des informations supplémentaires sur le marché du travail. Les utilisateurs pourraient avoir des rôles et des permissions pour accéder à différentes parties de l'application (proposition auto).

# Point : Je constate qu'il manque "comparaison_indicateurs_service.py" dans la couche service, mais on a "comparaison_indicateurs_controller.py".

# Suis pas trop fan de extraction_controller et de parsing_controller du fait qu'un utilisateur de l'API ne devrait probablement pas appeler POST /parse. Je pense que l'API devrait plutôt exposer des actions métier, comme "analyser un emploi" ou "comparer des pays", plutôt que des actions techniques comme "parser un fichier".

# Voici ce que je propose à partir de la structure de fichiers fournie (pour le modèle, ça peut être optionnel car ça rend le projet un peu plus lourd). Vous constaterez que j'ai ajouté database aussi :

ensai-it-project-2a-team23/
│
├── src/
│   │
│   ├── controllers/
│   │   ├── emploi_controller.py
│   │   ├── indicateur_controller.py
│   │   ├── comparaison_controller.py
│   │   ├── cartographie_controller.py
│   │   ├── rapport_controller.py
│   │   └── user_controller.py
│   │
│   ├── services/
│   │   ├── ingestion_service.py
│   │   ├── emploi_service.py
│   │   ├── comparaison_service.py
│   │   ├── cartographie_service.py
│   │   ├── rapport_service.py
│   │   └── user_service.py
│   │
│   ├── dao/
│   │   ├── emploi_dao.py
│   │   ├── indicateur_dao.py
│   │   ├── pays_dao.py
│   │   ├── user_dao.py
│   │   └── activity_dao.py
│   │
│   ├── models/
│   │   ├── emploi_model.py
│   │   ├── indicateur_model.py
│   │   ├── pays_model.py
│   │   ├── user_model.py
│   │   └── activity_model.py
│   │
│   ├── schemas/
│   │   ├── emploi_schema.py
│   │   ├── indicateur_schema.py
│   │   ├── comparaison_schema.py
│   │   └── user_schema.py
│   │
│   ├── business_objects/
│   │   ├── emploi.py
│   │   ├── indicateur.py
│   │   ├── pays.py
│   │   └── user.py
│   │
│   ├── database/
│   │   └── database.py
│   │
│   ├── config/
│   │   └── settings.py
│   │
│   └── main.py
│
├── tests/
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
