import tkinter as tk
from tkinter import ttk
import pandas as pd
import math
import threading
import subprocess
import sys
import networkx as nx

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import seaborn as sns
import mplcursors

BG     = "#F7F9FC"
WHITE  = "#FFFFFF"
GREEN  = "#4CAF50"
ORANGE = "#FF9800"
DARK   = "#333333"
GREY   = "#777777"


def load_and_clean_data(filepath):
    try:
        df = pd.read_csv(filepath)
        df['price'] = df['price'].astype(str).str.replace('EGP', '', regex=False).str.replace(',', '', regex=False)
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['warranty'] = df['warranty'].astype(str).str.extract(r"(\d+)")
        df['warranty'] = pd.to_numeric(df['warranty'], errors='coerce')
        df["rate"] = pd.to_numeric(df["rate"], errors='coerce')
        df['size'] = df['size'].astype(str).str.extract(r"(\d+)")
        df["size"] = pd.to_numeric(df['size'], errors='coerce')

        df_clean = df.dropna(subset=['price', 'size', 'rate']).copy()
        df_clean['Tier'] = pd.qcut(df_clean['price'], q=3, labels=[0, 1, 2], duplicates='drop')
        return df_clean
    except FileNotFoundError:
        return pd.DataFrame()


def embed_figure(fig, parent_frame):
    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)


def build_kpi_card(parent, title, value, column):
    card = tk.Frame(parent, bg=WHITE, relief="groove", bd=1)
    card.grid(row=0, column=column, padx=10, pady=5, sticky="ew")

    tk.Label(card, text=title, bg=WHITE, fg=GREY,
             font=("Arial", 11)).pack(pady=(12, 0))
    tk.Label(card, text=value, bg=WHITE, fg=ORANGE,
             font=("Arial", 18, "bold")).pack(pady=(4, 12))


def draw_dashboard_charts(parent, df):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    fig.patch.set_facecolor(BG)

    if 'brand' in df.columns:
        top_brands = df['brand'].value_counts().head(10)
        ax1.bar(top_brands.index, top_brands.values, color=GREEN)
        ax1.set_title("Top 10 Brands")
        ax1.tick_params(axis='x', rotation=45)

    col_to_use = 'size'
    if 'resolution' in df.columns:
        col_to_use = 'resolution'

    if col_to_use in df.columns:
        pie_data = df[col_to_use].value_counts().head(6)
        ax2.pie(pie_data, labels=pie_data.index, autopct='%1.1f%%',
                colors=plt.cm.Set2.colors, startangle=90)
        ax2.set_title("Distribution by " + col_to_use)

    plt.tight_layout()
    embed_figure(fig, parent)


