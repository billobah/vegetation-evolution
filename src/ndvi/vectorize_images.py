import duckdb
import numpy as np
import json
import pandas as pd
import rasterio
from pathlib import Path
from typing import Dict
from collections import Counter


def classify_land_cover(ndvi_vector: np.ndarray) -> list[str]:
    return np.select(
        [ndvi_vector > 0.6, ndvi_vector > 0.3],
        ['forest', 'grassland'],
        default='bare_soil'
    ).tolist()


def extract_bbox(image_path: str):
    with rasterio.open(image_path) as src:
        bounds = src.bounds
        return bounds.left, bounds.bottom, bounds.right, bounds.top


def summarize_land_cover(vectorized_data: Dict[str, Dict], output_csv: Path):
    summary = []
    for rec in vectorized_data.values():
        count = Counter(rec["land_cover_vector"])
        total = len(rec["land_cover_vector"])
        summary.append({
            "image_id": rec["image_id"],
            "image_name": rec["image_name"],
            "forest_pct": count["forest"] / total * 100,
            "grassland_pct": count["grassland"] / total * 100,
            "bare_soil_pct": count["bare_soil"] / total * 100,
            "bbox_xmin": rec["bbox"]["xmin"],
            "bbox_ymin": rec["bbox"]["ymin"],
            "bbox_xmax": rec["bbox"]["xmax"],
            "bbox_ymax": rec["bbox"]["ymax"]
        })
    df_summary = pd.DataFrame(summary)
    df_summary.to_csv(output_csv, index=False)
    print(f"Export CSV résumé → {output_csv}")


def main(
    cropped_path: str,
    ndvi_series: Dict[str, np.ndarray],
    db_path: str = "../bdd/image_vectors.duckdb",
    table_name: str = "ndvi_vectors_wide",
    export_dir: str = "../bdd"
) -> Dict[str, Dict]:

    print("Démarrage vectorisation NDVI...")

    export_dir = Path(export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)

    try:
        conn = duckdb.connect(db_path)
        print(f"Connexion à DuckDB → {db_path}")
    except duckdb.IOException as e:
        raise RuntimeError(
            f"DuckDB inaccessible : {db_path}\nDétail : {e}"
        )

    # Créer la table si elle n’existe pas
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            image_id TEXT,
            image_name TEXT,
            bbox_xmin DOUBLE,
            bbox_ymin DOUBLE,
            bbox_xmax DOUBLE,
            bbox_ymax DOUBLE,
            num_pixels INTEGER,
            ndvi_vector DOUBLE[],
            land_cover_vector TEXT[]
        )
    """)

    # Récupère les images déjà stockées
    existing = set(row[0] for row in conn.execute(f"SELECT image_name FROM {table_name}").fetchall())

    print(f"{len(existing)} image(s) déjà présentes en base.")

    vectorized_data = {}
    records_to_insert = []

    for image_name, ndvi_array in ndvi_series.items():
        if image_name in existing:
            print(f"Image déjà vectorisée : {image_name}")
            continue

        image_path = Path(cropped_path) / image_name
        if not image_path.is_file():
            print(f"Fichier manquant : {image_path}")
            continue

        try:
            image_id = Path(image_name).stem.replace("_cropped_straightened", "")
            ndvi_vector = ndvi_array.flatten()
            land_cover_vector = classify_land_cover(ndvi_vector)
            bbox_xmin, bbox_ymin, bbox_xmax, bbox_ymax = extract_bbox(str(image_path))

            record = (
                image_id, image_name,
                bbox_xmin, bbox_ymin, bbox_xmax, bbox_ymax,
                len(ndvi_vector),
                ndvi_vector.tolist(), land_cover_vector
            )

            records_to_insert.append(record)

            vectorized_data[image_name] = {
                "image_id": image_id,
                "image_name": image_name,
                "bbox": {
                    "xmin": bbox_xmin,
                    "ymin": bbox_ymin,
                    "xmax": bbox_xmax,
                    "ymax": bbox_ymax
                },
                "num_pixels": len(ndvi_vector),
                "ndvi_vector": ndvi_vector.tolist(),
                "land_cover_vector": land_cover_vector
            }

            print(f"Vectorisation : {image_name}")

        except Exception as e:
            print(f"Erreur sur {image_name} : {e}")

    # Insertion en batch
    if records_to_insert:
        conn.executemany(f"""
            INSERT INTO {table_name} (
                image_id, image_name,
                bbox_xmin, bbox_ymin, bbox_xmax, bbox_ymax,
                num_pixels,
                ndvi_vector, land_cover_vector
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, records_to_insert)
        print(f"{len(records_to_insert)} nouvelle(s) image(s) insérée(s) dans DuckDB.")
    else:
        print("Aucune nouvelle image à insérer.")

    conn.close()

    # Export JSON
    json_path = export_dir / "vectorized_ndvi.json"
    with open(json_path, "w") as f:
        json.dump(vectorized_data, f, indent=2)
    print(f"Export JSON → {json_path}")

    # Export Parquet
    df = pd.DataFrame([
        {
            "image_id": rec["image_id"],
            "image_name": rec["image_name"],
            "bbox_xmin": rec["bbox"]["xmin"],
            "bbox_ymin": rec["bbox"]["ymin"],
            "bbox_xmax": rec["bbox"]["xmax"],
            "bbox_ymax": rec["bbox"]["ymax"],
            "num_pixels": rec["num_pixels"],
            "ndvi_vector": rec["ndvi_vector"],
            "land_cover_vector": rec["land_cover_vector"]
        }
        for rec in vectorized_data.values()
    ])
    parquet_path = export_dir / "vectorized_ndvi.parquet"
    df.to_parquet(parquet_path, index=False)
    print(f"Export Parquet → {parquet_path}")

    # Export du résumé
    summary_csv = export_dir / "land_cover_summary.csv"
    summarize_land_cover(vectorized_data, summary_csv)

    print(f"Vectorisation terminée avec {len(vectorized_data)} image(s) nouvelles.")
    return vectorized_data
