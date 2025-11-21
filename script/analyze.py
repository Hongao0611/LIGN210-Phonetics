import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rcParams
import numpy as np

# 读取TSV文件
df = pd.read_csv('data/wk8/summarty.tsv', sep='\t', encoding='utf-16')

# 显示数据的基本信息
print("数据前几行:")
print(df.head())
print("\n数据列名:")
print(df.columns.tolist())
print("\n唯一的音标标签:")
print(df['label'].unique())

# 更新发音部位分类，考虑卷舌音（curly-tail/r）
fricative_categories = {
    # 清擦音
    's': 'alveolar',           # 齿龈清擦音
    'S': 'postalveolar',       # 龈后清擦音
    'E': 'palatal',            # 硬腭清擦音
    'C': 'palatal',            # 硬腭清擦音（替代符号）
    
    # 浊擦音  
    'z': 'alveolar',           # 齿龈浊擦音
    'y': 'velar',
    
    # 卷舌音（curly-tail/r结尾）
    'cr': 'retroflex',         # 卷舌清擦音
    'zr': 'retroflex',         # 卷舌浊擦音
    'dzr': 'retroflex',        # 卷舌塞擦音中的擦音部分
    'tcr': 'retroflex',        # 卷舌塞擦音中的擦音部分
    
    # 普通塞擦音中的擦音部分
    'ts': 'alveolar',          # ts中的s部分
    'dz': 'alveolar',          # dz中的z部分
    'tS': 'postalveolar',      # tʃ中的ʃ部分
    
    # 硬腭塞擦音中的擦音部分
    'dE': 'palatal',           # 硬腭浊塞擦音中的擦音部分
    'dC': 'palatal'            # 硬腭浊塞擦音中的擦音部分
}

def get_fricative_poa(label):
    """获取音标的擦音部分和发音部位，考虑卷舌音"""
    # 首先检查整个标签是否在字典中
    if label in fricative_categories:
        return fricative_categories[label]
    
    # 对于卷舌音，如果以'r'结尾且不在字典中，归类为retroflex
    if label.endswith('r') and label not in ['cr', 'zr', 'dzr', 'tcr']:
        return 'retroflex'
    
    # 处理其他塞擦音：提取第二个字符作为擦音部分
    if len(label) >= 2:
        # 检查是否是已知的塞擦音模式
        if label.startswith(('t', 'd')) and len(label) > 1:
            fricative_part = label[1:]
            if fricative_part in ['s', 'z', 'S', 'E', 'C']:
                # 映射到对应的POA
                poa_map = {
                    's': 'alveolar',
                    'z': 'alveolar', 
                    'S': 'postalveolar',
                    'E': 'palatal',
                    'C': 'palatal'
                }
                return poa_map.get(fricative_part, 'unknown')
    
    return None

# 提取擦音数据
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

# 创建擦音数据框
fricative_df = pd.DataFrame(fricative_data)

print(f"\n擦音数据数量: {len(fricative_df)}")
print("\n擦音数据的POA分布:")
print(fricative_df['POA'].value_counts())
print("\n擦音标签分布:")
print(fricative_df['label'].value_counts())

# 按POA计算COG的平均值和其他统计量
cog_by_poa = fricative_df.groupby('POA')['COG'].agg([
    'mean', 'std', 'count', 'min', 'max', 
    lambda x: np.percentile(x, 25),  # Q1
    lambda x: np.percentile(x, 50),  # 中位数
    lambda x: np.percentile(x, 75)   # Q3
]).round(2)

cog_by_poa.columns = ['Mean_COG', 'Std_COG', 'Count', 'Min_COG', 'Max_COG', 'Q1_COG', 'Median_COG', 'Q3_COG']
cog_by_poa = cog_by_poa.reset_index()

print("\n按POA分组的COG统计:")
print(cog_by_poa)

# 保存到Excel文件
with pd.ExcelWriter('fricative_cog_analysis.xlsx') as writer:
    cog_by_poa.to_excel(writer, sheet_name='COG_by_POA', index=False)
    fricative_df.to_excel(writer, sheet_name='Fricative_Data', index=False)
    
    # 添加按具体标签的统计
    label_stats = fricative_df.groupby('label')['COG'].agg(['mean', 'std', 'count']).round(2)
    label_stats.to_excel(writer, sheet_name='COG_by_Label')

print("\n数据已保存到 fricative_cog_analysis.xlsx")

# 绘制图表
plt.figure(figsize=(14, 10))

# 创建子图布局
fig = plt.figure(figsize=(15, 12))
gs = fig.add_gridspec(2, 2)

ax1 = fig.add_subplot(gs[0, 0])  # 条形图
ax2 = fig.add_subplot(gs[0, 1])  # 箱线图
ax3 = fig.add_subplot(gs[1, :])  # 小提琴图

# 子图1: 按POA的平均COG条形图
colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c']
poa_colors = {poa: color for poa, color in zip(cog_by_poa['POA'], colors)}

bars = ax1.bar(cog_by_poa['POA'], cog_by_poa['Mean_COG'], 
               color=[poa_colors[poa] for poa in cog_by_poa['POA']], 
               alpha=0.7, yerr=cog_by_poa['Std_COG'], capsize=5, edgecolor='black')

ax1.set_title('Mean COG of Fricatives by Place of Articulation', fontsize=14, fontweight='bold')
ax1.set_ylabel('Center of Gravity (COG)', fontsize=12)
ax1.set_xlabel('Place of Articulation', fontsize=12)
ax1.grid(axis='y', alpha=0.3)

