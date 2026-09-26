# CYCLONEX — Scientific Validation Report

**Experiment:** Leakage-Safe Cyclone-Level Intensity Category Inference  
**Evaluation Standard:** Leave-One-Cyclone-Out (LOCO) Group Cross-Validation  
**Target Standard:** India Meteorological Department (IMD) 8-Tier Classification  
**Status:** Completed & Traceable  
**Disclaimer:** This document reports an academic research benchmark evaluated on empirical historical tracks. It is **NOT operational meteorological validation** and should not be used for life-critical maritime or coastal evacuation decisions.

---

## 1. Research Question

> **Can tropical cyclone intensity categories (IMD 8-Tier Scale) be inferred from non-wind physical pressure deficit and geospatial kinematics alone, without directly supplying the wind speed that definitionally determines the target category?**

The existing CYCLONEX demonstration prototype includes a baseline model (Model B) achieving **99.67% accuracy**. However, a scientific audit revealed that this high accuracy was achieved because `wind_kts` was supplied directly as an input feature. Since the IMD classification scale is defined as direct, non-overlapping intervals of sustained wind speed (e.g., Cyclonic Storm = 34–47 kt, Severe Cyclonic Storm = 48–63 kt), providing wind speed allows any decision tree or classifier to perform a trivial threshold lookup.

This experiment investigates how accurately an explainable machine learning model can infer the 8 IMD categories when:
1. Wind speed is **completely excluded**.
2. No data from the tested cyclone is present in the training set (**Leave-One-Cyclone-Out**).
3. Only **100% real, empirical historical observations** from NOAA IBTrACS are used (zero synthetic rows).

---

## 2. Dataset Lineage & Empirical Ground Truth

The experiment uses the authoritative historical North Indian Ocean (NIO) dataset:
* **Source:** NOAA International Best Track Archive for Climate Stewardship (IBTrACS v04r00).
* **File Path:** `ml/data/samples/historical/ibtracs_nio_subset.csv`
* **Total Observations:** Exactly 26 empirical track points.
* **Storms Included:** 4 major North Indian Ocean cyclonic systems:

| Cyclone Name | Season | Basin | Track Observations | Peak Wind (kt) | Min Pressure (hPa) | Max IMD Tier Reached |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **AMPHAN** | 2020 | Bay of Bengal | 5 | 130.0 | 920.0 | Super Cyclonic Storm (Tier 7) |
| **BIPARJOY** | 2023 | Arabian Sea | 7 | 90.0 | 954.0 | Extremely Severe Cyclonic Storm (Tier 6) |
| **MICHAUNG** | 2023 | Bay of Bengal | 5 | 55.0 | 986.0 | Severe Cyclonic Storm (Tier 4) |
| **REMAL** | 2024 | Bay of Bengal | 9 | 60.0 | 978.0 | Severe Cyclonic Storm (Tier 4) |

### Note on Satellite and Atmospheric Remote Sensing Features
In raw tabular IBTrACS records, continuous satellite brightness temperatures (`core_temp_k`), cloud dense overcast symmetry (`cdo_symmetry`), and localized atmospheric humidity are not provided. Rather than fabricating or synthetically interpolating these fields, this experiment adhered strictly to scientific integrity and used only verified empirical variables.

---

## 3. Feature Selection & Physical Rationale

The benchmark evaluates 8 leakage-safe features derived from barometric observations, geospatial coordinates, kinematic movement, and astronomical seasonality:

