import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_district_geojson_integrity():
    geometry_path = ROOT / "data" / "reference" / "district_boundaries.geojson"
    master_path = ROOT / "data" / "reference" / "district_master.csv"

    collection = json.loads(geometry_path.read_text(encoding="utf-8"))
    with master_path.open(encoding="utf-8-sig", newline="") as handle:
        canonical_ids = {row["district_id"] for row in csv.DictReader(handle)}

    features = collection["features"]
    shape_ids = {feature["properties"]["shape_id"] for feature in features}
    mapped_ids = {feature["properties"]["district_id"] for feature in features}

    assert collection["type"] == "FeatureCollection"
    assert len(features) == 973
    assert len(shape_ids) == 973
    assert mapped_ids <= canonical_ids
    assert sum(
        feature["properties"]["match_method"] == "inherited"
        for feature in features
    ) == 17
    assert all(
        feature["geometry"]["type"] in {"Polygon", "MultiPolygon"}
        for feature in features
    )