# 在柱子上添加数值标签
for bar, count, mean_val in zip(bars, cog_by_poa['Count'], cog_by_poa['Mean_COG']):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 100,
             f'{mean_val:.0f}\nn={count}', ha='center', va='bottom', 
             fontweight='bold', fontsize=9)

# 子图2: 按POA的COG分布箱线图
fricative_df_sorted = fricative_df.copy()
# 按平均COG排序POA类别
poa_order = cog_by_poa.sort_values('Mean_COG')['POA'].tolist()
fricative_df_sorted['POA'] = pd.Categorical(fricative_df_sorted['POA'], categories=poa_order)

box_plot = sns.boxplot(data=fricative_df_sorted, x='POA', y='COG', ax=ax2, 
                       palette=[poa_colors[poa] for poa in poa_order])
sns.stripplot(data=fricative_df_sorted, x='POA', y='COG', ax=ax2, 
              color='black', alpha=0.6, size=3, jitter=True)

ax2.set_title('Distribution of COG by Place of Articulation', fontsize=14, fontweight='bold')
ax2.set_ylabel('Center of Gravity (COG)', fontsize=12)
ax2.set_xlabel('Place of Articulation', fontsize=12)
ax2.grid(axis='y', alpha=0.3)

# 子图3: 小提琴图显示分布密度
violin_plot = sns.violinplot(data=fricative_df_sorted, x='POA', y='COG', ax=ax3,
                            palette=[poa_colors[poa] for poa in poa_order], inner="quartile")
sns.stripplot(data=fricative_df_sorted, x='POA', y='COG', ax=ax3, 
              color='black', alpha=0.5, size=2, jitter=True)

ax3.set_title('Density Distribution of COG by Place of Articulation', fontsize=14, fontweight='bold')
ax3.set_ylabel('Center of Gravity (COG)', fontsize=12)
ax3.set_xlabel('Place of Articulation', fontsize=12)
ax3.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('fricative_cog_by_poa.png', dpi=300, bbox_inches='tight')
plt.show()

# 详细的统计分析
print("\n详细的统计分析:")
for poa in sorted(fricative_df['POA'].unique()):
    poa_data = fricative_df[fricative_df['POA'] == poa]['COG']
    labels_in_poa = fricative_df[fricative_df['POA'] == poa]['label'].unique()
    
    print(f"\n{poa.upper()} (n={len(poa_data)}):")
    print(f"  包含的音标: {', '.join(labels_in_poa)}")
    print(f"  均值: {poa_data.mean():.2f}")
    print(f"  标准差: {poa_data.std():.2f}")
    print(f"  范围: {poa_data.min():.2f} - {poa_data.max():.2f}")
    print(f"  中位数: {poa_data.median():.2f}")

# 如果有足够的数据，进行ANOVA检验
if len(cog_by_poa) >= 2:
    from scipy import stats
    
    anova_groups = [fricative_df[fricative_df['POA'] == poa]['COG'] for poa in cog_by_poa['POA']]
    
    # 检查每组是否有足够的数据进行ANOVA
    if all(len(group) > 1 for group in anova_groups):
        f_val, p_val = stats.f_oneway(*anova_groups)
        print(f"\nANOVA检验结果: F={f_val:.3f}, p={p_val:.3f}")
        if p_val < 0.05:
            print("不同POA之间的COG存在显著差异 (p < 0.05)")
            
            # 如果ANOVA显著，进行事后检验（Tukey HSD）
            if len(anova_groups) > 2:
                from statsmodels.stats.multicomp import pairwise_tukeyhsd
                print("\n进行Tukey HSD事后检验:")
                
                # 准备数据用于Tukey检验
                tukey_data = []
                tukey_labels = []
                for i, poa in enumerate(cog_by_poa['POA']):
                    group_data = fricative_df[fricative_df['POA'] == poa]['COG']
                    tukey_data.extend(group_data)
                    tukey_labels.extend([poa] * len(group_data))
                
                tukey_result = pairwise_tukeyhsd(tukey_data, tukey_labels, alpha=0.05)
                print(tukey_result)
        else:
            print("不同POA之间的COG没有显著差异")
    else:
        print("\n某些POA组的数据不足，无法进行ANOVA检验")

# 创建按具体音标标签的图表
plt.figure(figsize=(14, 8))

# 按标签分组计算统计量
label_stats_detailed = fricative_df.groupby('label')['COG'].agg(['mean', 'std', 'count']).round(2)
label_stats_detailed = label_stats_detailed.sort_values('mean')

# 绘制每个音标标签的COG
plt.bar(label_stats_detailed.index, label_stats_detailed['mean'], 
        yerr=label_stats_detailed['std'], capsize=5, alpha=0.7, color='skyblue', edgecolor='black')

plt.title('Mean COG by Phonetic Label', fontsize=16, fontweight='bold')
plt.ylabel('Center of Gravity (COG)', fontsize=12)
plt.xlabel('Phonetic Label', fontsize=12)
plt.xticks(rotation=45)
plt.grid(axis='y', alpha=0.3)

# 添加数量标签
for i, (label, row) in enumerate(label_stats_detailed.iterrows()):
    plt.text(i, row['mean'] + 100, f'n={int(row["count"])}', 
             ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig('fricative_cog_by_label.png', dpi=300, bbox_inches='tight')
plt.show()