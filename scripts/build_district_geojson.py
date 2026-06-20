"""geoBoundaries ADM2 geometrilerini Buraki ilçe kimlikleriyle eşleştirir.

Kaynak 2021 idari yapısında 973 ilçe içerir. Buraki veri seti ise 957
tarihsel/canonical ilçe kaydı kullanır. Eşleştirme sırası:

1. Normalize edilmiş ilçe adı ve tarihsel parantez içi adlar.
2. Aynı adlı ilçelerde kayıtlı ilçe merkez koordinatına yakınlık.
3. Değişen adlar için açık alias tablosu.
4. Sonradan kurulan 17 ilçe için tarihsel ana ilçenin skorunu miras alma.

Çıktı yalnızca geometri ve kimlik eşlemesini taşır; skorlar API'den güncel
olarak alınır ve frontend'de district_id üzerinden birleştirilir.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
import urllib.request
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "geoBoundaries-TUR-ADM2_simplified.geojson"
OUTPUT_PATH = ROOT / "data" / "reference" / "district_boundaries.geojson"
METADATA_PATH = ROOT / "data" / "reference" / "district_boundaries.metadata.json"
MASTER_PATH = ROOT / "data" / "reference" / "district_master.csv"
COORDINATE_SQL_PATH = ROOT / "data" / "reference" / "il_ilce_enlem_boylam.sql"

SOURCE_URL = (
    "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/"
    "releaseData/gbOpen/TUR/ADM2/"
    "geoBoundaries-TUR-ADM2_simplified.geojson"
)

# Tarihsel ad -> 2021 geometri adı. Anahtarlar normalize edilmeden yazılır.
EXPLICIT_ALIASES = {
    ("AFYONKARAHİSAR", "AFYON"): "Afyonkarahisar (Merkez İlçe)",
    ("ANKARA", "KAZAN"): "Kahramankazan",
    ("AYDIN", "AYDIN"): "Efeler",
    ("BALIKESİR", "BALIKESİR"): "Karesi",
    ("DENİZLİ", "AKKÖY"): "Pamukkale",
    ("DENİZLİ", "DENİZLİ"): "Merkezefendi",
    ("KAHRAMANMARAŞ", "KAHRAMANMARAŞ"): "Dulkadiroğlu",
    ("KAHRAMANMARAŞ", "ÇAĞLIYANCERİT"): "Çağlayancerit",
    ("KARABÜK", "KARABÜK"): "Merkez",
    ("KIRIKKALE", "KARAKEÇİLİ"): "Karakeçeli",
    ("MANİSA", "MANİSA"): "Şehzadeler",
    ("MARDİN", "MARDİN"): "Artuklu",
    ("MUĞLA", "MUĞLA"): "Menteşe",
    ("ORDU", "ORDU"): "Altınordu",
    ("SAMSUN", "ONDOKUZMAYIS(BALLICA)"): "19 Mayıs",
    ("SİİRT", "AYDINLAR"): "Tillo",
    ("TEKİRDAĞ", "TEKİRDAĞ"): "Süleymanpaşa",
    ("TRABZON", "TRABZON"): "Ortahisar",
    ("VAN", "VAN"): "İpekyolu",
    ("ZONGULDAK", "KARADENİZEREĞLİ"): "Ereğli",
    ("ÇANAKKALE", "GÖKÇEADA(İMROZ)"): "Imbros",
    ("İSTANBUL", "ADALAR"): "Prince Islands",
    ("İSTANBUL", "EYÜP"): "Eyüpsultan",
    ("ŞANLIURFA", "ŞANLIURFA"): "Haliliye",
}

# 2021'de bulunan fakat tarihsel 957 kayıtta olmayan ilçeler.
# Geometri, skorunu belirtilen tarihsel ana ilçeden alır.
INHERITED_SHAPES = (
    ("Seydikemer", "MUĞLA", "FETHİYE"),
    ("Kozlu", "ZONGULDAK", "ZONGULDAK"),
    ("Kilimli", "ZONGULDAK", "ZONGULDAK"),
    ("Karaköprü", "ŞANLIURFA", "ŞANLIURFA"),
    ("Eyyübiye", "ŞANLIURFA", "ŞANLIURFA"),
    ("Payas", "HATAY", "DÖRTYOL"),
    ("Arsuz", "HATAY", "İSKENDERUN"),
    ("Defne", "HATAY", "ANTAKYA"),
    ("Yunusemre", "MANİSA", "MANİSA"),
    ("Tuşba", "VAN", "VAN"),
    ("Altıeylül", "BALIKESİR", "BALIKESİR"),
    ("Ergene", "TEKİRDAĞ", "ÇORLU"),
    ("Kapaklı", "TEKİRDAĞ", "ÇERKEZKÖY"),
    ("Derecik", "HAKKARİ", "ŞEMDİNLİ"),
    ("Onikişubat", "KAHRAMANMARAŞ", "KAHRAMANMARAŞ"),
    ("Kemalpaşa", "ARTVİN", "HOPA"),
    ("Sultanhanı", "AKSARAY", "AKSARAY"),
)


def normalize(value: str) -> str:
    text = str(value).upper().strip().replace("İ", "I").replace("İ", "I")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z0-9]", "", text)


def name_variants(value: str) -> set[str]:
    parts = [value, value.split("(", 1)[0], *re.findall(r"\(([^)]+)\)", value)]
    variants: set[str] = set()
    for part in parts:
        cleaned = re.sub(
            r"\b(MERKEZ\s+ILCE|MERKEZI|MERKEZ|DISTRICT)\b",
            "",
            part,
            flags=re.IGNORECASE,
        )
        key = normalize(cleaned)
        if key:
            variants.add(key)
    return variants


def download_source(refresh: bool) -> None:
    if RAW_PATH.exists() and not refresh:
        return
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = RAW_PATH.with_suffix(".tmp")
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "Buraki/0.1 district-geometry-builder"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        temp_path.write_bytes(response.read())
    temp_path.replace(RAW_PATH)


def load_master() -> list[dict[str, str]]:
    with MASTER_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_coordinates() -> dict[tuple[str, str], tuple[float, float]]:
    sql = COORDINATE_SQL_PATH.read_text(encoding="utf-8")
    province_by_id = {
        match.group(1): match.group(2)
        for match in re.finditer(
            r"INSERT INTO `pk_il` VALUES \('([^']+)', '([^']+)'", sql
        )
    }
    coordinates: dict[tuple[str, str], tuple[float, float]] = {}
    pattern = re.compile(
        r"INSERT INTO `pk_ilce` VALUES \('([^']+)', '([^']+)', "
        r"'([^']+)', '([^']+)', '([^']+)'"
    )
    for match in pattern.finditer(sql):
        province = province_by_id[match.group(2)]
        district = match.group(3)
        coordinates[(province, district)] = (
            float(match.group(4)),
            float(match.group(5)),
        )
    return coordinates


def polygons(geometry: dict[str, Any]) -> list[list[list[list[float]]]]:
    if geometry["type"] == "Polygon":
        return [geometry["coordinates"]]
    if geometry["type"] == "MultiPolygon":
        return geometry["coordinates"]
    raise ValueError(f"Desteklenmeyen geometri: {geometry['type']}")


def geometry_bbox(geometry: dict[str, Any]) -> tuple[float, float, float, float]:
    points = [
        point
        for polygon in polygons(geometry)
        for ring in polygon
        for point in ring
    ]
    return (
        min(point[0] for point in points),
        min(point[1] for point in points),
        max(point[0] for point in points),
        max(point[1] for point in points),
    )


def point_in_ring(longitude: float, latitude: float, ring: list[list[float]]) -> bool:
    inside = False
    previous = len(ring) - 1
    for current, (current_lng, current_lat) in enumerate(ring):
        previous_lng, previous_lat = ring[previous]
        crosses = (current_lat > latitude) != (previous_lat > latitude)
        if crosses:
            boundary_lng = (
                (previous_lng - current_lng)
                * (latitude - current_lat)
                / (previous_lat - current_lat)
                + current_lng
            )
            if longitude < boundary_lng:
                inside = not inside
        previous = current
    return inside


def contains_point(
    geometry: dict[str, Any], longitude: float, latitude: float
) -> bool:
    return any(
        point_in_ring(longitude, latitude, polygon[0])
        and not any(
            point_in_ring(longitude, latitude, hole) for hole in polygon[1:]
        )
        for polygon in polygons(geometry)
    )


def squared_distance_to_center(
    bbox: tuple[float, float, float, float], longitude: float, latitude: float
) -> float:
    center_lng = (bbox[0] + bbox[2]) / 2
    center_lat = (bbox[1] + bbox[3]) / 2
    return (center_lng - longitude) ** 2 + (center_lat - latitude) ** 2


def choose_candidate(
    candidates: list[int],
    features: list[dict[str, Any]],
    bboxes: list[tuple[float, float, float, float]],
    longitude: float,
    latitude: float,
) -> int:
    if len(candidates) == 1:
        return candidates[0]
    containing = [
        index
        for index in candidates
        if contains_point(features[index]["geometry"], longitude, latitude)
    ]
    pool = containing or candidates
    return min(
        pool,
        key=lambda index: squared_distance_to_center(
            bboxes[index], longitude, latitude
        ),
    )


def build(refresh: bool = False) -> dict[str, Any]:
    download_source(refresh)
    source = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    source_features: list[dict[str, Any]] = source["features"]
    master = load_master()
    master_by_key = {
        (normalize(row["province"]), normalize(row["district"])): row
        for row in master
    }
    coordinates = load_coordinates()
    if len(master) != 957 or len(coordinates) != 957:
        raise RuntimeError("Canonical ilçe veya koordinat sayısı 957 değil")

    bboxes = [geometry_bbox(feature["geometry"]) for feature in source_features]
    variant_index: dict[str, set[int]] = defaultdict(set)
    for index, feature in enumerate(source_features):
        for variant in name_variants(feature["properties"]["shapeName"]):
            variant_index[variant].add(index)

    alias_by_key = {
        (normalize(province), normalize(district)): shape_name
        for (province, district), shape_name in EXPLICIT_ALIASES.items()
    }
    proposals: dict[int, list[tuple[int, str, dict[str, str]]]] = defaultdict(list)

    for row in master:
        source_key = (row["province"], row["district"])
        latitude, longitude = coordinates[source_key]
        normalized_key = (normalize(row["province"]), normalize(row["district"]))

        alias = alias_by_key.get(normalized_key)
        if alias:
            candidates = [
                index
                for index, feature in enumerate(source_features)
                if normalize(feature["properties"]["shapeName"]) == normalize(alias)
            ]
            method = "alias"
            priority = 1
        else:
            candidate_set: set[int] = set()
            for variant in name_variants(row["district"]):
                candidate_set.update(variant_index.get(variant, set()))
            candidates = list(candidate_set)
            method = "name"
            priority = 0

        if not candidates:
            candidates = [
                index
                for index, bbox in enumerate(bboxes)
                if bbox[0] <= longitude <= bbox[2]
                and bbox[1] <= latitude <= bbox[3]
                and contains_point(
                    source_features[index]["geometry"], longitude, latitude
                )
            ]
            method = "coordinate"
            priority = 2

        if not candidates:
            raise RuntimeError(f"Geometri bulunamadı: {source_key}")
        chosen = choose_candidate(
            candidates, source_features, bboxes, longitude, latitude
        )
        if len(candidates) > 1:
            method += "_proximity"
        proposals[chosen].append((priority, method, row))

    assigned: dict[int, tuple[str, dict[str, str]]] = {}
    for shape_index, shape_proposals in proposals.items():
        _, method, row = min(
            shape_proposals,
            key=lambda proposal: (
                proposal[0],
                proposal[1],
                proposal[2]["district_id"],
            ),
        )
        assigned[shape_index] = (method, row)

    inherited_count = 0
    for shape_name, parent_province, parent_district in INHERITED_SHAPES:
        parent = master_by_key[
            (normalize(parent_province), normalize(parent_district))
        ]
        candidates = [
            index
            for index, feature in enumerate(source_features)
            if index not in assigned
            and normalize(feature["properties"]["shapeName"])
            == normalize(shape_name)
        ]
        if len(candidates) != 1:
            raise RuntimeError(
                f"Miras geometri tekil değil: {shape_name} ({len(candidates)})"
            )
        assigned[candidates[0]] = ("inherited", parent)
        inherited_count += 1

    unassigned = [
        feature["properties"]["shapeName"]
        for index, feature in enumerate(source_features)
        if index not in assigned
    ]
    if unassigned:
        raise RuntimeError(f"Eşleşmeyen kaynak geometrileri: {unassigned}")

    output_features = []
    for index, source_feature in enumerate(source_features):
        method, row = assigned[index]
        source_properties = source_feature["properties"]
        output_features.append(
            {
                "type": "Feature",
                "id": source_properties["shapeID"],
                "properties": {
                    "shape_id": source_properties["shapeID"],
                    "shape_name": source_properties["shapeName"],
                    "district_id": row["district_id"],
                    "province": row["province"],
                    "district": row["district"],
                    "match_method": method,
                },
                "geometry": source_feature["geometry"],
            }
        )

    collection = {
        "type": "FeatureCollection",
        "name": "Buraki district boundaries",
        "features": output_features,
    }
    OUTPUT_PATH.write_text(
        json.dumps(collection, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    represented_ids = {
        feature["properties"]["district_id"] for feature in output_features
    }
    method_counts: dict[str, int] = defaultdict(int)
    for feature in output_features:
        method_counts[feature["properties"]["match_method"]] += 1
    metadata = {
        "source": "geoBoundaries gbOpen TUR ADM2",
        "source_url": SOURCE_URL,
        "source_revision": "9469f09",
        "source_year": 2021,
        "source_license": "Open Data Commons Open Database License 1.0",
        "source_license_url": "https://www.openstreetmap.org/copyright",
        "built_at": datetime.now(UTC).isoformat(),
        "feature_count": len(output_features),
        "canonical_district_count": len(master),
        "represented_district_count": len(represented_ids),
        "inherited_feature_count": inherited_count,
        "unrepresented_canonical_district_ids": sorted(
            {row["district_id"] for row in master} - represented_ids
        ),
        "match_methods": dict(sorted(method_counts.items())),
    }
    METADATA_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--refresh", action="store_true", help="Sabit kaynak GeoJSON'u yeniden indir"
    )
    args = parser.parse_args()
    metadata = build(refresh=args.refresh)
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
