import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv('data/vowels/dipthongs/summary.tsv', sep='\t')

all_vowels = sorted(df['vowel'].unique())
vowels_left = [v for v in all_vowels if len(v)<3]
vowels_right = [v for v in all_vowels if len(v)>=3]


def get_timepoint_data(group):
    timepoints = []
    for tp in [25, 50, 75]:
        idx = (group['VowelPercent'] - tp).abs().idxmin()
        timepoints.append(group.loc[idx])
    return pd.DataFrame(timepoints)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 12))
plt.rcParams.update({'font.size': 18})

colors_left = plt.cm.Set2(np.linspace(0, 1, len(vowels_left) if vowels_left else 1))
color_dict_left = {vowel: colors_left[i] for i, vowel in enumerate(vowels_left)}

if vowels_right:
    colors_right = plt.cm.tab20(np.linspace(0, 1, len(vowels_right)))
    color_dict_right = {vowel: colors_right[i] for i, vowel in enumerate(vowels_right)}
else:
    color_dict_right = {}

all_f1_values = []
all_f2_values = []

if vowels_left:
    df_left = df[df['vowel'].isin(vowels_left)].copy()
    df_timepoints_left = df_left.groupby(['Filename', 'vowel']).apply(get_timepoint_data).reset_index(drop=True)
    df_timepoints_left['timepoint_label'] = df_timepoints_left.groupby(['Filename', 'vowel']).cumcount()
    df_timepoints_left['timepoint_label'] = df_timepoints_left['timepoint_label'].map({0: '25%', 1: '50%', 2: '75%'})
    for vowel in vowels_left:
        vowel_data = df_timepoints_left[df_timepoints_left['vowel'] == vowel]
        for filename, group in vowel_data.groupby('Filename'):
            group = group.sort_values('VowelPercent')
            sizes = [1, 1, 1]
            for i, (idx, row) in enumerate(group.iterrows()):
                size = sizes[min(i, len(sizes)-1)]
                ax1.scatter(row['F2'], row['F1'], 
                           color=color_dict_left[vowel], s=size, zorder=3)
                all_f1_values.append(row['F1'])
                all_f2_values.append(row['F2'])
            
            for i in range(len(group) - 1):
                x_start, y_start = group.iloc[i]['F2'], group.iloc[i]['F1']
                x_end, y_end = group.iloc[i+1]['F2'], group.iloc[i+1]['F1']
                
                dx = x_end - x_start
                dy = y_end - y_start
                
                ax1.arrow(x_start, y_start, dx, dy,
                        head_width=10, head_length=12,
                        fc=color_dict_left[vowel], ec=color_dict_left[vowel],
                        length_includes_head=True, zorder=2)
            
            start_point = group.iloc[0]
            ax1.text(start_point['F2'], start_point['F1'], 
                    vowel, fontsize=25, fontweight='bold',
                    color=color_dict_left[vowel], ha='center', va='center')

ax1.set_xlabel('F2 (Hz)', fontsize=24, labelpad=20)
ax1.set_ylabel('')
ax1.set_yticklabels([])
ax1.text(0.5, -0.05, 'Diphthongs', transform=ax1.transAxes, 
         fontsize=26, fontweight='bold', ha='center')
ax1.invert_yaxis()
ax1.invert_xaxis()

ax1.xaxis.set_label_position('top')
ax1.xaxis.tick_top()
ax1.yaxis.set_label_position('right')
ax1.yaxis.tick_right()

ax1.tick_params(axis='both', which='major', labelsize=18)

ax1.grid(True, alpha=0.4, linestyle='--')

if vowels_right:
    df_right = df[df['vowel'].isin(vowels_right)].copy()
    df_timepoints_right = df_right.groupby(['Filename', 'vowel']).apply(get_timepoint_data).reset_index(drop=True)
    
    df_timepoints_right['timepoint_label'] = df_timepoints_right.groupby(['Filename', 'vowel']).cumcount()
    df_timepoints_right['timepoint_label'] = df_timepoints_right['timepoint_label'].map({0: '25%', 1: '50%', 2: '75%'})
    
    for vowel in vowels_right:
        vowel_data = df_timepoints_right[df_timepoints_right['vowel'] == vowel]
        
        for filename, group in vowel_data.groupby('Filename'):
            group = group.sort_values('VowelPercent')
            sizes = [1, 1, 1]
            for i, (idx, row) in enumerate(group.iterrows()):
                size = sizes[min(i, len(sizes)-1)]
                ax2.scatter(row['F2'], row['F1'], 
                           color=color_dict_right[vowel], s=size, zorder=3)
                all_f1_values.append(row['F1'])
                all_f2_values.append(row['F2'])
            
            for i in range(len(group) - 1):
                x_start, y_start = group.iloc[i]['F2'], group.iloc[i]['F1']
                x_end, y_end = group.iloc[i+1]['F2'], group.iloc[i+1]['F1']
                
                dx = x_end - x_start
                dy = y_end - y_start
                
                ax2.arrow(x_start, y_start, dx, dy,
                        head_width=10, head_length=12,
                        fc=color_dict_right[vowel], ec=color_dict_right[vowel],
                        length_includes_head=True, zorder=2)
            
            start_point = group.iloc[0]
            ax2.text(start_point['F2'], start_point['F1'], 
                    vowel, fontsize=25, fontweight='bold',
                    color=color_dict_right[vowel], ha='center', va='center')

ax2.set_xlabel('F2 (Hz)', fontsize=24, labelpad=20)
ax2.set_ylabel('F1 (Hz)', fontsize=24, labelpad=20)
ax2.text(0.5, -0.05, 'Vowel clusters', transform=ax2.transAxes, 
         fontsize=26, fontweight='bold', ha='center')
ax2.invert_yaxis()
ax2.invert_xaxis()
ax2.xaxis.set_label_position('top')
ax2.xaxis.tick_top()
ax2.yaxis.set_label_position('right')
ax2.yaxis.tick_right()
ax2.tick_params(axis='both', which='major', labelsize=18)
ax2.grid(True, alpha=0.2, linestyle='--')

if all_f1_values and all_f2_values:
    f1_min, f1_max = min(all_f1_values), max(all_f1_values)
    f2_min, f2_max = min(all_f2_values), max(all_f2_values)
    
    f1_margin = (f1_max - f1_min) * 0.05
    f2_margin = (f2_max - f2_min) * 0.05
    
    ax1.set_xlim(f2_max + f2_margin, f2_min - f2_margin)
    ax1.set_ylim(f1_max + f1_margin, f1_min - f1_margin)
    
    ax2.set_xlim(f2_max + f2_margin, f2_min - f2_margin)
    ax2.set_ylim(f1_max + f1_margin, f1_min - f1_margin)

plt.tight_layout()
plt.savefig('pics/diphthongs.png', dpi=300, bbox_inches='tight')
plt.show()

print("\n=== Vowels plotted ===")
print(f"Left: {len(vowels_left)}")
print(f"Right: {len(vowels_right)}")