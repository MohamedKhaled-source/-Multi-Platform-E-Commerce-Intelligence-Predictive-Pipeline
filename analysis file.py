import networkx as nx 
import matplotlib.pyplot as plt
import pandas as pd
df = pd.read_csv("data_sheet _best_output.csv")
G =nx.Graph()
brand_counts = df['brand'].value_counts()


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

plt.figure(figsize=(15, 12))

plt.subplot(2,3,1)#brand average


plt.bar(brand_counts.index,brand_counts.values ,color='green', alpha = 0.7 , label = "Brands Bar Chart")
plt.ylabel("Number Of Devices")
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', linestyle='-', alpha=0.7)
plt.tight_layout()
plt.legend()

plt.subplot(2,3,2)#prices
plt.scatter(df['brand'], df['price'], alpha=0.6)
plt.ylabel("Prices")
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', linestyle='--', alpha=0.7)

plt.subplot(2,3,3)

plt.plot(avg_rating.index, avg_rating.values,marker='o', linestyle='-', alpha=0.7)
plt.ylabel("Average Rating")
plt.title("Average Rating per Brand")
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.legend()


plt.subplot(2,3,4)
plt.plot(avg_warranty.index,avg_warranty.values ,color='y', alpha = 0.7 ,marker='o', linestyle='-', label = "warranties Bar Chart")
plt.ylabel("average warranties")
plt.xticks(rotation=45, ha='right') 
plt.grid(axis='y', linestyle='-', alpha=0.7)

plt.subplot(2,3,5)
size_counts = df.groupby(['brand', 'size']).size().unstack()
size_counts.plot(kind='bar',ax=plt.gca())
plt.ylabel("number of devices")
plt.xticks(rotation=45)
plt.legend(title="size")
plt.tight_layout()

plt.figure(figsize=(16,12))
plt.subplot(2,2,1)

G_price = nx.Graph()

for i in range(len(df)):
    brand = df.loc[i, "brand"]
    price = df.loc[i, "price"]

    if price < 10000:
        sentence = "Budget (<10k)"
    elif 10000<=price <= 25000:
        sentence = "(10k-25k)"
    elif 25000 <=price <= 35000:
        sentence = "(35k-25k)"
    elif 40000<=price <= 60000:
        sentence = "(40k-60k)"
    elif  60000 <=price :
        sentence = "(>60k)"
    G_price.add_edge(brand, sentence)

nx.draw(G_price, with_labels=True, node_color="gold",edgecolors="black", linewidths=1, font_weight="bold")
plt.title(" Brand vs Price ")
plt.axis("off")

plt.subplot(2,2,2)

G_rate = nx.Graph()
for i in range(len(df)):
    brand = df.loc[i, "brand"]
    rate = df.loc[i, "rate"]

    if pd.isna(rate):#if there is a missing rate it will skip this item
        continue

    if rate >= 4.5:
        rating = "Excellent (4.5+)"
    elif rate >= 3.5:
        rating = "Good (3.5 - 4.4)"
    else:
        rating = "Poor (<3.5)"

    G_rate.add_edge(brand, rating)

nx.draw(G_rate, with_labels=True, node_color="lightgreen",edgecolors="black", linewidths=1 ,font_weight="bold")
plt.title("Brand vs Rating ")
plt.axis("off")

plt.subplot(2,2,3)

G_size = nx.Graph()
for i in range(len(df)):
    brand = df.loc[i, "brand"]
    size = df.loc[i, "size"]

    if pd.isna(size):#if there is a missing rate it will skip this item
        continue
    if size <= 43:
        sizing = "Small size"
    elif 43 < size  < 60:
        sizing = "Medium size"
    elif 60 <= size:
        sizing = "Large size"
    G_size.add_edge(brand,sizing)
nx.draw(G_size,with_labels=True,node_color="cyan",edgecolors="black", linewidths=1 ,font_weight="bold")
plt.title("Graph for sizes")
plt.axis("off")


plt.subplot(2,2,4)

G_warranty = nx.Graph()

for i in range(len(df)):
    brand = df.loc[i, "brand"]
    warranty = df.loc[i, "warranty"]

    if pd.isna(warranty):
        continue

    warranty_node = str(int(warranty)) + " Years Warranty"
    G_warranty.add_edge(brand, warranty_node)


nx.draw(G_warranty, with_labels=True, edgecolors="black", linewidths=1,node_color="red", font_weight="bold")
plt.title(" Brand vs Warranty Years")
plt.axis("off")


plt.tight_layout()
plt.show()

#---------------------------------------------------------------------

df['price_per_inch'] = df['price'] / df['size']
df = df.dropna(subset=['rate'])
df['warranty'] = df['warranty'].fillna(0)
df['value_score'] = (df['rate'] * 15) + (df['warranty'] * 5) - (df['price_per_inch'] * 0.05)

df_sorted_by_value = df.sort_values(by='value_score', ascending=False)

print("\n--- TOP 5 BEST VALUE TVs ---")
print(df_sorted_by_value[['brand', 'size', 'price', 'rate', 'value_score']].head())

#--------------------------------------------------------------------------



