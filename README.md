# SmartShelf - Smart Stock Replenishment System

> **Versão em português:** [Estoque-Inteligente---PTBR](https://github.com/MaylVrosa/Estoque-Inteligente---PTBR)

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Status](https://img.shields.io/badge/status-in%20development-orange)
![License](https://img.shields.io/badge/license-MIT-green)

A stock replenishment support system for a canned-goods shop in Lisbon. It answers a practical, everyday question for the shop: **how many boxes of each product should we order?** — by combining demand forecasting with on-shelf stock counting.

The project is being built in three phases. This README explicitly separates **what already works** from **what is planned**, and is updated as each phase progresses.

---

## Project status

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Demand forecasting (Python/pandas) + order-list generation |  **Completed** |
| **Phase 2** | Stock counting via computer vision (YOLOv8) | **In progress** |
| **Phase 3** | Web interface with manager approval and PDF export | **Planned** |

*Last updated: August 2026.*

---

## Phase 1 - Demand forecasting 

The first phase is built and validated. It takes the shop's sales history and produces a per-product order list, in number of boxes.

**What it does:**
- Computes forecasted demand using a **5-year weighted average** of historical sales.
- Validated through **backtesting**, achieving a **MAPE of approximately 28%** (mean absolute percentage error).
- Converts the forecast into a **ready-to-use order list in boxes per product**.

**A note on the MAPE:** ~28% is the model's honest current figure at this stage. It is a working baseline, not a final result — accuracy is expected to improve with more data and refinement of the weighting.

---

## Phase 2 - Computer-vision counting

Currently in development. The goal is to remove manual stock counting: the manager photographs the shelf and the system counts the cans.

**Planned flow:**
1. The manager photographs the shelf.
2. The model (YOLOv8) **detects and counts the cans** per product.
3. The result feeds into the Phase 1 formula, closing the loop forecast → count → order.

**Current status (honest):**
- 📸 **Dataset being annotated** in Roboflow: ~34 photos, 4 product classes.
- 📐 **Annotation criterion:** only **fully visible** objects are annotated (cans partially hidden by others are not counted), to keep the dataset consistent.
- 💻 **Training environment:** Google Colab (T4 GPU), due to PyTorch incompatibility with Intel Mac.
- ⏳ **The model has not been trained yet.** This section will be updated with results (e.g. mAP) as soon as the first training run is complete.

---

## Phase 3 - Web interface 

Planned, not yet started.

**Goal:** give the manager a simple interface to:
- Review the count and the suggested order list.
- **Approve or manually adjust** before confirming.
- **Export the order as a PDF** to send to the supplier.

---

## Architecture decisions

Some technical choices that guide the project:

**Separation between detection and depth estimation.**
The vision model has a single responsibility: **recognising the can** in the image. Estimating how many cans sit behind one another in the shelf's depth (which the camera cannot see directly) is **post-detection logic, outside the model**. This keeps the model simple and the business logic independently testable.

**Low-confidence detections are flagged as "uncertain".**
When the model is not confident enough about a detection, the item is flagged for **manual confirmation** rather than being counted automatically. This preserves the safety margin of the order formula — it is better to ask for confirmation than to under-order because of a counting error.

**Shop data privacy.**
Real sales data and real shelf photographs are **kept private**. This repository is public and uses **synthetic data and images only**, generated for demonstration.

---

## Quick start (Phase 1)

> ⚙️ **Note:** this quick start assumes relative paths to the synthetic data included in the repository. If `smartshelf.py` still contains local absolute paths, they need to be adjusted first (see *Structure* below).

```bash
# 1. Clone the repository
git clone https://github.com/MaylVrosa/SmartShelf---EN.git
cd SmartShelf---EN

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install pandas numpy

# 4. Run the forecast
python smartshelf.py
```

> There is no `requirements.txt` yet — for now the dependencies (pandas, numpy) are installed manually. It will be added as the project grows.

---

## Repository structure

```
.
├── README.md                     # this file
├── smartshelf.py                 # Phase 1: forecast + order list
├── fase2_visao.py                # Phase 2: detection and counting (in progress)
├── .gitignore
│
├── data/                         # SYNTHETIC data (never real data)
│   ├── produtos.csv
│   ├── resumo_mensal.csv
│   ├── sazonalidade_top15.csv
│   ├── vendas_diarias_2021_2025.csv
│   ├── vendas_mensais_2021_2025.csv
│   └── vendas_semanais_2021_2025.csv
│
└── dataset/                      # Phase 2: image dataset (being annotated)
```

> **To be fixed:** `smartshelf.py` currently loads the CSVs by absolute path (e.g. `/Users/.../smartshelf/produtos.csv`). For the code to run on other machines, these paths should become relative (e.g. `data/produtos.csv`).

---

## What does NOT go into the repository

For privacy and good practice, these items are kept **out** of version control (see `.gitignore`):

- **Virtual environments** (`.venv/`, `.venv-anotacao/`, `.venv-visao/`) — each person creates their own.
- **Trained model weights** (`.pt`) — will be distributed via *GitHub Releases*, not in the repository.
- **Real shop data** — only synthetic data is public.
- **Secrets** — `.env` files, API keys, credentials.

---

## Maintenance

This README tracks the project. As each phase progresses:

- The **status table** at the top is the first thing to update.
- **Real results** (MAPE, mAP) replace estimates as soon as they exist.
- Every sentence describes what the system **does today**, not what it will do — anything unbuilt lives in the *Planned* section.

---

## License

Released under the MIT License. See the `LICENSE` file.
