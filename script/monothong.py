import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

class VowelSpacePlotter:
    def __init__(self, tsv_path):
        self.tsv_path = tsv_path
        self.df = self.load_tsv_data()
    
    def load_tsv_data(self):
        df = pd.read_csv(self.tsv_path, sep='\t')
        df.rename(columns={
            'Filename': 'filename',
            'vowel': 'vowel',
            'F1': 'F1',
            'F2': 'F2'
        }, inplace=True)
        return df
    
    def transform_by_label(self):
        vowel_data = self.df[self.df['vowel'].notna()].copy()
        vowel_data['F1'] = pd.to_numeric(vowel_data['F1'], errors='coerce')
        vowel_data['F2'] = pd.to_numeric(vowel_data['F2'], errors='coerce')
        vowel_data = vowel_data[vowel_data['F1'].notna() & vowel_data['F2'].notna()]
        grouped = vowel_data.groupby('vowel').agg({
            'F1': ['count', 'max', 'min', 'mean', 'std'],
            'F2': ['max', 'min', 'mean', 'std']
        }).round(2)
        grouped.columns = [
            'count', 'F1_max', 'F1_min', 'F1_mean', 'F1_sd',
            'F2_max', 'F2_min', 'F2_mean', 'F2_sd'
        ]
        result_df = grouped.reset_index()
        print("Summary Statics:")
        print(result_df)
        return result_df, vowel_data
    
    def plot_vowel_space(self, save_path=None, figsize=(12, 8)):
        vowel_stats, plot_data = self.transform_by_label()
        fig = plt.figure(figsize=figsize)
        gs = fig.add_gridspec(2, 2, width_ratios=[3, 1], height_ratios=[3, 1])
        ax_main = fig.add_subplot(gs[0, 0])
        vowels = sorted(plot_data['vowel'].unique())
        colors = plt.cm.viridis(np.linspace(0, 1, len(vowels)))
        for i, vowel in enumerate(vowels):
            vowel_data = plot_data[plot_data['vowel'] == vowel]
            if vowel in vowel_stats['vowel'].values:
                stats = vowel_stats[vowel_stats['vowel'] == vowel].iloc[0]
                mean_f1 = stats['F1_mean']
                mean_f2 = stats['F2_mean']
                std_f1 = stats['F1_sd']
                std_f2 = stats['F2_sd']
                count = stats['count']
            else:
                mean_f1 = vowel_data['F1'].mean()
                mean_f2 = vowel_data['F2'].mean()
                std_f1 = vowel_data['F1'].std()
                std_f2 = vowel_data['F2'].std()
                count = len(vowel_data)
            point_size = min(30, 10 + count)
            scatter = ax_main.scatter(
                vowel_data['F2'],
                vowel_data['F1'],
                c=[colors[i]], 
                label=f"{vowel} (n={count})", 
                s=point_size,
                alpha=0.7, 
                edgecolors='white', 
                linewidth=1
            )
            
            for scale, linestyle, alpha in [(1, '--', 0.5), (2, ':', 0.3)]:
                ellipse = Ellipse(
                    xy=(mean_f2, mean_f1),
                    width=std_f2 * scale * 2, 
                    height=std_f1 * scale * 2,
                    edgecolor=colors[i], 
                    facecolor='none', 
                    linestyle=linestyle, 
                    linewidth=1.5,
                    alpha=alpha
                )
                ax_main.add_patch(ellipse)
            
            ax_main.annotate(
                vowel, 
                (mean_f2, mean_f1),
                xytext=(0, 0),
                textcoords='offset points',
                fontsize=18,
                fontweight='bold',
                ha='center',
                va='center',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.9)
            )
        
        ax_main.set_xlabel('F2 (Hz)', fontsize=18, fontweight='bold')
        ax_main.set_ylabel('F1 (Hz)', fontsize=18, fontweight='bold')
        ax_main.grid(True, alpha=0.3)
        
        ax_main.xaxis.tick_top()
        ax_main.yaxis.tick_right()
        ax_main.xaxis.set_label_position('top')
        ax_main.yaxis.set_label_position('right')
        ax_main.invert_xaxis()
        ax_main.invert_yaxis()
        ax_main.tick_params(axis='both', which='major', labelsize=18)
        ax_main.tick_params(axis='both', which='minor', labelsize=18)
        
        legend = ax_main.legend(bbox_to_anchor=(1.1, 1), loc='upper left')
        for text in legend.get_texts():
            text.set_fontsize(18)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"saved to: {save_path}")
        
        plt.show()
        return fig, ax_main


if __name__ == "__main__":
    tsv_path = "data/vowels/monothongs/summary.tsv"
    plotter = VowelSpacePlotter(tsv_path)
    plotter.plot_vowel_space(save_path="./pics/vowel_space.png")