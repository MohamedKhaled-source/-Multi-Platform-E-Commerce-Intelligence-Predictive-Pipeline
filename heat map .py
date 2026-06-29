import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def generate_fair_heatmap(df, selected_titles):
    df_clean = df.dropna(subset=['price', 'size', 'rate']).copy()
    if 'res_score' not in df_clean.columns:
        df_clean['res_score'] = 5.0  

    df_clean['price_per_inch'] = df_clean['price'] / df_clean['size']

    user_tvs = df_clean[df_clean['title'].isin(selected_titles)]
    if user_tvs.empty:
        return print("Error: Selected TVs not found in the database.")

    def calc_score(column, reverse=False):
        market_min = df_clean[column].min()
        market_max = df_clean[column].max()
        
        if market_min == market_max: 
            return [5.0] * len(user_tvs) 
        
        score = (user_tvs[column] - market_min) / (market_max - market_min) * 10
        return (10 - score).values if reverse else score.values

    short_names = user_tvs['title'].str[:20] + "..."
    scores_df = pd.DataFrame(index=short_names)

    scores_df['Size Score'] = calc_score('size')
    scores_df['Resolution Score'] = calc_score('res_score')
    scores_df['Rating Score'] = calc_score('rate')
    
    scores_df['Value (Price/Inch)'] = calc_score('price_per_inch', reverse=True) 

    plt.figure(figsize=(10, 5))
    sns.heatmap(scores_df.T, annot=True, cmap='Blues', cbar=False, fmt='.1f', linewidths=1)
    plt.title('Fair Device Comparison (10 = Best Value)')
    plt.tight_layout()
    plt.show()