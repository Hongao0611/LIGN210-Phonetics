import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rcParams

# 读取TSV文件
df = pd.read_csv('data/wk8/summarty.tsv', sep='\t')

# 显示数据的基本信息
print("数据前几行:")
print(df.head())
print("\n数据列名:")
print(df.columns.tolist())
print("\n唯一的音标标签:")
print(df['label'].unique())

# 定义擦音和塞擦音的擦音部分
# 根据语音学知识，擦音包括：s, z, ʃ, ʒ, f, v, θ, ð, x, ɣ, χ, ʁ, ħ, ʕ, h, ɦ
# 塞擦音的擦音部分通常由第二个字母表示
fricative_categories = {
    # 清擦音
    's': 'alveolar',      # 齿龈清擦音
    'S': 'postalveolar',  # 龈后清擦音
    'E': 'palatal',       # 硬腭清擦音
    'C': 'palatal',       # 硬腭清擦音（替代符号）
    
    # 浊擦音  
    'z': 'alveolar',      # 齿龈浊擦音
    'Z': 'postalveolar',  # 龈后浊擦音
    'r': 'alveolar',      # 齿龈浊擦音（在某些系统中）
    
    # 塞擦音中的擦音部分
    'ts': 'alveolar',     # ts中的s部分
    'dz': 'alveolar',     # dz中的z部分
    'tS': 'postalveolar', # tʃ中的ʃ部分
    'dZ': 'postalveolar', # dʒ中的ʒ部分
    'tcr': 'alveolar',    # t͡s中的s部分
    'dzr': 'alveolar',    # d͡z中的z部分
    'tsh': 'postalveolar',# tʃʰ中的ʃ部分
    'cr': 'alveolar',     # t͡s中的s部分
    'zr': 'alveolar'      # d͡z中的z部分
}

def get_fricative_poa(label):
    """获取音标的擦音部分和发音部位"""
    if label in fricative_categories:
        return fricative_categories[label]
    
    # 处理塞擦音：提取第二个字符作为擦音部分
    if len(label) >= 2:
        fricative_part = label[1:]
        if fricative_part in fricative_categories:
            return fricative_categories[fricative_part]
    
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
            'duration': row['duration']
        })

# 创建擦音数据框
fricative_df = pd.DataFrame(fricative_data)

print(f"\n擦音数据数量: {len(fricative_df)}")
print("\n擦音数据的POA分布:")
print(fricative_df['POA'].value_counts())

# 按POA计算COG的平均值
cog_by_poa = fricative_df.groupby('POA')['COG'].agg(['mean', 'std', 'count']).reset_index()
cog_by_poa.columns = ['POA', 'Mean_COG', 'Std_COG', 'Count']

print("\n按POA分组的COG平均值:")
print(cog_by_poa)

# 保存到Excel文件
with pd.ExcelWriter('fricative_cog_analysis.xlsx') as writer:
    cog_by_poa.to_excel(writer, sheet_name='COG_by_POA', index=False)
    fricative_df.to_excel(writer, sheet_name='Fricative_Data', index=False)

print("\n数据已保存到 fricative_cog_analysis.xlsx")

# 绘制图表
plt.figure(figsize=(12, 8))

# 创建子图
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# 子图1: 按POA的平均COG条形图
colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6']
bars = ax1.bar(cog_by_poa['POA'], cog_by_poa['Mean_COG'], 
               color=colors[:len(cog_by_poa)], alpha=0.7,
               yerr=cog_by_poa['Std_COG'], capsize=5)

ax1.set_title('Mean COG of Fricatives by Place of Articulation', fontsize=16, fontweight='bold')
ax1.set_ylabel('Center of Gravity (COG)', fontsize=12)
ax1.set_xlabel('Place of Articulation', fontsize=12)

# 在柱子上添加数值标签
for bar, count in zip(bars, cog_by_poa['Count']):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 100,
             f'n={count}', ha='center', va='bottom', fontweight='bold')

# 子图2: 按POA的COG分布箱线图
fricative_df_sorted = fricative_df.copy()
# 按平均COG排序POA类别
poa_order = cog_by_poa.sort_values('Mean_COG')['POA'].tolist()
fricative_df_sorted['POA'] = pd.Categorical(fricative_df_sorted['POA'], categories=poa_order)

sns.boxplot(data=fricative_df_sorted, x='POA', y='COG', ax=ax2, palette=colors[:len(poa_order)])
sns.stripplot(data=fricative_df_sorted, x='POA', y='COG', ax=ax2, 
              color='black', alpha=0.5, size=4, jitter=True)

ax2.set_title('Distribution of COG by Place of Articulation', fontsize=16, fontweight='bold')
ax2.set_ylabel('Center of Gravity (COG)', fontsize=12)
ax2.set_xlabel('Place of Articulation', fontsize=12)

plt.tight_layout()
plt.savefig('fricative_cog_by_poa.png', dpi=300, bbox_inches='tight')
plt.show()

# 额外的统计分析
print("\n详细的统计分析:")
for poa in cog_by_poa['POA']:
    poa_data = fricative_df[fricative_df['POA'] == poa]['COG']
    print(f"\n{poa} (n={len(poa_data)}):")
    print(f"  均值: {poa_data.mean():.2f}")
    print(f"  标准差: {poa_data.std():.2f}")
    print(f"  范围: {poa_data.min():.2f} - {poa_data.max():.2f}")

# 如果有足够的数据，进行ANOVA检验
if len(cog_by_poa) >= 2:
    from scipy import stats
    anova_groups = [fricative_df[fricative_df['POA'] == poa]['COG'] for poa in cog_by_poa['POA']]
    if all(len(group) > 1 for group in anova_groups):
        f_val, p_val = stats.f_oneway(*anova_groups)
        print(f"\nANOVA检验结果: F={f_val:.3f}, p={p_val:.3f}")
        if p_val < 0.05:
            print("不同POA之间的COG存在显著差异")
        else:
            print("不同POA之间的COG没有显著差异")