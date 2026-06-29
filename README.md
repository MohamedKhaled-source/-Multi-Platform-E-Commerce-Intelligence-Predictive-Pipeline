# -Multi-Platform-E-Commerce-Intelligence-Predictive-Pipeline
# Smart TV Market Analyzer 📺
### Full-Stack Data Pipeline · Web Scraping → Cleaning → Analysis → Interactive GUI

> A real-world data engineering project that scrapes live e-commerce data, cleans and analyzes it, then surfaces every insight through a polished desktop application — built end-to-end in Python.

---

## What This Project Does

Most data projects work with pre-packaged datasets. This one doesn't.

This pipeline targets **El Araby Group's smart TV catalog** — Egypt's largest electronics retailer — and builds everything from scratch: automated scraping, multi-stage cleaning, statistical analysis, and an interactive GUI that wraps every visualization into one self-contained desktop app.

**The result:** a tool that can tell you the best-value TV on the Egyptian market, how any two devices compare across four normalized dimensions, and exactly which screen size fits your room — all from live scraped data.

---

## Feature Overview

| Module | What It Does |
|---|---|
| **Dual Scraper** | Collects data via two independent methods (Requests + Selenium) |
| **Data Cleaning Pipeline** | Normalizes prices, sizes, warranties, ratings, and resolutions |
| **Statistical Analysis** | Computes per-brand aggregates and a custom value-score ranking |
| **3D Market Polarization Chart** | Interactive 3D scatter plot with click-to-inspect tooltips |
| **Network Graphs** | 4 relationship graphs mapping brands to price/rating/size/warranty tiers |
| **Fair Comparison Heatmap** | Side-by-side device comparison normalized against the full market |
| **Room Size Assessor** | Physics-based calculator that recommends optimal TV size for any room |
| **Help Me Choose Quiz** | 5-step guided recommender that filters to your perfect TV |
| **Smart Search** | Real-time filterable product table with brand, size, and price range filters |
| **Live Scraper Console** | Runs the Selenium scraper from inside the GUI with a live log stream |

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      DATA COLLECTION                         │
│                                                             │
│   requests.py          │        selenium_.py                │
│   (Static HTML pages)  │   (Dynamic JS-rendered content)    │
│   BeautifulSoup parser │   ChromeDriver automation          │
│   6 listing pages      │   "Load More" click + scroll       │
│   Per-product spec     │   Per-product visit + review       │
│   table extraction     │   extraction, images disabled      │
└────────────┬────────────────────────┬────────────────────────┘
             │                        │
             └──────────┬─────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA CLEANING                             │