| Feature Name | Type | Physical / Meteorological Rationale |
| :--- | :--- | :--- |
| `pressure_deficit_hpa` | Barometric Physical | $1013.25\text{ hPa} - P_{\text{center}}$. Core barometric depression is the primary thermodynamic driver of vortex spin-up (Atkinson-Holliday wind-pressure relationship). |
| `central_pressure_hpa` | Barometric Physical | Direct minimum sea level pressure ($P_{\text{center}}$) measured in hPa. |
| `latitude` | Geospatial | Governs Coriolis parameter ($f = 2\Omega\sin\phi$), dictating planetary vorticity and maximum potential intensity. |
| `longitude` | Geospatial | Differentiates Arabian Sea vs. Bay of Bengal oceanic heat content and bathymetry regimes. |
| `movement_speed_kmh` | Kinematic | Vortex translation velocity; slow-moving cyclones induce oceanic upwelling and cold wakes, altering intensification. |
| `movement_direction_deg`| Kinematic | Steering azimuth governing approach to landfall or recurvature. |
| `seasonality_sin` | Cyclical Temporal | $\sin(2\pi \cdot \text{day\_of\_year} / 365.25)$. Models the bimodal pre-monsoon (April–May) and post-monsoon (October–December) NIO cyclone seasons. |
| `seasonality_cos` | Cyclical Temporal | $\cos(2\pi \cdot \text{day\_of\_year} / 365.25)$. Orthogonal cyclical component. |

---

## 4. Leakage Exclusions & Safety Controls

The following variables were strictly audited and excluded:

1. **`wind_kts` / `WMO_WIND`:** Excluded due to **definitional target leakage**. Including sustained wind speed in knots allows a decision tree to trivially memorize the IMD category boundaries.
2. **`wind_kmh`:** Excluded ($1.852 \times \text{wind\_kts}$).
3. **Synthetic Satellite Proxies (`cdo_symmetry`, `core_temp_k`):** Excluded because they were procedurally derived from the category label in earlier demo scripts.
4. **Synthetic Environmental Proxies (`humidity`, `sst`):** Excluded to prevent training on fabricated data.
5. **Future Observations / Track Lookahead:** Excluded. Only instantaneous observations at the current track point are used.

---

## 5. Cyclone-Level Split Methodology: Leave-One-Cyclone-Out (LOCO)

Standard random train/test splitting (e.g., shuffling all 26 points and taking 20% for test) is severely flawed for storm tracks:
* Points along the same cyclone track separated by 3 or 6 hours share near-identical pressure, position, and kinematics.
* Random splitting results in the model memorizing a storm's unique geographical trajectory rather than learning generalizable cyclonic physics.

**Enforced Protocol: Leave-One-Cyclone-Out (LOCO)**
* For each of the 4 cyclones $C_i \in \{\text{AMPHAN}, \text{BIPARJOY}, \text{MICHAUNG}, \text{REMAL}\}$:
  * **Train Set:** All observations belonging to the other 3 cyclones ($\sim 70\%\text{--}80\%$ of data).
  * **Test Set:** All observations belonging strictly to cyclone $C_i$.
* **Zero Contamination Guarantee:** No row belonging to the held-out cyclone is ever seen during model training.

---

## 6. Model Configuration

A simple, explainable, and reproducible ensemble was selected:
* **Algorithm:** `RandomForestClassifier` (Scikit-Learn)
* **Hyperparameters:**
  * `n_estimators = 40`
  * `max_depth = 4` (prevents leaf node memorization on small sample size)
  * `random_state = 42` (fixed deterministic seed)
* **Preprocessing:** Zero data snooping; standard deterministic features.
* **No Hyperparameter Tuning Against Held-Out Folds:** Parameters were fixed prior to fold execution to prevent information leakage through tuning.

---

## 7. Fold-by-Fold Results

Every fold evaluates an unseen, held-out cyclone:

| Fold ID | Held-Out Cyclone | Train Samples | Test Samples | Fold Accuracy | Held-Out Classes Present | Classes Unseen in Training |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **Fold 1** | **AMPHAN** | 21 | 5 | **40.0%** (2/5) | Tier 3, 4, 5, 6, 7 | **Tier 7 (SuCS)** |
| **Fold 2** | **BIPARJOY** | 19 | 7 | **14.3%** (1/7) | Tier 3, 4, 5, 6 | None |
| **Fold 3** | **MICHAUNG** | 21 | 5 | **60.0%** (3/5) | Tier 1, 3, 4 | None |
| **Fold 4** | **REMAL** | 17 | 9 | **11.1%** (1/9) | Tier 1, 2, 3, 4 | **Tier 2 (DD)** |