def make_home_view(parent, app):
    frame = tk.Frame(parent, bg=BG)
    frame.grid_rowconfigure(2, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    banner = tk.Frame(frame, bg=GREEN)
    banner.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
    tk.Label(banner, text="Executive Data Overview", bg=GREEN, fg=WHITE,
             font=("Arial", 20, "bold")).pack(pady=12)

    kpi_row = tk.Frame(frame, bg=BG)
    kpi_row.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
    for i in range(5):
        kpi_row.grid_columnconfigure(i, weight=1)

    df = app.data
    if df is None or df.empty:
        tk.Label(kpi_row, text="No Data. Run Scraper.", fg="red", bg=BG).grid(row=0, column=0)
    else:
        build_kpi_card(kpi_row, "Total Devices",  f"{len(df):,}",                    0)
        build_kpi_card(kpi_row, "Unique Brands",  f"{df['brand'].nunique()}",         1)
        build_kpi_card(kpi_row, "Avg Price",      f"{df['price'].mean():,.0f} EGP",   2)
        build_kpi_card(kpi_row, "Avg Rating",     f"{df['rate'].mean():.1f} Star",    3)
        build_kpi_card(kpi_row, "Avg Warranty",   f"{df['warranty'].mean():.1f} Yrs", 4)

        chart_frame = tk.Frame(frame, bg=BG)
        chart_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        draw_dashboard_charts(chart_frame, df)

    return frame


def do_search(tree, app, search_var, brand_var, size_var, min_var, max_var):
    df = app.data
    if df is None or df.empty:
        return

    query = search_var.get().strip()
    if query:
        df = df[df['title'].str.contains(query, case=False, na=False, regex=True)]

    if brand_var.get() != "All Brands":
        df = df[df['brand'] == brand_var.get()]

    if size_var.get() != "All Sizes":
        df = df[df['size'].astype(str) == size_var.get()]

    try:
        df = df[df['price'] >= float(min_var.get())]
    except ValueError:
        pass

    try:
        df = df[df['price'] <= float(max_var.get())]
    except ValueError:
        pass

    for item in tree.get_children():
        tree.delete(item)

    for _, row in df.head(100).iterrows():
        tree.insert("", "end", values=(
            str(row.get('title', ''))[:60] + "...",
            row.get('brand', 'N/A'),
            row.get('size',  'N/A'),
            f"{row.get('price', 0):,.0f} EGP",
            row.get('rate',  'N/A')
        ))


def make_search_view(parent, app):
    frame = tk.Frame(parent, bg=BG)
    frame.grid_rowconfigure(2, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    df = app.data

    search_frame = tk.Frame(frame, bg=WHITE, relief="groove", bd=1)
    search_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

    search_var = tk.StringVar()
    search_entry = tk.Entry(search_frame, textvariable=search_var,
                            font=("Arial", 16), relief="flat", bg=WHITE)
    search_entry.insert(0, "Search...")
    search_entry.pack(fill="x", padx=20, pady=12)

    filter_frame = tk.Frame(frame, bg=WHITE, relief="groove", bd=1)
    filter_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

    brand_var = tk.StringVar(value="All Brands")
    size_var  = tk.StringVar(value="All Sizes")
    min_var   = tk.StringVar()
    max_var   = tk.StringVar()

    brands = ["All Brands"] + (df['brand'].dropna().unique().tolist() if df is not None and not df.empty else [])
    sizes  = ["All Sizes"]  + (df['size'].dropna().astype(str).unique().tolist() if df is not None and not df.empty else [])

    tk.Label(filter_frame, text="Brand:", bg=WHITE).pack(side="left", padx=(15, 4))
    tk.OptionMenu(filter_frame, brand_var, *brands).pack(side="left", padx=4)

    tk.Label(filter_frame, text="Size:", bg=WHITE).pack(side="left", padx=(15, 4))
    tk.OptionMenu(filter_frame, size_var, *sizes).pack(side="left", padx=4)

    tk.Label(filter_frame, text="Min Price:", bg=WHITE).pack(side="left", padx=(15, 4))
    tk.Entry(filter_frame, textvariable=min_var, width=8).pack(side="left", padx=4)

    tk.Label(filter_frame, text="Max Price:", bg=WHITE).pack(side="left", padx=(15, 4))
    tk.Entry(filter_frame, textvariable=max_var, width=8).pack(side="left", padx=4, pady=10)

    table_frame = tk.Frame(frame, bg=WHITE)
    table_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")

    cols = ("Title", "Brand", "Size", "Price", "Rating")
    tree = ttk.Treeview(table_frame, columns=cols, show="headings")
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=100 if col in ("Size", "Price", "Rating") else 300)

    sb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=sb.set)
    sb.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True)

    trigger = lambda *_: do_search(tree, app, search_var, brand_var, size_var, min_var, max_var)
    search_entry.bind("<KeyRelease>", trigger)
    brand_var.trace_add("write", trigger)
    size_var.trace_add("write",  trigger)
    min_var.trace_add("write",   trigger)
    max_var.trace_add("write",   trigger)

    do_search(tree, app, search_var, brand_var, size_var, min_var, max_var)

    return frame


