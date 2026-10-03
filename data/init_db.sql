-- -----------------------------------------------------
-- LaborScope - Création des tables
-- Les dépendances de clés étrangères imposent l'ordre de création.
-- -----------------------------------------------------

DROP TABLE IF EXISTS observation CASCADE;
DROP TABLE IF EXISTS import_donnees CASCADE;
DROP TABLE IF EXISTS journal_activite CASCADE;
DROP TABLE IF EXISTS rapport CASCADE;
DROP TABLE IF EXISTS classification CASCADE;
DROP TABLE IF EXISTS indicateur CASCADE;
DROP TABLE IF EXISTS pays CASCADE;
DROP TABLE IF EXISTS utilisateur CASCADE;

-- -----------------------------------------------------
-- Utilisateur
-- -----------------------------------------------------
CREATE TABLE utilisateur (
     id                  SERIAL PRIMARY KEY,
     nom_utilisateur     VARCHAR(50) UNIQUE NOT NULL,
     mot_de_passe_hash   VARCHAR(256) NOT NULL,
     role                VARCHAR(20) NOT NULL DEFAULT 'utilisateur'
                         CHECK (role IN ('utilisateur', 'admin')),
     actif               BOOLEAN NOT NULL DEFAULT TRUE,
     date_creation       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
     derniere_connexion  TIMESTAMP
);

-- -----------------------------------------------------
-- Pays (référentiel)
-- -----------------------------------------------------
CREATE TABLE pays (
     code_pays   VARCHAR(10) PRIMARY KEY,
     nom_pays    VARCHAR(100) NOT NULL
);

-- -----------------------------------------------------
-- Indicateur (référentiel)
-- -----------------------------------------------------
CREATE TABLE indicateur (
     code_indicateur VARCHAR(50) PRIMARY KEY,
     description     VARCHAR(255) NOT NULL,
     unite           VARCHAR(50),
     source          VARCHAR(100),
     actif           BOOLEAN NOT NULL DEFAULT TRUE
);

-- -----------------------------------------------------
-- Classification (référentiel : âge ou occupation)
-- Colonnes spécifiques selon le type :
--    age        -> age_min / age_max
--    occupation -> valeur
-- -----------------------------------------------------
CREATE TABLE classification (
     code        VARCHAR(50) PRIMARY KEY,
     libelle     VARCHAR(255) NOT NULL,
     type        VARCHAR(20) NOT NULL CHECK (type IN ('age', 'occupation')),
     age_min     INTEGER,
     age_max     INTEGER,
     valeur      VARCHAR(100)
);

-- -----------------------------------------------------
-- Import de données
-- -----------------------------------------------------
CREATE TABLE import_donnees (
     id              SERIAL PRIMARY KEY,
     indicateur_code VARCHAR(50) REFERENCES indicateur (code_indicateur),
     utilisateur_id  INTEGER REFERENCES utilisateur (id),
     date_debut      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
     date_fin        TIMESTAMP,
     statut          VARCHAR(20) NOT NULL DEFAULT 'en_cours'
                     CHECK (statut IN ('en_cours', 'succes', 'echec')),
     nombre_lignes   INTEGER NOT NULL DEFAULT 0,
     fichier_source  VARCHAR(255),
     message_erreur  TEXT
);

-- -----------------------------------------------------
-- Observation
-- Contrainte d'unicité : une seule valeur par combinaison
-- (indicateur, pays, période, sexe, classification).
-- NULLS NOT DISTINCT (PostgreSQL >= 15) traite les classifications
-- nulles comme égales pour éviter les doublons.
-- -----------------------------------------------------
CREATE TABLE observation (
     id                  BIGSERIAL PRIMARY KEY,
     code_indicateur     VARCHAR(50) NOT NULL REFERENCES indicateur (code_indicateur),
     code_pays           VARCHAR(10) NOT NULL REFERENCES pays (code_pays),
     periode             VARCHAR(20) NOT NULL,
     valeur              NUMERIC(18, 4),
     sexe                VARCHAR(10) NOT NULL DEFAULT 'total'
                         CHECK (sexe IN ('homme', 'femme', 'total')),
     code_classification VARCHAR(50) REFERENCES classification (code),
     import_id           INTEGER REFERENCES import_donnees (id),
     source              VARCHAR(100),
     date_import         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
     CONSTRAINT uq_observation UNIQUE NULLS NOT DISTINCT
         (code_indicateur, code_pays, periode, sexe, code_classification)
);

-- -----------------------------------------------------
-- Journal d'activité
-- -----------------------------------------------------
CREATE TABLE journal_activite (
     id              BIGSERIAL PRIMARY KEY,
     utilisateur_id  INTEGER REFERENCES utilisateur (id),
     action          VARCHAR(100) NOT NULL,
     cible           VARCHAR(255),
     details         TEXT,
     date_heure      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------
-- Rapport
-- -----------------------------------------------------
CREATE TABLE rapport (
     id              SERIAL PRIMARY KEY,
     utilisateur_id  INTEGER REFERENCES utilisateur (id),
     titre           VARCHAR(255) NOT NULL,
     description     TEXT,
     date_creation   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
     fichier_path    VARCHAR(255),
     statut          VARCHAR(20) NOT NULL DEFAULT 'en_attente'
                     CHECK (statut IN ('en_attente', 'pret', 'echec'))
);

-- -----------------------------------------------------
-- Index utiles aux analyses (lecture de séries / par période)
-- -----------------------------------------------------
CREATE INDEX idx_observation_serie   ON observation (code_indicateur, code_pays, periode);
CREATE INDEX idx_observation_periode ON observation (code_indicateur, periode);