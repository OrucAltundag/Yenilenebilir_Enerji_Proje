"use client";

import type { FeatureCollection, MultiPolygon, Polygon } from "geojson";
import maplibregl, {
  type ExpressionSpecification,
  type GeoJSONSource,
  type Map as MapLibreMap,
  type StyleSpecification,
} from "maplibre-gl";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  api,
  type DistrictGeometryProperties,
  type Energy,
} from "@/lib/api";

type MapProperties = DistrictGeometryProperties & {
  score: number | null;
  percentile: number | null;
};

type MapCollection = FeatureCollection<Polygon | MultiPolygon, MapProperties>;

type HoveredDistrict = {
  province: string;
  district: string;
  score: number;
  percentile: number | null;
  inherited: boolean;
};

const EMPTY_STYLE: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [
    {
      id: "background",
      type: "background",
      paint: { "background-color": "#0b1220" },
    },
  ],
};

function colorExpression(energy: Energy): ExpressionSpecification {
  const colors =
    energy === "ges"
      ? ["#382b52", "#76528d", "#c87945", "#f2b84b", "#ffe68a"]
      : ["#172d4d", "#225b83", "#2d8ead", "#58bfd0", "#b9edf1"];
  return [
    "interpolate",
    ["linear"],
    ["coalesce", ["get", "score"], 0],
    0,
    colors[0],
    25,
    colors[1],
    45,
    colors[2],
    65,
    colors[3],
    100,
    colors[4],
  ];
}