def start_scraping(btn, log_box, app):
    btn.config(state="disabled", text="Running...")
    log_box.delete("1.0", "end")

    def run():
        log_box.insert("end", "Starting scraper...\n")
        try:
            process = subprocess.Popen(
                [sys.executable, "selenium of the phase1.py"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            for line in iter(process.stdout.readline, ''):
                log_box.insert("end", line)
                log_box.see("end")

            process.wait()
            log_box.insert("end", f"\n--- Done. Exit code {process.returncode} ---\n")

            if process.returncode == 0:
                log_box.insert("end", "Refreshing data...\n")
                app.data = load_and_clean_data("data_sheet _best_output.csv")

        except Exception as e:
            log_box.insert("end", f"ERROR: {e}\n")
        finally:
            btn.config(state="normal", text="Start Scraper")

    threading.Thread(target=run, daemon=True).start()


def make_scraper_view(parent, app):
    frame = tk.Frame(parent, bg=BG)
    frame.grid_rowconfigure(1, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    ctrl = tk.Frame(frame, bg=WHITE, relief="groove", bd=1)
    ctrl.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
    tk.Label(ctrl, text="Headless Data Acquisition",
             bg=WHITE, fg=DARK, font=("Arial", 14, "bold")).pack(side="left", padx=20, pady=15)

    log_box = tk.Text(frame, font=("Courier", 11), bg=WHITE, fg=DARK, relief="groove")
    log_box.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

    btn = tk.Button(ctrl, text="▶ Start Scraper", bg=ORANGE, fg=WHITE,
                    font=("Arial", 12, "bold"), relief="flat", padx=15)
    btn.config(command=lambda: start_scraping(btn, log_box, app))
    btn.pack(side="right", padx=20, pady=15)

    return frame


def draw_3d_chart(parent, df):
    color_map = {0: 'green', 1: 'red', 2: 'blue'}
    point_colors = df['Tier'].astype(int).map(color_map)

    fig = plt.figure(figsize=(10, 7), facecolor=WHITE)
    ax = fig.add_subplot(projection='3d')
    ax.set_facecolor(WHITE)

    scatter = ax.scatter(df['price'], df['size'], df['rate'],
                         c=point_colors, s=60, alpha=0.8, edgecolors='w')

    ax.set_xlabel('Price (X)')
    ax.set_ylabel('Size (Y)')
    ax.set_zlabel('Rating (Z)')
    ax.set_title('3D Market Polarization Analysis\nGreen=Best-Value | Red=Mid-Range | Blue=Premium',
                 fontsize=12, fontweight='bold')
    ax.view_init(elev=25, azim=135)
    plt.tight_layout()

    cursor = mplcursors.cursor(scatter, hover=False)

    @cursor.connect("add")
    def on_add(sel):
        index = sel.index
        row = df.iloc[index]
        label = f"Brand: {row['brand']}\nModel: {str(row['title'])[:30]}...\nPrice: {row['price']:,} EGP\nRating: {row['rate']} Stars"
        sel.annotation.set_text(label)
        sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    toolbar = NavigationToolbar2Tk(canvas, parent)
    toolbar.update()
    canvas.get_tk_widget().pack(fill="both", expand=True)


def make_3d_view(parent, app):
    frame = tk.Frame(parent, bg=BG)
    frame.pack_propagate(False)

    tk.Label(frame, text="3D Market Polarization Analysis",
             bg=BG, fg=DARK, font=("Arial", 18, "bold")).pack(pady=10)

    chart_frame = tk.Frame(frame, bg=WHITE, relief="groove", bd=1)
    chart_frame.pack(fill="both", expand=True, padx=20, pady=20)

    df = app.data
    if df is not None and not df.empty:
        draw_3d_chart(chart_frame, df)

    return frame


def draw_2d_chart(canvas_frame, app, chart_type):
    for w in canvas_frame.winfo_children():
        w.destroy()

    df = app.data
    if df is None or df.empty:
        return

    fig, ax = plt.subplots(figsize=(8, 5), facecolor=WHITE)
    ax.set_facecolor(WHITE)

    if chart_type == 'bar':
        counts = df['brand'].value_counts()
        ax.bar(counts.index, counts.values, color=GREEN, alpha=0.8)
        ax.set_ylabel("Number of Devices")

    elif chart_type == 'scatter':
        ax.scatter(df['brand'], df['price'], alpha=0.6, color=ORANGE)
        ax.set_ylabel("Prices")

    elif chart_type == 'rating':
        avg = df.groupby('brand')['rate'].mean()
        ax.plot(avg.index, avg.values, marker='o', color="blue")
        ax.set_ylabel("Average Rating")

    elif chart_type == 'warranty':
        avg = df.groupby('brand')['warranty'].mean()
        ax.plot(avg.index, avg.values, marker='s', color="red")
        ax.set_ylabel("Average Warranty")

    elif chart_type == 'stacked':
        df.groupby(['brand', 'size']).size().unstack().plot(
            kind='bar', stacked=True, ax=ax)
        ax.set_ylabel("Number of Devices")

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    embed_figure(fig, canvas_frame)


def make_matplotlib_view(parent, app):
    frame = tk.Frame(parent, bg=BG)
    frame.grid_rowconfigure(1, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    btn_row = tk.Frame(frame, bg=WHITE, relief="groove", bd=1)
    btn_row.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

    canvas_frame = tk.Frame(frame, bg=WHITE, relief="groove", bd=1)
    canvas_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

    charts = [
        ("Brands Bar",         'bar'),
        ("Prices Scatter",     'scatter'),
        ("Avg Rating",         'rating'),
        ("Avg Warranty",       'warranty'),
        ("Size/Brand Stacked", 'stacked'),
    ]
    for label, ctype in charts:
        tk.Button(btn_row, text=label, bg=GREEN, fg=WHITE,
                  font=("Arial", 11, "bold"), relief="flat", padx=10,
                  command=lambda c=ctype: draw_2d_chart(canvas_frame, app, c)
                  ).pack(side="left", padx=8, pady=12)

    return frame


def draw_network(canvas_frame, app, net_type):#yara
    for w in canvas_frame.winfo_children():
        w.destroy()

    df = app.data
    if df is None or df.empty:
        return

    G = nx.Graph()
    node_color = "gold"

    for _, row in df.iterrows():
        brand = row["brand"]

        if net_type == 'price':
            p = row["price"]
            if pd.isna(p):
                continue
            if p < 10000:
                node2 = "Budget (<10k)"
            elif p <= 25000:
                node2 = "Mid (10k-25k)"
            elif p <= 35000:
                node2 = "Upper (25k-35k)"
            else:
                node2 = "Premium (>35k)"
            node_color = "gold"

        elif net_type == 'rate':
            r = row["rate"]
            if pd.isna(r):
                continue
            if r >= 4.5:
                node2 = "Excellent (4.5+)"
            elif r >= 3.5:
                node2 = "Good (3.5-4.4)"
            else:
                node2 = "Poor (<3.5)"
            node_color = "lightgreen"

        elif net_type == 'size':
            s = row["size"]
            if pd.isna(s):
                continue
            if s <= 43:
                node2 = "Small (<=43)"
            elif s < 60:
                node2 = "Medium (44-59)"
            else:
                node2 = "Large (60+)"
            node_color = "cyan"

        elif net_type == 'warranty':
            w = row["warranty"]
            if pd.isna(w):
                continue
            node2 = f"{int(w)} Year Warranty"
            node_color = "#e9ff7e"

        G.add_edge(brand, node2)

    fig = plt.figure(figsize=(8, 6), facecolor="white")
    ax = fig.add_subplot(1, 1, 1)
    nx.draw(G, ax=ax, with_labels=True, node_color=node_color,
            edgecolors="black", linewidths=1,
            font_weight="bold", font_size=8)
    plt.tight_layout()
    embed_figure(fig, canvas_frame)


def make_network_view(parent, app):
    frame = tk.Frame(parent, bg=BG)
    frame.grid_rowconfigure(1, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    btn_row = tk.Frame(frame, bg=WHITE, relief="groove", bd=1)
    btn_row.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

    canvas_frame = tk.Frame(frame, bg=WHITE, relief="groove", bd=1)
    canvas_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

    options = [
        ("Brand vs Price Tier", 'price'),
        ("Brand vs Rating",     'rate'),
        ("Brand vs Size",       'size'),
        ("Brand vs Warranty",   'warranty'),
    ]
    for label, ntype in options:
        tk.Button(btn_row, text=label, bg=GREEN, fg=WHITE,
                  font=("Arial", 11, "bold"), relief="flat", padx=10,
                  command=lambda n=ntype: draw_network(canvas_frame, app, n)
                  ).pack(side="left", padx=8, pady=12)

    return frame


def res_to_score(r):
    r = str(r).lower()
    if 'ultra hd' in r:
        return 4
    if '4k' in r:
        return 3
    if 'full hd' in r or '1080' in r:
        return 2
    return 1


def scale_column(user_tvs, df_all, col, reverse=False):
    lo = df_all[col].min()
    hi = df_all[col].max()
    if lo == hi:
        return [5.0] * len(user_tvs)
    scores = (user_tvs[col] - lo) / (hi - lo) * 10
    return (10 - scores).tolist() if reverse else scores.tolist()


def render_heatmap(canvas_frame, app, sel_vars):
    """
    Reads the 3 selected device names, scores them across 4 metrics,
    and draws the comparison heatmap.
    """
    for w in canvas_frame.winfo_children():
        w.destroy()

    selected = [v.get() for v in sel_vars if v.get() != "— Select —"]
    if len(selected) < 2:
        tk.Label(canvas_frame, text="Select at least 2 devices.",
                 fg="red", bg=WHITE).pack(pady=30)
        return

    df = app.data
    if df is None or df.empty:
        tk.Label(canvas_frame, text="No data. Run scraper first.",
                 fg="red", bg=WHITE).pack(pady=30)
        return

    df_clean = df.dropna(subset=['price', 'size', 'rate', 'resolution']).copy()
    df_clean['res_score']      = df_clean['resolution'].apply(res_to_score)
    df_clean['price_per_inch'] = df_clean['price'] / df_clean['size']

    user_tvs = df_clean[df_clean['title'].isin(selected)].copy().reset_index(drop=True)
    if user_tvs.empty:
        tk.Label(canvas_frame, text="Could not match selected devices.",
                 fg="red", bg=WHITE).pack(pady=30)
        return

    names = (user_tvs['title'].str[:25] + "...").tolist()

    scores_df = pd.DataFrame({
        'Size Score':         scale_column(user_tvs, df_clean, 'size'),
        'Resolution Score':   scale_column(user_tvs, df_clean, 'res_score'),
        'Rating Score':       scale_column(user_tvs, df_clean, 'rate'),
        'Value (Price/Inch)': scale_column(user_tvs, df_clean, 'price_per_inch', reverse=True),
    }, index=names)

    fig, ax = plt.subplots(figsize=(10, 4), facecolor=BG)
    fig.patch.set_facecolor(BG)
    sns.heatmap(scores_df.T, annot=True, cmap='Blues',
                cbar=False, fmt='.1f', linewidths=1, ax=ax)
    ax.set_title('Fair Device Comparison  (10 = Best)', fontweight='bold')
    fig.tight_layout()
    embed_figure(fig, canvas_frame)


def make_heatmap_view(parent, app):
    """Builds the Heatmap comparison screen."""
    frame = tk.Frame(parent, bg=BG)
    frame.grid_rowconfigure(1, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    ctrl = tk.Frame(frame, bg=WHITE, relief="groove", bd=1)
    ctrl.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

    tk.Label(ctrl, text="Fair Device Comparison",
             bg=WHITE, fg=DARK, font=("Arial", 16, "bold")).pack(pady=(15, 5))
    tk.Label(ctrl, text="Select up to 3 devices to compare",
             bg=WHITE, fg=GREY, font=("Arial", 11)).pack(pady=(0, 10))

    df = app.data
    titles = ["— Select —"] + (df['title'].dropna().unique().tolist()
                                if df is not None and not df.empty else [])

    # Three device dropdowns side by side
    sel_vars = []
    drop_row = tk.Frame(ctrl, bg=WHITE)
    drop_row.pack(pady=(0, 10))

    for i in range(3):
        v = tk.StringVar(value="— Select —")
        sel_vars.append(v)
        tk.Label(drop_row, text=f"Device {i+1}:",
                 bg=WHITE, font=("Arial", 11, "bold")).grid(row=0, column=i*2, padx=(15, 4))
        tk.OptionMenu(drop_row, v, *titles).grid(row=0, column=i*2+1, padx=(0, 15), pady=10)

    canvas_frame = tk.Frame(frame, bg=WHITE, relief="groove", bd=1)
    canvas_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

    tk.Button(ctrl, text=" Compare Devices", bg=GREEN, fg=WHITE,
              font=("Arial", 12, "bold"), relief="flat", padx=15,
              command=lambda: render_heatmap(canvas_frame, app, sel_vars)
              ).pack(pady=(0, 15))

    return frame


def calc_room(res_frame, rvars, app):
    for w in res_frame.winfo_children():
        w.destroy()

    try:
        length = float(rvars[0].get())
        width  = float(rvars[1].get())
        view_d = float(rvars[2].get())

        area    = length * width
        view_in = view_d * 39.37

        opt_4k   = view_in * 2 * math.tan(math.radians(15))
        opt_1080 = view_in * 2 * math.tan(math.radians(10))

        min_size = opt_1080 * 0.85
        max_size = opt_4k   * 1.15

        df = app.data
        if df is None or df.empty:
            raise ValueError("No data loaded. Run scraper first.")

        avail = df[(df['size'] >= min_size) & (df['size'] <= max_size)].copy()

        results = [
            ("Room Area",               f"{area:.1f} m²"),
            ("Recommended Size Range",  f"{min_size:.0f}\" {max_size:.0f}\""),
            ("Best for 4K ",   f"{opt_4k:.0f}\""),
            ("Best for Full HD ",  f"{opt_1080:.0f}\""),
            ("Matching TVs in Dataset", str(len(avail))),
        ]
        for label, value in results:
            row_f = tk.Frame(res_frame, bg=WHITE)
            row_f.pack(fill="x", pady=3)
            tk.Label(row_f, text=label + ":", bg=WHITE, fg=GREY,
                     font=("Arial", 12), width=28, anchor="e").pack(side="left", padx=10)
            tk.Label(row_f, text=value, bg=WHITE, fg=DARK,
                     font=("Arial", 13, "bold")).pack(side="left", padx=10)

        if not avail.empty:
            tk.Label(res_frame, text="Top Matching TVs:",
                     bg=WHITE, fg=DARK, font=("Arial", 14, "bold")).pack(
                         anchor="w", pady=(15, 5), padx=20)

            for _, row in avail.sort_values('rate', ascending=False).head(3).iterrows():
                card = tk.Frame(res_frame, bg=BG, relief="groove", bd=1)
                card.pack(fill="x", padx=20, pady=4, ipady=8)
                tk.Label(card,
                         text=f"  {row['brand']}  |  {str(row['title'])[:55]}...",
                         bg=BG, fg=DARK, font=("Arial", 11, "bold")).pack(side="left", padx=10)
                tk.Label(card,
                         text=f"{row['price']:,.0f} EGP",
                         bg=BG, fg=GREEN, font=("Arial", 12, "bold")).pack(side="right", padx=15)

    except Exception as e:
        tk.Label(res_frame, text=f"Error: {e}",
                 fg="red", bg=WHITE, font=("Arial", 12, "bold")).pack(pady=20)


def make_room_view(parent, app):
    frame = tk.Frame(parent, bg=BG)
    frame.grid_rowconfigure(1, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    input_frame = tk.Frame(frame, bg=WHITE, relief="groove", bd=1)
    input_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

    tk.Label(input_frame, text="Room Size Virtual Assessor",
             bg=WHITE, fg=DARK, font=("Arial", 16, "bold")).pack(pady=(15, 4))
    tk.Label(input_frame, text="Enter room dimensions → get optimal TV size",
             bg=WHITE, fg=GREY, font=("Arial", 11)).pack(pady=(0, 12))

    form = tk.Frame(input_frame, bg=WHITE)
    form.pack(pady=8)

    fields = [
        ("Room Length (meters):", "5.0"),
        ("Room Width (meters):",  "4.0"),
        ("Viewing Distance (m):", "3.0"),
    ]
    rvars = []
    for i, (label, default) in enumerate(fields):
        tk.Label(form, text=label, bg=WHITE, fg=DARK,
                 font=("Arial", 12, "bold"), anchor="e", width=25
                 ).grid(row=i, column=0, padx=10, pady=6, sticky="e")
        v = tk.StringVar(value=default)
        tk.Entry(form, textvariable=v, width=12,
                 font=("Arial", 12)).grid(row=i, column=1, padx=10, pady=6, sticky="w")
        rvars.append(v)

    res_container = tk.Frame(frame, bg=WHITE, relief="groove", bd=1)
    res_container.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

    res_canvas = tk.Canvas(res_container, bg=WHITE, highlightthickness=0)
    scrollbar  = ttk.Scrollbar(res_container, orient="vertical", command=res_canvas.yview)
    res_frame  = tk.Frame(res_canvas, bg=WHITE)

    res_frame.bind("<Configure>",
                   lambda e: res_canvas.configure(scrollregion=res_canvas.bbox("all")))
    res_canvas.create_window((0, 0), window=res_frame, anchor="nw")
    res_canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    res_canvas.pack(side="left", fill="both", expand=True)

    tk.Button(input_frame, text=" Calculate", bg=GREEN, fg=WHITE,
              font=("Arial", 12, "bold"), relief="flat", padx=15,
              command=lambda: calc_room(res_frame, rvars, app)
              ).pack(pady=15)

    return frame


def make_quiz_view(parent, app):
    QUESTIONS = [
        ("What's your primary use?", [
            ("Gaming",            {"type_pref": "gaming"}),
            ("Movies/Streaming",  {"type_pref": "movies"}),
            ("Daily TV / News",   {"type_pref": "casual"}),
            ("Sports",            {"type_pref": "sports"}),
        ]),
        ("How bright is your room?", [
            ("Very bright",  {"brightness": "high"}),
            ("Moderate",     {"brightness": "medium"}),
            ("Dark/cinema",  {"brightness": "low"}),
        ]),
        ("What is your budget?", [
            ("Budget  < 15k",   {"max_price": 15000}),
            ("Mid    15k-35k",  {"max_price": 35000, "min_price": 15000}),
            ("Premium 35k-70k", {"max_price": 70000, "min_price": 35000}),
            ("Flagship > 70k",  {"min_price": 70000}),
        ]),
        ("Preferred screen size?", [
            ("Small  43 or less", {"max_size": 43}),
            ("Medium 43 to 60",   {"min_size": 43, "max_size": 60}),
            ("Large  60 plus",    {"min_size": 60}),
        ]),
        ("How important is warranty?", [
            ("Very - 2 years or more", {"min_warranty": 2}),
            ("Moderate - 1 year",      {"min_warranty": 1}),
            ("Not important",          {"min_warranty": 0}),
        ]),
    ]

    answers = {}
    current_step = [0]  # list so inner functions can modify it

    # ── main frame ──────────────────────────────────────────────
    frame = tk.Frame(parent, bg=BG)
    frame.grid_rowconfigure(1, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    # ── green banner at top ──────────────────────────────────────
    banner = tk.Frame(frame, bg=GREEN)
    banner.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
    tk.Label(banner, text="Help Me Choose",
             bg=GREEN, fg=WHITE, font=("Arial", 16, "bold")).pack(padx=20, pady=15)

    # ── white body ───────────────────────────────────────────────
    body = tk.Frame(frame, bg=WHITE, relief="groove", bd=1)
    body.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

    # step counter label  e.g. "Question 1 of 5"
    step_lbl = tk.Label(body, text="", bg=WHITE, fg=GREY, font=("Arial", 11))
    step_lbl.pack(pady=(20, 0))

    # question text label
    q_lbl = tk.Label(body, text="", bg=WHITE, fg=DARK, font=("Arial", 15, "bold"))
    q_lbl.pack(pady=(10, 20))

    # frame that holds the answer buttons
    btn_frame = tk.Frame(body, bg=WHITE)
    btn_frame.pack()

    # frame that holds the result cards
    result_frame = tk.Frame(body, bg=WHITE)
    result_frame.pack(fill="both", expand=True, padx=20, pady=10)

    # ── functions ────────────────────────────────────────────────
    def clear_frame(f):
        for widget in f.winfo_children():
            widget.destroy()

    def show_question():
        step = current_step[0]
        clear_frame(btn_frame)
        clear_frame(result_frame)

        if step >= len(QUESTIONS):
            show_results()
            return

        question_text, options = QUESTIONS[step]
        step_lbl.config(text=f"Question {step + 1} of {len(QUESTIONS)}")
        q_lbl.config(text=question_text)

        for i, (button_label, data) in enumerate(options):
            tk.Button(
                btn_frame,
                text=button_label,
                bg=GREEN, fg=WHITE,
                font=("Arial", 12, "bold"),
                relief="flat", padx=15, pady=10,
                command=lambda d=data: answer_clicked(d)
            ).grid(row=0, column=i, padx=8)

    def answer_clicked(data):
        answers.update(data)          # save this answer
        current_step[0] += 1          # move to next question
        show_question()               # refresh the screen

    def show_results():
        clear_frame(btn_frame)
        step_lbl.config(text="Based on your answers")
        q_lbl.config(text="Your TV Recommendations")

        df = app.data.copy()

        # apply every filter the user set through their answers
        if 'max_price'  in answers:
            df = df[df['price'] <= answers['max_price']]
        if 'min_price'  in answers:
            df = df[df['price'] >= answers['min_price']]
        if 'max_size'   in answers:
            df = df[df['size']  <= answers['max_size']]
        if 'min_size'   in answers:
            df = df[df['size']  >= answers['min_size']]
        if answers.get('min_warranty', 0) >= 1:
            df = df[df['warranty'].fillna(0) >= answers['min_warranty']]
        if answers.get('type_pref') == 'movies':
            df = df[df['resolution'].str.contains('4K|4k|Ultra', na=False)]

        df = df.dropna(subset=['rate']).sort_values('rate', ascending=False)

        if df.empty:
            tk.Label(result_frame, text="No matches found, showing top rated instead.",
                     fg=ORANGE, bg=WHITE, font=("Arial", 11)).pack(pady=10)
            df = app.data.dropna(subset=['rate']).sort_values('rate', ascending=False)

        medals = ["1st", "2nd", "3rd", "4th"]
        for i, (_, row) in enumerate(df.head(4).iterrows()):
            card = tk.Frame(result_frame, bg=BG, relief="groove", bd=1)
            card.pack(fill="x", pady=6, ipady=8)
            tk.Label(card,
                     text=f"{medals[i]}  {str(row['title'])[:55]}",
                     bg=BG, fg=DARK, font=("Arial", 12, "bold")).pack(anchor="w", padx=16)
            tk.Label(card,
                     text=f"{row.get('brand','?')}  |  {row.get('size','?')} inch  |  {row.get('price',0):,.0f} EGP  |  {row.get('rate','?')} stars",
                     bg=BG, fg=GREY, font=("Arial", 11)).pack(anchor="w", padx=16)

        tk.Button(result_frame, text="Restart Quiz",
                  bg=ORANGE, fg=WHITE, font=("Arial", 12, "bold"),
                  relief="flat", padx=15,
                  command=restart
                  ).pack(pady=12)

    def restart():
        answers.clear()
        current_step[0] = 0
        show_question()

    show_question()
    return frame


def make_sidebar(parent, app, show_fn):
    sidebar = tk.Frame(parent, bg=WHITE, width=200, relief="groove", bd=1)

    tk.Label(sidebar, text="E-Commerce\nArchitect",
             bg=WHITE, fg=DARK, font=("Arial", 16, "bold")).pack(pady=30)

    nav_items = [
        ("Home Dashboard",    "home"),
        ("Smart Search",      "search"),
        ("3D Analytics",      "3d"),
        ("Matplotlib 2D",     "2d"),
        ("NetworkX",          "network"),
        ("Smart Heatmap",     "heatmap"),
        ("Room Assessor",     "room"),
        ("Help Me Choose 🎮", "quiz"),
    ]
    for label, key in nav_items:
        tk.Button(sidebar, text=label, bg=GREEN, fg=WHITE,
                  font=("Arial", 12, "bold"), relief="flat",
                  command=lambda k=key: show_fn(k)
                  ).pack(fill="x", padx=15, pady=6)

    tk.Frame(sidebar, bg=WHITE).pack(fill="both", expand=True)

    tk.Button(sidebar, text="Live Scraper", bg="#E0E0E0", fg=DARK,
              font=("Arial", 12, "bold"), relief="flat",
              command=lambda: show_fn("scraper")
              ).pack(fill="x", padx=15, pady=15)

    return sidebar


class EcommerceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("E-Commerce Dashboard")
        self.geometry("1400x850")
        self.configure(bg=BG)

        self.data = load_and_clean_data("data_sheet _best_output.csv")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.container = tk.Frame(self, bg=BG)
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.views = {
            "home":    make_home_view(self.container,       self),
            "search":  make_search_view(self.container,     self),
            "scraper": make_scraper_view(self.container,    self),
            "3d":      make_3d_view(self.container,         self),
            "2d":      make_matplotlib_view(self.container, self),
            "network": make_network_view(self.container,    self),
            "heatmap": make_heatmap_view(self.container,    self),
            "room":    make_room_view(self.container,       self),
            "quiz":    make_quiz_view(self.container,       self),
        }

        for view in self.views.values():
            view.grid(row=0, column=0, sticky="nsew")

        sidebar = make_sidebar(self, self, self.show_view)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)

        self.show_view("home")

    def show_view(self, key):
        self.views[key].tkraise()


if __name__ == "__main__":
    app = EcommerceApp()
    app.mainloop()