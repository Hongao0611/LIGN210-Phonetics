import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv('data/vowels/tones/mean_f0_results.tsv', sep='\t')
tone_categories = ['T1', 'T2', 'T3', 'T4']
df_filtered = df[df['Segment label'].isin(tone_categories)]
f0_columns = [f'F0_{i}' for i in range(1, 21)]
for col in f0_columns:
    df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')
normalized_time = np.linspace(0, 1, 20)
plt.figure(figsize=(12, 8))
colors = {'T1': 'red', 'T2': 'blue', 'T3': 'green', 'T4': 'purple'}
sample_counts = df_filtered['Segment label'].value_counts()
for tone in tone_categories:
    tone_data = df_filtered[df_filtered['Segment label'] == tone]
    f0_values = tone_data[f0_columns].values
    mean_f0 = np.nanmean(f0_values, axis=0)
    std_f0 = np.nanstd(f0_values, axis=0)
    count = sample_counts.get(tone, 0)
    plt.plot(normalized_time, mean_f0, 
             color=colors[tone], 
             linewidth=2, 
             label=f'{tone} (n={count})',
             marker='o', 
             markersize=4)
    plt.fill_between(normalized_time, 
                     mean_f0 - std_f0, 
                     mean_f0 + std_f0, 
                     alpha=0.3, 
                     color='gray')
plt.xlabel('Normalized Duration', fontsize=20)
plt.ylabel('Pitch (Hz)', fontsize=20)
# plt.title('Mean F0 with Error Bars (±1 SD) for Tone Categories', fontsize=20, pad=20)
plt.legend(title='Tone Category', fontsize=14, title_fontsize=16, loc='upper right')
plt.grid(True, alpha=0.3)
plt.xticks(fontsize=18)
plt.yticks(fontsize=18)
# plt.ylim(bottom=120)
plt.tight_layout()
plt.savefig('pics/tones.png', dpi=300, bbox_inches='tight')
plt.show()
print("Number of segments per tone category:")
print(df_filtered['Segment label'].value_counts().sort_index())