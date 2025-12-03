import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

class TextGridProcessor:
    def __init__(self, directory_path, output_path=None):
        self.directory_path = directory_path
        self.voiced_stops = ['p','t','k']
        self.voiceless_stops = ['pʰ','tʰ','kʰ']
        if output_path is None:
            self.output_path = os.path.join(self.directory_path, "textgrid_summary.csv")
        else:
            self.output_path = output_path
        if os.path.exists(self.output_path):
            self.df = pd.read_csv(self.output_path)
        else:
            print(f"No summary file found. Calling TextGridProcessor.process_directory()...")
            self.df = self.process_directory()
            self.df.to_csv(self.output_path, index=False, encoding='utf-8')
            print(f"Saving summary stat to: {self.output_path}")
    
    def find_textgrid_files(self):
        pattern = re.compile(r'^\d+_[a-zA-Z_]+\.TextGrid$', re.IGNORECASE)
        textgrid_files = []
        for file in os.listdir(self.directory_path):
            if pattern.match(file):
                textgrid_files.append(os.path.join(self.directory_path, file))
        return textgrid_files
    
    def parse_textgrid_file(self, file_path):
        intervals_data = []
        filename = os.path.basename(file_path)
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        vot_pattern = r'name = "vot".*?intervals: size = (\d+)(.*?)(?=item \[|\Z)'
        vot_match = re.search(vot_pattern, content, re.DOTALL)
        intervals_content = vot_match.group(2)
        interval_pattern = r'intervals \[(\d+)\]:\s*xmin = ([\d.]+)\s*xmax = ([\d.]+)\s*text = "([^"]*)"'
        intervals = re.findall(interval_pattern, intervals_content)
        for seq, xmin, xmax, text in intervals:
            intervals_data.append({
                'filename': filename,
                'interval_sequence': int(seq),
                'xmin': float(xmin),
                'xmax': float(xmax),
                'text': text if text.strip() != '' else np.nan
            })
        return intervals_data
    
    def process_directory(self):
        textgrid_files = self.find_textgrid_files()
        total_intervals = 0
        data = []
        for file_path in textgrid_files:
            intervals = self.parse_textgrid_file(file_path)
            data.extend(intervals)
            total_intervals += len(intervals)
        df = pd.DataFrame(data, columns=['filename', 'interval_sequence', 'xmin', 'xmax', 'text'])
        df = df[df['text'].notna()]
        df['label'] = df['text'].apply(lambda x: x.split(' ')[0])
        df['vot'] = df['text'].apply(lambda x: x.split(' ')[1])
        return df
    
    def calculate_statistics(self):
        self.df['vot'] = pd.to_numeric(self.df['vot'], errors='coerce')
        stats = self.df.groupby('label').agg(
            N=('vot', 'count'),
            Mean=('vot', 'mean'),
            SD=('vot', 'std'),
            Minimum=('vot', 'min'),
            Maximum=('vot', 'max')
        ).reset_index()
        stats.columns = ['Phoneme', 'N', 'Mean', 'SD', 'Minimum', 'Maximum']
        return stats
    
    def plot_vot_bar(self, save_path="vot_bar_plot.png"):
        stats = self.calculate_statistics()
        plosives = ['p', 'pʰ', 't', 'tʰ', 'k', 'kʰ']
        stats = stats[stats['Phoneme'].isin(plosives)].reset_index()
        place_mapping = {
            'p': 'bilabial', 'pʰ': 'bilabial',
            't': 'alveolar', 'tʰ': 'alveolar',
            'k': 'velar', 'kʰ': 'velar'
        }
        voicing_mapping = {
            'p': 'voiceless', 't': 'voiceless', 'k': 'voiceless',
            'pʰ': 'voiceless aspirated', 'tʰ': 'voiceless aspirated', 'kʰ': 'voiceless aspirated'
        }
        stats['Place'] = stats['Phoneme'].map(place_mapping)
        stats['Voicing'] = stats['Phoneme'].map(voicing_mapping)
        
        place_order = ['alveolar', 'bilabial', 'velar']
        phoneme_order = ['t', 'tʰ', 'p', 'pʰ', 'k', 'kʰ']
        
        stats['Place'] = pd.Categorical(stats['Place'], categories=place_order, ordered=True)
        stats['Phoneme'] = pd.Categorical(stats['Phoneme'], categories=phoneme_order, ordered=True)
        stats = stats.sort_values(['Place', 'Phoneme'])
        
        plt.figure(figsize=(12, 8))
        colors = {'voiceless': '#1f77b4', 'voiceless aspirated': '#ff7f0e'}
        bars = []
        labels = []
        
        for idx, row in stats.iterrows():
            color = colors.get(row['Voicing'], '#999999')
            bar = plt.bar(idx, row['Mean'], color=color, edgecolor='black', linewidth=1)
            bars.append(bar[0])
            labels.append(row['Phoneme'])
            
            # error bar
            if not pd.isna(row['SD']) and row['N'] > 1:  # only when N > 1
                plt.errorbar(idx, row['Mean'], yerr=row['SD'], 
                            color='black', capsize=5, capthick=1.5, linewidth=1.5)
            
            plt.text(idx, row['Mean'] + (2 if row['Mean'] > 0 else -10), 
                    f"{row['Mean']:.1f}", ha='center', va='bottom' if row['Mean'] > 0 else 'top', fontsize=18)
        
        plt.xticks(range(len(stats)), labels, fontsize=18)
        
        prev_place = None
        start_idx = 0
        for idx, place in enumerate(stats['Place']):
            if place != prev_place:
                if prev_place is not None:
                    plt.axvline(x=idx-0.5, color='gray', linestyle='--', alpha=0.5)
                    plt.text((start_idx + idx - 1) / 2, plt.ylim()[1] * 1.01, 
                            prev_place.title(), ha='center', fontsize=18, fontweight='bold')
                start_idx = idx
                prev_place = place
        plt.text((start_idx + len(stats) - 1) / 2, plt.ylim()[1] * 1.01, 
                prev_place.title(), ha='center', fontsize=18, fontweight='bold')
        plt.ylabel("Mean VOT (ms)", fontsize=18)
        plt.xlabel("Phoneme", fontsize=18)
        plt.grid(axis='y', alpha=0.3, linestyle='--')
        plt.axhline(y=0, color='black', linewidth=0.8)

        legend_elements = [
            Patch(facecolor=colors['voiceless'], edgecolor='black', label='Voiceless Unaspirated'),
            Patch(facecolor=colors['voiceless aspirated'], edgecolor='black', label='Voiceless Aspirated')
        ]
        plt.legend(handles=legend_elements, fontsize=18)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Bar plot saved to: {save_path}")
        plt.show()

    def plot_affricates_bar(self, save_path="affricates_bar_plot.png"):
        stats = self.calculate_statistics()
        affricates = ['ts', 'tsʰ', 'tɕ', 'tɕʰ']
        stats = stats[stats['Phoneme'].isin(affricates)].reset_index()
        
        place_mapping = {
            'ts': 'alveolar', 'tsʰ': 'alveolar',
            'tɕ': 'palatal', 'tɕʰ': 'palatal'
        }
        voicing_mapping = {
            'ts': 'voiceless', 'tɕ': 'voiceless',
            'tsʰ': 'voiceless aspirated', 'tɕʰ': 'voiceless aspirated'
        }
        
        stats['Place'] = stats['Phoneme'].map(place_mapping)
        stats['Voicing'] = stats['Phoneme'].map(voicing_mapping)
        
        place_order = ['alveolar', 'palatal']
        phoneme_order = ['ts', 'tsʰ', 'tɕ', 'tɕʰ']
        
        stats['Place'] = pd.Categorical(stats['Place'], categories=place_order, ordered=True)
        stats['Phoneme'] = pd.Categorical(stats['Phoneme'], categories=phoneme_order, ordered=True)
        stats = stats.sort_values(['Place', 'Phoneme'])
        
        plt.figure(figsize=(12, 8))
        colors = {'voiceless': '#1f77b4', 'voiceless aspirated': '#ff7f0e'}
        bars = []
        labels = []
        
        for idx, row in stats.iterrows():
            color = colors.get(row['Voicing'], '#999999')
            bar = plt.bar(idx, row['Mean'], color=color, edgecolor='black', linewidth=1)
            bars.append(bar[0])
            labels.append(row['Phoneme'])
            
            # error bar
            if not pd.isna(row['SD']) and row['N'] > 1:  # only when N > 1
                plt.errorbar(idx, row['Mean'], yerr=row['SD'], 
                            color='black', capsize=5, capthick=1.5, linewidth=1.5)
            
            plt.text(idx, row['Mean'] + (2 if row['Mean'] > 0 else -10), 
                    f"{row['Mean']:.1f}", ha='center', va='bottom' if row['Mean'] > 0 else 'top', fontsize=18)
        
        plt.xticks(range(len(stats)), labels, fontsize=18)
        
        prev_place = None
        start_idx = 0
        for idx, place in enumerate(stats['Place']):
            if place != prev_place:
                if prev_place is not None:
                    plt.axvline(x=idx-0.5, color='gray', linestyle='--', alpha=0.5)
                    plt.text((start_idx + idx - 1) / 2, plt.ylim()[1] * 1.01, 
                            prev_place.title(), ha='center', fontsize=18, fontweight='bold')
                start_idx = idx
                prev_place = place
        plt.text((start_idx + len(stats) - 1) / 2, plt.ylim()[1] * 1.01, 
                prev_place.title(), ha='center', fontsize=18, fontweight='bold')
        
        plt.ylabel("Mean VOT (ms)", fontsize=18)
        plt.xlabel("Phoneme", fontsize=18)
        plt.grid(axis='y', alpha=0.3, linestyle='--')
        plt.axhline(y=0, color='black', linewidth=0.8)

        legend_elements = [
            Patch(facecolor=colors['voiceless'], edgecolor='black', label='Voiceless Unaspirated'),
            Patch(facecolor=colors['voiceless aspirated'], edgecolor='black', label='Voiceless Aspirated')
        ]
        plt.legend(handles=legend_elements, fontsize=18)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Affricates bar plot saved to: {save_path}")
        plt.show()

if __name__ == "__main__":
    processor = TextGridProcessor("./data/vot/")
    stats = processor.calculate_statistics()
    stats.to_csv("./data/vot/stat.csv", index=False, encoding='utf-8')
    print("Statistics saved to: stat.csv")
    print(stats)
    processor.plot_vot_bar(save_path="pics/plosives_vot.png")
    processor.plot_affricates_bar(save_path="pics/affricates_vot.png")