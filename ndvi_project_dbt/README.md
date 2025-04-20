# Projet NDVI avec DBT

Ce projet DBT transforme les données brutes NDVI calculées à partir d’images satellites Landsat.

## Objectifs (non encore exhaustif)
- Classifier les NDVI en classes de végétation
- Calculer la distribution des pixels par classe et par image
- Préparer les données pour une visualisation temporelle (via Power BI, Streamlit, etc.)

## Arborescence
- `staging` : normalisation des NDVI bruts
- `marts` : classification + distribution des NDVI
- `macros`, `tests`, `analyses` : extensibles

## Commandes utiles pour lancer le projet
```bash
dbt debug
dbt deps
dbt seed
dbt run
dbt test