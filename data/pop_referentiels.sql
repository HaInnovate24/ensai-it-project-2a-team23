-- -----------------------------------------------------
-- LaborScope - Peuplement des référentiels
-- Pays, classifications (âge + occupation) et les deux indicateurs.
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Pays (code ISO 3166-1 alpha-3 et nom)
-- -----------------------------------------------------
INSERT INTO pays (code_pays, nom_pays) VALUES
     ('FRA', 'France'),
     ('DEU', 'Allemagne'),
     ('GBR', 'Royaume-Uni'),
     ('ESP', 'Espagne'),
     ('ITA', 'Italie'),
     ('USA', 'États-Unis'),
     ('CAN', 'Canada'),
     ('BRA', 'Brésil'),
     ('MEX', 'Mexique'),
     ('ARG', 'Argentine'),
     ('CHN', 'Chine'),
     ('IND', 'Inde'),
     ('JPN', 'Japon'),
     ('KOR', 'Corée du Sud'),
     ('IDN', 'Indonésie'),
     ('ZAF', 'Afrique du Sud'),
     ('NGA', 'Nigéria'),
     ('EGY', 'Égypte'),
     ('MAR', 'Maroc'),
     ('SEN', 'Sénégal'),
     ('AUS', 'Australie'),
     ('NZL', 'Nouvelle-Zélande');

-- -----------------------------------------------------
-- Classifications par âge (bandes agrégées ILOSTAT)
-- age_min / age_max renseignés ; valeur laissée nulle.
-- -----------------------------------------------------
INSERT INTO classification (code, libelle, type, age_min, age_max, valeur) VALUES
     ('AGE_AGGREGATE_TOTAL', 'Tous âges (15 ans et plus)', 'age', 15,  NULL, NULL),
     ('AGE_AGGREGATE_Y15-24', '15 à 24 ans',                'age', 15,  24,   NULL),
     ('AGE_AGGREGATE_Y25-plus', '25 ans et plus',           'age', 25,  NULL, NULL);

-- -----------------------------------------------------
-- Classifications par occupation (ISCO-08, 1 chiffre)
-- valeur = code du grand groupe ISCO-08 ; age_min / age_max nuls.
-- -----------------------------------------------------
INSERT INTO classification (code, libelle, type, age_min, age_max, valeur) VALUES
     ('OCU_ISCO08_TOTAL', 'Toutes professions',                                  'occupation', NULL, NULL, NULL),
     ('OCU_ISCO08_1',     'Directeurs, cadres de direction et gérants',          'occupation', NULL, NULL, '1'),
     ('OCU_ISCO08_2',     'Professions intellectuelles et scientifiques',        'occupation', NULL, NULL, '2'),
     ('OCU_ISCO08_3',     'Professions intermédiaires',                          'occupation', NULL, NULL, '3'),
     ('OCU_ISCO08_4',     'Employés de type administratif',                      'occupation', NULL, NULL, '4'),
     ('OCU_ISCO08_5',     'Personnel des services et vendeurs',                  'occupation', NULL, NULL, '5'),
     ('OCU_ISCO08_6',     'Agriculteurs et ouvriers qualifiés',                  'occupation', NULL, NULL, '6'),
     ('OCU_ISCO08_7',     'Métiers qualifiés de l''industrie et de l''artisanat','occupation', NULL, NULL, '7'),
     ('OCU_ISCO08_8',     'Conducteurs d''installations et de machines',         'occupation', NULL, NULL, '8'),
     ('OCU_ISCO08_9',     'Professions élémentaires',                            'occupation', NULL, NULL, '9'),
     ('OCU_ISCO08_0',     'Professions militaires',                              'occupation', NULL, NULL, '0'),
     ('OCU_ISCO08_X',     'Non classé ailleurs',                                 'occupation', NULL, NULL, 'X');

-- -----------------------------------------------------
-- Indicateurs
-- -----------------------------------------------------
INSERT INTO indicateur (code_indicateur, description, unite, source, actif) VALUES
     ('EMP_TEMP_SEX_OCU_NB',  'Emploi par sexe et profession',                    'Milliers', 'ILOSTAT', TRUE),
     ('POP_XWAP_SEX_AGE_NB',  'Population en âge de travailler par sexe et âge',  'Milliers', 'ILOSTAT', TRUE);