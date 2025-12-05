import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 读取TSV文件
df = pd.read_csv('data/fricatives/summary.tsv', sep='\t')

# 显示数据的基本信息
print("数据前几行:")
print(df.head())
print("\n数据列名:")
print(df.columns.tolist())
print("\n唯一的音标标签:")
print(df['label'].unique())

# 更新发音部位分类，考虑卷舌音（curly-tail/r）
fricative_categories = {
    'f': 'labiodental',
    'v': 'labiodental',
    's': 'alveolar',
    'z': 'alveolar',
    'ɕ': 'alveolo-palatal',
    'x': 'velar',
}

def get_fricative_poa(label):
    if label in fricative_categories:
        return fricative_categories[label]
    return None

fricative_data = []
for idx, row in df.iterrows():
    label = row['label']
    poa = get_fricative_poa(label)
    
    if poa is not None:
        fricative_data.append({
            'Filename': row['Filename'],
            'label': label,
            'POA': poa,
            'COG': row['cog'],
            'duration': row['duration'],
            'sdev': row['sdev'],
            'skew': row['skew'],
            'kurt': row['kurt']
        })

fricative_df = pd.DataFrame(fricative_data)
cog_by_poa = fricative_df.groupby('POA')['COG'].agg([
    'mean', 'std', 'count', 'min', 'max', 
    lambda x: np.percentile(x, 25),  # Q1
    lambda x: np.percentile(x, 50),  # Med
    lambda x: np.percentile(x, 75)   # Q3
]).round(2)

cog_by_poa.columns = ['Mean_COG', 'Std_COG', 'Count', 'Min_COG', 'Max_COG', 'Q1_COG', 'Median_COG', 'Q3_COG']
cog_by_poa = cog_by_poa.reset_index()

with pd.ExcelWriter('data/fricatives/fricative_cog.xlsx') as writer:
    cog_by_poa.to_excel(writer, sheet_name='COG_by_POA', index=False)
    fricative_df.to_excel(writer, sheet_name='Fricative_Data', index=False)
    label_stats = fricative_df.groupby('label')['COG'].agg(['mean', 'std', 'count']).round(2)
    label_stats.to_excel(writer, sheet_name='COG_by_Label')

plt.figure(figsize=(14, 10))
fig = plt.figure(figsize=(15, 18))
gs = fig.add_gridspec(2, 2)
ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[1, :])

colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c18', '#9b59b6', '#1abc9c']
poa_colors = {poa: color for poa, color in zip(cog_by_poa['POA'], colors)}
bars = ax1.bar(cog_by_poa['POA'], cog_by_poa['Mean_COG'], 
               color=[poa_colors[poa] for poa in cog_by_poa['POA']], 
               alpha=0.7, yerr=cog_by_poa['Std_COG'], capsize=5, edgecolor='black')
ax1.set_title('Mean COG of Fricatives by Place of Articulation', fontsize=14, fontweight='bold')
ax1.set_ylabel('Center of Gravity (COG)', fontsize=18)
ax1.set_xlabel('Place of Articulation', fontsize=18)
ax1.grid(axis='y', alpha=0.3)

for bar, count, mean_val in zip(bars, cog_by_poa['Count'], cog_by_poa['Mean_COG']):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 100,
             f'{mean_val:.0f}\nn={count}', ha='center', va='bottom', 
             fontweight='bold', fontsize=9)

fricative_df_sorted = fricative_df.copy()
poa_order = cog_by_poa.sort_values('Mean_COG')['POA'].tolist()
fricative_df_sorted['POA'] = pd.Categorical(fricative_df_sorted['POA'], categories=poa_order)
box_plot = sns.boxplot(data=fricative_df_sorted, x='POA', y='COG', ax=ax2, 
                       palette=[poa_colors[poa] for poa in poa_order])
sns.stripplot(data=fricative_df_sorted, x='POA', y='COG', ax=ax2, 
              color='black', alpha=0.6, size=3, jitter=True)
ax2.set_title('Distribution of COG by Place of Articulation', fontsize=14, fontweight='bold')
ax2.set_ylabel('Center of Gravity (COG)', fontsize=18)
ax2.set_xlabel('Place of Articulation', fontsize=18)
ax2.grid(axis='y', alpha=0.3)

violin_plot = sns.violinplot(data=fricative_df_sorted, x='POA', y='COG', ax=ax3,
                            palette=[poa_colors[poa] for poa in poa_order], inner="quartile")
sns.stripplot(data=fricative_df_sorted, x='POA', y='COG', ax=ax3, 
              color='black', alpha=0.5, size=2, jitter=True)
ax3.set_title('Density Distribution of COG by Place of Articulation', fontsize=14, fontweight='bold')
ax3.set_ylabel('Center of Gravity (COG)', fontsize=18)
ax3.set_xlabel('Place of Articulation', fontsize=18)
ax3.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('pics/fricative_cog_by_poa.png', dpi=300, bbox_inches='tight')
plt.show()
