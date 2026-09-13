# ensai-it-project-2a-team23



src/
├── dao/
│   ├── emploi_dao.py
│   ├── activity_dao.py
│   ├── indicateur_dao.py
│   └── user_dao.py
│
├── services/
│   ├── extraction_service.py       # F1
│   ├── parsing_service.py          # F2
│   ├── analyse_emploi_service.py   # F3
│   ├── comparaison_pays_service.py # F4
│   ├── user_service.py             # F6
│   ├── cartographie_service.py     # FO2 
│   └── rapport_pdf__service.py     # F03
│
├── controllers/
│   ├── extraction_controller.py
│   ├── parsing_controller.py
│   ├── analyse_emploi_controller.py
│   ├── comparaison_pays_controller.py
│   ├── comparaison_indicateurs_controller.py
│   ├── cartographie_controller.py
│   ├── rapport_pdf_controller.py
│   └── user_controller.py
│
├── schema/
│   ├── emploi_model.py
│   ├── indicateur_model.py
│   ├── pays_model.py
│   └── user_model.py
│
└── bussiness_object/
    ├── emploi.py
    ├── indicateur.py
    ├── pays.py
    └── user.py
