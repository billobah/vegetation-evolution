# Analyse de l'Indice de Végétation NDVI à partir des Images Satellitaires Landsat

## Description du Projet

Ce projet vise à analyser l'évolution de l'indice de végétation **NDVI** (Normalized Difference Vegetation Index) d'une aire géographique donnée à partir d'images satellites **Landsat**. L'analyse est basée sur l'extraction, le traitement et l'interprétation des bandes spectrales des images satellite fournies par l'API Machine-to-Machine (M2M) de l'USGS EarthExplorer.

L'objectif est de :
1. **Télécharger** les images Landsat via l'API **m2m-api**.
2. **Extraire** les bandes spectrales nécessaires pour le calcul du NDVI (bandes B3 et B4).
3. **Redresser** et pré-traiter les images (corrections géométriques et radiométriques).
4. **Calculer** l'indice NDVI.
5. **Réaliser une analyse spatiale et temporelle** pour observer les variations du NDVI.

---

## Structure du Projet


---

## Installation et Prérequis

### 1. Cloner le dépôt


### 2. Créer un environnement virtuel (optionnel)


### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

---

## Étape 1 : Téléchargement des images Landsat avec **m2m-api**

Ce projet utilise la bibliothèque **m2m-api** (disponible sur [GitHub](https://github.com/Fergui/m2m-api)) pour interagir avec l'API Machine-to-Machine (M2M) de l'USGS et télécharger des images Landsat.

**Avant de lancer ce script, assure-toi d'avoir un compte USGS et d'avoir demandé l'accès M2M (Machine-to-Machine) sur [ERS USGS](https://ers.cr.usgs.gov/profile/access).**  

Une fois l'accès validé, renseigne tes identifiants ou ton token dans le fichier `config.json`.

```bash
python m2m_api/download_images.py
```

Ce script :
- Se connecte à l'API USGS via `m2m-api`.
- Effectue une recherche d'images Landsat en fonction des critères définis (zone géographique, période, couverture nuageuse).
- Télécharge automatiquement les images valides.

---

## Étape 2 : Prétraitement des Images

Le script `image_utils/crop_straighten_images.py` réalise le **redressement géométrique** des images pour garantir leur alignement.

```bash
python utils/crop_straighten_images.py
```

Ce script :
- Extrait les bandes **B3 (Rouge)** et **B4 (Proche Infrarouge)**.
- Aligne les images pour corriger les erreurs de positionnement.
- Convertit les fichiers en un format exploitable.

---

## Étape 3 : Calcul du NDVI

Le script `ndvi/compute_ndvi.py` calcule le **NDVI** à partir des bandes spectrales extraites, selon la formule :

NDVI = (B4 - B3)/(B4 + B3)

```bash
python ndvi/compute_ndvi.py
```

Ce script :
- Charge les bandes B3 et B4.
- Applique la formule NDVI pixel par pixel.
- Génère des cartes NDVI sous forme d'images géoréférencées.

---

## Étape 4 : Analyse Temporelle du NDVI

Le script `ndvi/analyze_ndvi.py` permet d'analyser l'évolution du NDVI au fil du temps afin d'observer les tendances de la végétation.

```bash
python ndvi/analyze_ndvi.py
```

Ce script :
- Agrège les valeurs du NDVI sur plusieurs périodes.
- Génère des **graphes temporels** illustrant les variations du NDVI.
- Met en évidence les tendances et anomalies de la végétation.

---

## Résultats et Visualisation

Les résultats sont stockés dans le dossier `results/`, sous forme de :
- **Cartes NDVI géoréférencées** (format PNG).
- **Graphiques temporels** illustrant l'évolution du NDVI.
- **Visuels statistiques** sur les tendances observées.

---

## Références

- **m2m-api** : [https://github.com/Fergui/m2m-api](https://github.com/Fergui/m2m-api)
- **USGS EarthExplorer API** : [https://earthexplorer.usgs.gov/](https://earthexplorer.usgs.gov/)
- **Documentation Landsat** : [https://www.usgs.gov/landsat](https://www.usgs.gov/landsat)

---