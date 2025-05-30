import pandas as pd
import matplotlib.pyplot as plt
import random

def plot_lines(df, cols, st_idx):
    plt.figure(figsize=(12,3))
    x = pd.to_datetime(df.index[st_idx:])
    
    random.seed(10)
    for col in cols:
        colors = (random.random(),random.random(),random.random())
        y = df[col].iloc[st_idx:]               
        plt.plot(x, y, color=colors)
    plt.legend(cols, loc='lower left')
    plt.show()