### Fold Analysis:
* **Fold 1 (AMPHAN):** AMPHAN contained the only Super Cyclonic Storm observation ($130\text{ kt}, 920\text{ hPa}$, Tier 7) in the dataset. Because Tier 7 never appeared in the training set of Fold 1, predicting Tier 7 was mathematically impossible out-of-sample. The model predicted Tier 4 (Severe Cyclonic Storm), adjacent in pressure profile.
* **Fold 3 (MICHAUNG):** Achieved 60.0% accuracy, correctly identifying Cyclonic Storm stages from barometric depression and movement profiles.
* **Fold 4 (REMAL):** REMAL contained the only Deep Depression (Tier 2) point in the dataset, which was unseen during training.

---

## 8. Aggregate Out-of-Fold Results

Combining predictions across all 4 held-out folds yields the aggregate, out-of-fold performance:

| Metric | Score | Interpretation |
| :--- | :---: | :--- |
| **Out-of-Fold Accuracy** | **26.92%** | 7 of 26 empirical observations correctly classified across 8 fine-grained categories. |
| **Weighted F1-Score** | **0.2260** | Balances class support across the observed distribution. |
| **Macro F1-Score** | **0.1070** | Heavily penalized by extreme categories (Tier 7, Tier 2) with zero training representation in specific folds. |
| **Macro Precision** | **0.0922** | Indicates conservative clustering toward common central categories. |
| **Macro Recall** | **0.1276** | Reflects difficulty in recovering rare extreme intensities without wind data. |
| **Adjacent-tier agreement among incorrect predictions** | **68.4%** | 13 of 19 errors classified into an immediately adjacent IMD category. |
| **Correct or Adjacent-Tier Predictions** | **76.9%** | 20 of 26 total predictions were either correct (7) or within one adjacent IMD tier (13). |

---

## 9. Confusion Matrix

The $8 \times 8$ confusion matrix across all 26 empirical observations:

```
True \ Pred      LPA(0)  D(1)  DD(2)  CS(3)  SCS(4)  VSCS(5)  ESCS(6)  SuCS(7)
-----------------------------------------------------------------------------
LPA (Tier 0)       0      0     0      0       0       0        0        0     [0 samples]
Depression (1)     0      0     0      2       0       0        0        0     [2 samples]
Deep Depr (2)      0      0     0      1       0       0        0        0     [1 sample]
Cyclonic Storm(3)  0      0     0      6       1       1        0        0     [8 samples] -> 75% precision
Severe CS (4)      0      0     0      2       1       4        0        0     [7 samples]
Very Severe CS (5) 0      0     0      0       5       0        0        0     [5 samples]
Extremely SCS (6)  0      0     0      0       2       0        0        0     [2 samples]
Super CS (7)       0      0     0      0       1       0        0        0     [1 sample]
```

### Key Error Patterns:
1. **Adjacent-Tier Agreement:** Among the incorrect predictions, 68.4% were classified into an immediately adjacent IMD tier (13 of 19 errors). Including correct predictions, 76.9% of all benchmark predictions were either correct or within one adjacent IMD tier (20 of 26).
2. **Central Clustering:** The model concentrated predictions into Tier 3 (Cyclonic Storm) and Tier 4 (Severe Cyclonic Storm), which represent the statistical median of barometric pressure in the historical sample.
3. **No False Extreme Alarms:** The model never falsely predicted a Super Cyclonic Storm (Tier 7) or Extremely Severe Cyclonic Storm (Tier 6).

---

