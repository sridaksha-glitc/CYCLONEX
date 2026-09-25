# CYCLONEX: Meteorological Classification & Standards

## 1. Authoritative Framework
CYCLONEX adheres strictly to the **World Meteorological Organization (WMO)** and **India Meteorological Department (IMD)** Tropical Cyclone Intensity Scales for the North Indian Ocean basin (Bay of Bengal & Arabian Sea), with normalized cross-mapping to the Saffir-Simpson Hurricane Wind Scale (SSHWS) for international compatibility.

No categories, thresholds, or units are fabricated.

---

## 2. IMD / WMO Cyclone Classification Scale

| Classification | Abbr | 3-minute Sustained Winds (knots) | 3-minute Sustained Winds (km/h) | Central Pressure Deficit (hPa) | Typical Impact Tier |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Low Pressure Area** | LPA | < 17 kts | < 31 km/h | < 1.0 hPa | Minor surface agitation |
| **Depression** | D | 17 – 27 kts | 31 – 49 km/h | 1.0 – 3.0 hPa | Rough seas, squally winds |
| **Deep Depression** | DD | 28 – 33 kts | 50 – 61 km/h | 3.0 – 4.5 hPa | Moderate squalls, warning for fishermen |
| **Cyclonic Storm** | CS | 34 – 47 kts | 62 – 88 km/h | 4.5 – 8.5 hPa | Gale winds, structural damage to thatched huts |
| **Severe Cyclonic Storm** | SCS | 48 – 63 kts | 89 – 117 km/h | 8.5 – 15.0 hPa | Tree uprooting, minor power disruption |
| **Very Severe Cyclonic Storm** | VSCS | 64 – 89 kts | 118 – 166 km/h | 15.0 – 30.0 hPa | Extensive damage to structures, storm surge 1.5–3m |
| **Extremely Severe Cyclonic Storm**| ESCS | 90 – 119 kts | 167 – 221 km/h | 30.0 – 60.0 hPa | Catastrophic damage, storm surge 3–6m |
| **Super Cyclonic Storm** | SuCS | ≥ 120 kts | ≥ 222 km/h | > 60.0 hPa | Total devastation, storm surge > 6m |

---

## 3. Data Sources & Provenance

* **Satellite Infrared (IR) & Visible Bands:**
  * INSAT-3D / 3DR, NOAA GOES, or MSG IR channel 10.8µm equivalent brightness temperature ($T_B$).
  * Key feature metrics: Minimum eye/core temperature, CDO (Central Dense Overcast) symmetry, spiral band curvature, Dvorak T-number equivalent.
* **In-Situ / Atmospheric (OpenWeather & Meteorological Reanalysis):**
  * Surface pressure ($P_{sfc}$ in hPa).
  * 10m sustained wind speed ($V_{max}$ in km/h or knots).
  * Sea Surface Temperature ($SST$ in °C) & Oceanic Heat Content ($OHC$).
  * Vertical Wind Shear ($VWS$ in knots, 850–200 hPa).
  * Relative Humidity at mid-troposphere (700 hPa).
* **Authoritative Historical Archive (IBTrACS):**
  * NOAA International Best Track Archive for Climate Stewardship (v04r00).
  * Historical analogs: Cyclone Fani (2019), Cyclone Amphan (2020), Cyclone Tauktae (2021), Cyclone Biparjoy (2023), Cyclone Michaung (2023), Cyclone Remal (2024).

---

## 4. Multi-Source Fusion Architecture

```
Raw Image (IR/Vis) ────► CNN / ResNet Feature Extractor ─► 16-d Vision Vector ┐
                                                                               ├─► Multi-Source Fusion Vector (32-d)
Weather Feed (Live/Demo) ─► Atmospheric Preprocessing ───► 10-d Atmospheric ──┤       │
                                                                               │       ├─► Model A: Detection (Binary + Prob)
IBTrACS Analogs ──────────► Spatial-Temporal Normalizer ─► 6-d Historical ────┘       ├─► Model B: Classification (IMD 8-tier)
                                                                                       └─► Model C: 6h/12h/24h Prediction
```

---

## 5. Prototype Risk Index (PRI) Formula

> [!WARNING]
> The Prototype Risk Index is a decision-support metric engineered solely for demonstration and research prototyping. It is **NOT** an official warning issued by IMD, NOAA, or WMO.

The Prototype Risk Index ($PRI \in [0, 100]$) is computed through a deterministic multi-factor model:

$$PRI = w_w \cdot \mathcal{S}_{wind} + w_p \cdot \mathcal{S}_{pressure} + w_c \cdot \mathcal{S}_{confidence} + w_t \cdot \mathcal{S}_{trend} + w_e \cdot \mathcal{S}_{exposure}$$

* **$S_{wind}$ (Wind Hazard):** $\min(100, \frac{V_{max}}{220} \times 100)$
* **$S_{pressure}$ (Pressure Deficit Hazard):** $\min(100, \frac{1013 - P_{min}}{70} \times 100)$
* **$S_{confidence}$ (Model Certainty Weight):** Classification probability scalar
* **$S_{trend}$ (Rapid Intensification Penalty):** $+15$ pts if predicted $\Delta V_{24h} \ge 30 \text{ knots}$
* **Risk Tier Thresholds:**
  * `LOW`: 0 – 35
  * `MODERATE`: 36 – 60
  * `HIGH`: 61 – 80
  * `EXTREME`: 81 – 100