export function DistrictMap({ energy }: { energy: Energy }) {
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [hovered, setHovered] = useState<HoveredDistrict | null>(null);

  const geometryQuery = useQuery({
    queryKey: ["district-geometry"],
    queryFn: api.districtGeoJSON,
    staleTime: 60 * 60 * 1000,
  });
  const scoresQuery = useQuery({
    queryKey: ["score-map", energy],
    queryFn: () => api.scoreMap(energy),
  });

  const mapData = useMemo<MapCollection | null>(() => {
    if (!geometryQuery.data || !scoresQuery.data) return null;
    const scores = new Map(
      scoresQuery.data.items.map((item) => [item.district_id, item])
    );
    return {
      ...geometryQuery.data,
      features: geometryQuery.data.features.map((feature) => {
        const score = scores.get(feature.properties.district_id);
        return {
          ...feature,
          properties: {
            ...feature.properties,
            score: score?.score ?? null,
            percentile: score?.percentile ?? null,
          },
        };
      }),
    };
  }, [geometryQuery.data, scoresQuery.data]);

  useEffect(() => {
    if (!containerRef.current || !geometryQuery.data || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: EMPTY_STYLE,
      center: [35.2, 39.1],
      zoom: 4.45,
      minZoom: 4,
      maxZoom: 11,
      maxBounds: [
        [24.8, 34.8],
        [46.2, 43.2],
      ],
      attributionControl: false,
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    map.addControl(
      new maplibregl.AttributionControl({
        compact: true,
        customAttribution: "© OpenStreetMap · geoBoundaries",
      }),
      "bottom-right"
    );

    map.on("load", () => {
      map.addSource("districts", {
        type: "geojson",
        data: geometryQuery.data,
        promoteId: "shape_id",
      });
      map.addLayer({
        id: "district-fill",
        type: "fill",
        source: "districts",
        paint: {
          "fill-color": colorExpression("ges"),
          "fill-opacity": 0.88,
        },
      });
      map.addLayer({
        id: "district-outline",
        type: "line",
        source: "districts",
        paint: {
          "line-color": "#08101e",
          "line-width": ["interpolate", ["linear"], ["zoom"], 4, 0.35, 8, 1],
          "line-opacity": 0.9,
        },
      });
      setMapLoaded(true);
    });

    map.on("mousemove", "district-fill", (event) => {
      map.getCanvas().style.cursor = "pointer";
      const properties = event.features?.[0]?.properties;
      if (!properties) return;
      setHovered({
        province: String(properties.province),
        district: String(properties.district),
        score: Number(properties.score ?? 0),
        percentile:
          properties.percentile == null ? null : Number(properties.percentile),
        inherited: properties.match_method === "inherited",
      });
    });
    map.on("mouseleave", "district-fill", () => {
      map.getCanvas().style.cursor = "";
      setHovered(null);
    });
    map.on("click", "district-fill", (event) => {
      const districtId = event.features?.[0]?.properties?.district_id;
      if (districtId) router.push(`/district/${String(districtId)}`);
    });

    return () => {
      map.remove();
      mapRef.current = null;
      setMapLoaded(false);
    };
  }, [geometryQuery.data, router]);

  useEffect(() => {
    if (!mapLoaded || !mapData || !mapRef.current) return;
    const source = mapRef.current.getSource("districts") as GeoJSONSource | undefined;
    source?.setData(mapData);
    mapRef.current.setPaintProperty(
      "district-fill",
      "fill-color",
      colorExpression(energy)
    );
    setHovered(null);
  }, [energy, mapData, mapLoaded]);

  const error = geometryQuery.error ?? scoresQuery.error;
  if (error) {
    return (
      <div role="alert" style={{ padding: 24, color: "#fc8d59" }}>
        Harita yüklenemedi: {(error as Error).message}
      </div>
    );
  }

  return (
    <section
      aria-label="Türkiye ilçe yatırım skoru haritası"
      style={{
        position: "relative",
        overflow: "hidden",
        border: "1px solid #23314d",
        borderRadius: 12,
        background: "var(--color-surface)",
      }}
    >
      <div
        ref={containerRef}
        data-testid="district-map"
        role="img"
        aria-label={`${energy.toUpperCase()} skorlarına göre renklendirilmiş Türkiye ilçe haritası`}
        style={{ width: "100%", height: 500 }}
      />

      {(!geometryQuery.data || !scoresQuery.data || !mapLoaded) && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "grid",
            placeItems: "center",
            background: "rgba(11, 18, 32, 0.82)",
          }}
        >
          Harita yükleniyor…
        </div>
      )}

      {hovered && (
        <div
          data-testid="map-tooltip"
          style={{
            position: "absolute",
            left: 12,
            top: 12,
            maxWidth: 280,
            padding: "10px 12px",
            borderRadius: 8,
            background: "rgba(11, 18, 32, 0.94)",
            border: "1px solid #34415d",
            pointerEvents: "none",
          }}
        >
          <div style={{ fontWeight: 700 }}>
            {hovered.province} / {hovered.district}
          </div>
          <div style={{ marginTop: 4, fontSize: 13 }}>
            Skor {hovered.score.toFixed(1)}
            {hovered.percentile != null
              ? ` · Yüzdelik %${hovered.percentile.toFixed(0)}`
              : ""}
          </div>
          {hovered.inherited && (
            <div style={{ marginTop: 4, fontSize: 11, opacity: 0.65 }}>
              Tarihsel ana ilçe skoru kullanılıyor
            </div>
          )}
        </div>
      )}

      <div
        aria-label="Skor renk açıklaması"
        style={{
          position: "absolute",
          left: 12,
          bottom: 12,
          padding: "8px 10px",
          borderRadius: 8,
          background: "rgba(11, 18, 32, 0.9)",
          fontSize: 11,
        }}
      >
        <div
          style={{
            width: 180,
            height: 8,
            borderRadius: 4,
            background:
              energy === "ges"
                ? "linear-gradient(90deg,#382b52,#76528d,#c87945,#f2b84b,#ffe68a)"
                : "linear-gradient(90deg,#172d4d,#225b83,#2d8ead,#58bfd0,#b9edf1)",
          }}
        />
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 3 }}>
          <span>0 düşük</span>
          <span>100 yüksek</span>
        </div>
      </div>
    </section>
  );
}