│                                                             │
│  Strip EGP / commas → numeric price                         │
│  Regex extract → numeric size & warranty                    │
│  Resolution string → numeric score (720p/1080p/4K/8K)      │
│  Drop rows missing price, size, or rating                   │
│  Price-tier labeling via pd.qcut (Budget / Mid / Premium)   │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              ANALYSIS & VISUALIZATION                        │
│                                                             │
│  pandas / numpy        networkx         matplotlib          │
│  (aggregation,         (brand-tier      (2D charts,         │
│   value scoring)        graphs)          3D scatter)         │
│                                                             │
│  seaborn               mplcursors                           │
│  (comparison           (hover tooltips                      │
│   heatmap)              on 3D plot)                         │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   DESKTOP GUI (Tkinter)                      │
│                                                             │
│  9-view sidebar navigation app (1400 × 850)                 │
│  matplotlib embedded via FigureCanvasTkAgg                  │
│  Live scraper thread with real-time log output              │
│  Dropdown selectors, search fields, quiz buttons            │
└─────────────────────────────────────────────────────────────┘
```

---

## Visualization Deep-Dives

### 3D Market Polarization
Each TV is plotted at `(Price, Size, Rating)` in 3D space. Products are binned into three price tiers using `pd.qcut` and color-coded:
- 🟢 **Green** — Budget tier (strong value per price)
- 🔴 **Red** — Mid-range trap (premium price, underwhelming specs)
- 🔵 **Blue** — Flagship tier (premium everything)

Clicking any point surfaces a tooltip with brand, model, price, and rating — powered by `mplcursors`.

### Fair Comparison Heatmap
Selects up to 3 devices and scores each across four dimensions:

```
Size Score        → normalized screen size vs. full market
Resolution Score  → 720p=2 / 1080p=5 / 4K=8 / 8K=10
Rating Score      → customer rating relative to market range
Value (Price/Inch)→ inverted — cheaper per inch = higher score
```

All scores are min-max normalized `[0, 10]` against the full dataset so comparison is always relative to the market, not absolute.

### Room Size Assessor
Uses viewing-angle geometry to compute optimal screen size:

```
Optimal size (4K)   = viewing_distance_inches × 2 × tan(15°)
Optimal size (1080p) = viewing_distance_inches × 2 × tan(10°)
```

Then queries the live dataset for real products in that range, ranked by rating.

### Network Graphs (NetworkX)
Four bipartite graphs mapping brand nodes to category nodes:

| Graph | Categories |
|---|---|
| Brand vs Price Tier | Budget / Mid / Upper / Premium |
| Brand vs Rating | Excellent (4.5+) / Good / Poor |
| Brand vs Size | Small ≤43" / Medium / Large ≥60" |
| Brand vs Warranty | 1 Year / 2 Years / etc. |

---

## Value Score Formula

A custom formula ranks every TV by real-world worth:

```python
value_score = (rating × 15) + (warranty_years × 5) - (price_per_inch × 0.05)
```

This weights customer satisfaction and longevity positively, and penalizes poor size-to-price ratio — surfacing the top 5 genuinely best-value devices in the dataset.

---

## Why Two Scrapers?

| | `requests` + BeautifulSoup | Selenium |
|---|---|---|
| **Speed** | Fast (no browser overhead) | Slower (full browser) |
| **JS rendering** | No | Yes |
| **Dynamic pagination** | No | Yes (clicks "Load More") |
| **Use case** | Static HTML spec tables | Dynamic product listing pages |
| **Output** | `by_request_way1.csv` | `data_sheet_best_output.csv` |

Running both allowed direct comparison of coverage and data completeness between the two approaches.

---

## Installation & Setup

**Requirements:** Python 3.8+, Google Chrome + ChromeDriver (for Selenium)

```bash
# Clone the repository
git clone https://github.com/your-username/tv-market-analyzer.git
cd tv-market-analyzer

# Install dependencies
pip install requests beautifulsoup4 html5lib selenium pandas numpy \
            matplotlib seaborn networkx mplcursors

# (Optional) Run a fresh scrape
python selenium_.py

# Launch the GUI
python gui__full_for_project_.py
```

> If you already have `data_of_the_project.csv`, the GUI will load it immediately without needing to re-scrape.

---

## Project Structure

```
tv-market-analyzer/
│
├── requests_.py              # Scraper 1: requests + BeautifulSoup
├── selenium_.py              # Scraper 2: Selenium + ChromeDriver
│
├── analysis_file.py          # Statistical analysis + NetworkX graphs
├── 3d_img.py                 # Standalone 3D scatter plot
├── heat_map_.py              # Standalone heatmap comparison tool
│
├── gui__full_for_project_.py # Full desktop application (main entry point)
│
├── data_of_the_project.csv   # Scraped and cleaned dataset
│
└── README.md
```

---

## Dataset

Scraped from [El Araby Group](https://www.elarabygroup.com/en/tvs-and-electronics/televisions/smart-tvs) — Egypt's largest consumer electronics retailer.

| Field | Description |
|---|---|
| `title` | Full product name |
| `price` | Listed price in EGP |
| `rate` | Customer star rating |
| `brand` | Manufacturer (Sony, Samsung, LG, Hisense, TCL, …) |
| `type` | Signal type (DVB-T/T2) |
| `size` | Screen size in inches |
| `resolution` | Display resolution (1080p, 4K, 8K) |
| `warranty` | Warranty period in years |
| `link` | Product page URL |
| `review` | First customer review text |

---

## Tech Stack

```
Python 3          Core language
requests          HTTP client for static scraping
BeautifulSoup     HTML parser
Selenium          Browser automation for dynamic content
pandas            Data manipulation and aggregation
numpy             Numerical operations
matplotlib        2D charts, 3D scatter, figure embedding
seaborn           Heatmap generation
networkx          Brand-tier relationship graphs
mplcursors        Interactive hover tooltips on 3D plot
tkinter           Desktop GUI framework
threading         Non-blocking scraper execution in GUI
subprocess        Launching scraper process from inside the app
```

---

## Authors

**Mohamed Khaled Abdelhaq** · `202508546`  

Zewail City University of Science and Technology — 2025

## Copyright

© 2026 Mohamed Khaled Abdelhaq. All rights reserved.

This project is released under the MIT License. See the LICENSE file for details.