## 10. Class Imbalance & Zero-Shot Out-of-Distribution Challenges

The empirical dataset exhibits the extreme imbalance natural to tropical cyclone climatology:

| IMD Category | Tier | Real Sample Count | Percentage of Dataset |
| :--- | :---: | :---: | :---: |
| Low Pressure Area (LPA) | 0 | 0 | 0.0% |
| Depression (D) | 1 | 2 | 7.7% |
| Deep Depression (DD) | 2 | 1 | 3.8% |
| **Cyclonic Storm (CS)** | 3 | **8** | **30.8%** |
| **Severe Cyclonic Storm (SCS)** | 4 | **7** | **26.9%** |
| Very Severe Cyclonic Storm (VSCS)| 5 | 5 | 19.2% |
| Extremely Severe Cyclonic Storm (ESCS)| 6 | 2 | 7.7% |
| Super Cyclonic Storm (SuCS) | 7 | 1 | 3.8% |

Because Super Cyclonic Storms are historically rare (Amphan 2020 was the first super cyclone in the Bay of Bengal since 1999), holding out Amphan creates a complete absence of Tier 7 during training. This mathematically caps the theoretical maximum LOCO accuracy below 100%.

---

## 11. Comparison Against Existing Benchmark

| Property | Calibrated Prototype Benchmark (Existing) | Scientific Validation Experiment (New) |
| :--- | :--- | :--- |
| **Benchmark Label** | `DEFINITIONALLY LEAKED / CALIBRATION BENCHMARK` | `SCIENTIFIC VALIDATION EXPERIMENT` |
| **Includes Wind Speed?** | **YES** (`wind_kts` included directly) | **NO** (`wind_kts` completely excluded) |
| **Splitting Strategy** | Random 75/25 split (permits cross-track leakage) | **Leave-One-Cyclone-Out (Zero storm overlap)** |
| **Data Nature** | 26 real rows + 1,200 synthetically augmented rows | **100% Empirical IBTrACS Rows (26 rows)** |
| **Accuracy Reported** | **99.67%** | **26.92%** |
| **Macro F1 Reported** | **0.9967** | **0.1070** |
| **What It Measures** | Demonstrates pipeline integration and verifies that the classifier implements IMD wind thresholds correctly. | Measures inferential power of non-wind pressure deficit and geospatial kinematics on unseen storms. |
| **Operational Claim** | NOT operational accuracy. | NOT operational accuracy. |

---

## 12. Scientific Limitations

1. **Sample Size:** The verified empirical subset contains 26 track points across 4 storms. While scientifically rigorous, this sample size is insufficient to train complex multi-parameter deep networks without overfitting.
2. **Absence of Co-located Continuous Satellite Radiometry:** Multi-spectral infrared brightness temperature (e.g. INSAT-3D TIR1/TIR2/WV) was not co-located for all 26 historical tracks in tabular form.
3. **Discrete 8-Tier Boundary Arbitrariness:** The IMD scale partitions a continuous thermodynamic continuum into discrete buckets. A storm with 47 kt wind is Tier 3; at 48 kt it is Tier 4. Pressure deficit alone cannot perfectly resolve boundary threshold crossings of $\pm 1\text{ knot}$.

---

## 13. Safe Interpretation & Guidance for Hackathon Judges

When presenting these results to judges and meteorologists:

> "In our demonstration prototype, Model B achieves 99.67% accuracy as a calibrated baseline because it directly consumes wind speed, verifying that our software correctly maps IMD thresholds.
>
> Among the incorrect predictions, 68.4% were classified into an immediately adjacent IMD tier (13 of 19 errors). Including correct predictions, 76.9% of all benchmark predictions were either correct or within one adjacent IMD tier (20 of 26).
>
> The result suggests that pressure deficit and track kinematics may contain useful physical signal for intensity estimation when sustained wind is unavailable, but the four-cyclone, 26-observation benchmark is too small to establish operational performance."
