import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

plt.style.use('seaborn-v0_8-darkgrid')

file_path = "data/fricatives/spectral_envolope.tsv"
df = pd.read_csv(file_path, sep='\t')
df['Frequency_kHz'] = df['Frequency'] / 1000
mean_spectra = df.groupby(['Label', 'Frequency_kHz'])['Amplitude'].mean().reset_index()
fricatives = sorted(mean_spectra['Label'].unique())
print(f"Fricatives: {fricatives}")

colors = sns.color_palette("Set2", len(fricatives))
fricative_colors = dict(zip(fricatives, colors))

fig, axes = plt.subplots(2, 3, figsize=(18, 12))
if len(fricatives) > 6:
    fricatives_to_plot = fricatives[:6]
else:
    fricatives_to_plot = fricatives
    
for idx, fricative in enumerate(fricatives_to_plot):
    row = idx // 3
    col = idx % 3
    fricative_data = mean_spectra[mean_spectra['Label'] == fricative]
    axes[row, col].plot(fricative_data['Frequency_kHz'], fricative_data['Amplitude'], 
                       linewidth=2.5, color=fricative_colors[fricative], alpha=0.8)
    axes[row, col].fill_between(fricative_data['Frequency_kHz'], 
                               fricative_data['Amplitude'], 
                               alpha=0.2, color=fricative_colors[fricative])
    title_text = f'[{fricative}]'
    axes[row, col].set_title(title_text, fontsize=18, fontweight='bold', 
                            pad=12, bbox=dict(boxstyle="round,pad=0.3", 
                                            facecolor="lightgrey", 
                                            edgecolor="gray", alpha=0.7))
    
    if row == 1:
        axes[row, col].set_xlabel('')
    else:
        axes[row, col].set_xlabel('')
        axes[row, col].set_xticklabels([])
    if col != 0:
        axes[row, col].set_ylabel('')
        axes[row, col].set_yticklabels([])
    else:
        axes[row, col].set_ylabel('')
    axes[row, col].set_xlim(0, 16)
    axes[row, col].set_ylim(-50, 50)
    
    axes[row, col].grid(True, alpha=0.3, linestyle='--', color='gray')
    axes[row, col].tick_params(axis='both', labelsize=14)

    max_amp = fricative_data['Amplitude'].max()
    min_amp = fricative_data['Amplitude'].min()
    max_freq_at_max_amp = fricative_data.loc[fricative_data['Amplitude'].idxmax(), 'Frequency_kHz']
    axes[row, col].plot(max_freq_at_max_amp, max_amp, 'o', 
                       markersize=8, color='red', alpha=0.7)
    axes[row, col].annotate(f'{max_amp:.1f} dB', 
                           xy=(max_freq_at_max_amp, max_amp),
                           xytext=(max_freq_at_max_amp + 0.8, max_amp - 3),
                           fontsize=18,
                           arrowprops=dict(arrowstyle='->', color='red', alpha=0.7))

for idx in range(len(fricatives_to_plot), 6):
    row = idx // 3
    col = idx % 3
    axes[row, col].set_visible(False)

fig.supxlabel('Frequency (kHz)', fontsize=18, fontweight='bold', y=0.02)
fig.supylabel('Intensity (dB)', fontsize=18, fontweight='bold', x=0.02)
plt.tight_layout()
plt.savefig("pics/fricatives.png", dpi=300, bbox_inches='tight')
plt.show()