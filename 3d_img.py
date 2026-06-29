import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import mplcursors 

df = pd.read_csv("data_sheet _best_output.csv")

# Standard cleaning
df['price'] = df['price'].str.replace('EGP', '')  
df['price'] = df['price'].str.replace(',', '')
df['price'] = pd.to_numeric(df['price'])
avg_price = df.groupby('brand')['price'].mean()

df['warranty'] = df['warranty'].str.extract(r"(\d+)")
df['warranty'] = pd.to_numeric(df['warranty'])
avg_warranty = df.groupby("brand")['warranty'].mean()

df["rate"] = pd.to_numeric(df["rate"])
avg_rating = df.groupby('brand')['rate'].mean()

df['size'] = df['size'].str.extract(r"(\d+)")
df["size"] = pd.to_numeric(df['size'])
avg_size = df.groupby("brand")['size'].mean()

df_clean = df.dropna(subset=['price', 'size', 'rate']).copy()

df_clean['Tier'] = pd.qcut(df_clean['price'], q=3, labels=[0, 1, 2]) 

colors_hex = np.array(['green', 'red', 'blue'])
point_colors = colors_hex[df_clean['Tier'].astype(int)]

fig = plt.figure(figsize=(12, 9))
ax = fig.add_subplot(projection='3d')

X = df_clean['price'].values
Y = df_clean['size'].values
Z = df_clean['rate'].values

scatter = ax.scatter(X, Y, Z, c=point_colors, s=60, alpha=0.8, edgecolors='w')

ax.set_xlabel('Price (X)')
ax.set_ylabel('Size (Y)')
ax.set_zlabel('Rating (Z)')
plt.title('3D Market Polarization Analysis\nGreen=Value(Budget Winners) | RED=DANGER ZONE(Mid-Range Trap) | Blue=Premium(Luxury)', 
          fontsize=14, fontweight='bold')


cursor = mplcursors.cursor(scatter, hover=False)

@cursor.connect("add")
def on_add(sel):
    index = sel.index
    row = df_clean.iloc[index]
    
    label = (f"Brand: {row['brand']}\n"
             f"Model: {row['title'][:30]}...\n"
             f"Price: {row['price']:,} EGP\n"
             f"Rating: {row['rate']} Stars")
    
    sel.annotation.set_text(label)
    sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)

ax.view_init(elev=25, azim=135)

plt.tight_layout()
plt.show()