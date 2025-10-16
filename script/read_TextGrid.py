import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

class TextGridProcessor:
    def __init__(self, directory_path, output_path=None):
        """
        初始化TextGrid处理器
        
        Args:
            directory_path (str): 包含TextGrid文件的目录路径
        """
        self.directory_path = directory_path
        self.voiced_stops = ['b','d','g','dz','dʐ']
        self.voiceless_stops = ['pʰ','t','tʰ','tç','tçʰ','ts','tsʰ','k','kʰ']
        if output_path is None:
            self.output_path = os.path.join(self.directory_path, "textgrid_summary.csv")
        else:
            self.output_path = output_path
        if os.path.exists(self.output_path):
            print(f"数据存在，读取:{self.output_path}")
            self.df = pd.read_csv(self.output_path)
            if 'label' in self.df.columns:
                print(f"label列存在，开始统计...")
                transformed_df = self.transform_by_label()
                transformed_df.to_csv('transformed_summary.csv',index=False)
        else:
            print(f"数据不存在，调用TextGridProcessor.process_directory()...")
            self.df = self.process_directory()
            self.save_to_csv()
        
        if not self.df.empty:
            # 显示前几行数据
            print("\n数据预览:")
            print(self.df.head())
            # 统计信息
            print(f"\n数据统计:")
            print(f"文件数量: {self.df['filename'].nunique()}")
            print(f"总interval数量: {len(self.df)}")
            print(f"text字段非空的数量: {self.df['text'].notna().sum()}")
    
    def find_textgrid_files(self):
        """
        查找目录中所有符合命名规范的TextGrid文件
        
        Returns:
            list: 文件路径列表
        """
        pattern = re.compile(r'^\d+_[a-zA-Z_]+\.TextGrid$', re.IGNORECASE)
        textgrid_files = []
        for file in os.listdir(self.directory_path):
            if pattern.match(file):
                textgrid_files.append(os.path.join(self.directory_path, file))
        return textgrid_files
    
    def parse_textgrid_file(self, file_path):
        """
        解析单个TextGrid文件，提取VOT tier的interval信息
        
        Args:
            file_path (str): TextGrid文件路径
            
        Returns:
            list: 包含interval信息的字典列表
        """
        intervals_data = []
        filename = os.path.basename(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            # 查找VOT tier部分
            vot_pattern = r'name = "VOT".*?intervals: size = (\d+)(.*?)(?=item \[|\Z)'
            vot_match = re.search(vot_pattern, content, re.DOTALL)
            if not vot_match:
                print(f"警告: 在文件 {filename} 中未找到VOT tier")
                return intervals_data
            intervals_content = vot_match.group(2)
            # 提取所有interval
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
            print(f"成功解析文件 {filename}, 找到 {len(intervals_data)} 个intervals")
        except Exception as e:
            print(f"解析文件 {filename} 时出错: {str(e)}")
        return intervals_data
    
    def process_directory(self):
        """
        处理目录中的所有TextGrid文件
        
        Returns:
            pandas.DataFrame: 包含所有interval数据的DataFrame
        """
        print(f"开始处理目录: {self.directory_path}")
        # 查找所有TextGrid文件
        textgrid_files = self.find_textgrid_files()
        print(f"找到 {len(textgrid_files)} 个TextGrid文件")
        if not textgrid_files:
            print("未找到符合命名规范的TextGrid文件")
            return pd.DataFrame()
        # 处理每个文件
        total_intervals = 0
        data = []
        for file_path in textgrid_files:
            intervals = self.parse_textgrid_file(file_path)
            data.extend(intervals)
            total_intervals += len(intervals)
        print(f"处理完成! 总共提取了 {total_intervals} 个intervals")
        # 创建DataFrame
        df = pd.DataFrame(data, columns=['filename', 'interval_sequence', 'xmin', 'xmax', 'text'])
        return df
    
    def save_to_csv(self):
        """
        将处理结果保存为CSV文件
        
        Returns:
            str: 保存的文件路径
        """
        if not self.df:
            print("没有数据可保存，请先调用 process_directory() 方法")
            return None
        self.df.to_csv(self.output_path, index=False, encoding='utf-8')
        print(f"数据已保存到: {self.output_path}")
        return self.output_path
    
    def transform_by_label(self):
        """
        仅保留label不为空的数据，将结果按照label列变换，每一行为一种label的text列汇总值。
        Returns:
            df: cols 'label', 'count', 'max', 'min', 'mean', 'sd'
        """
        assert 'label' in self.df.columns, f"Label column not found. Open the .csv file and add labels before calling this function."
        # 过滤掉label为空的数据
        df_filtered = self.df[self.df['label'].notna()].copy()
        # 将text列转换为数值类型，无法转换的设为NaN
        df_filtered['text_numeric'] = pd.to_numeric(df_filtered['text'], errors='raise')
        # 按label分组计算统计指标
        result = df_filtered.groupby('label')['text_numeric'].agg([
            ('count', 'count'),      # 计数
            ('max', 'max'),          # 最大值
            ('min', 'min'),          # 最小值
            ('mean', 'mean'),        # 均值
            ('sd', 'std')            # 标准差
        ]).reset_index()
        # 保留两位小数
        numeric_columns = ['max', 'min', 'mean', 'sd']
        for col in numeric_columns:
            result[col] = result[col].round(2)
        # 重命名列以符合要求
        result = result.rename(columns={'label': 'label'})
        return result
    def plot_vot_violin(self, save_path=None, figsize=(15, 6)):
        """
        分别绘制浊辅音和清辅音的小提琴图，横坐标为具体音素
        
        Args:
            save_path (str, optional): 图片保存路径，如果为None则不保存
            figsize (tuple): 图片大小
        """
        # 检查是否有转换后的数据
        if not hasattr(self, 'transformed_df'):
            if 'label' in self.df.columns:
                self.transformed_df = self.transform_by_label()
            else:
                print("错误: 没有label列，无法绘制小提琴图")
                return
        # 准备数据
        voiced_data = []
        voiceless_data = []
        # 过滤出浊辅音的数据
        for phoneme in self.voiced_stops:
            phoneme_data = self.df[self.df['label'] == phoneme].copy()
            phoneme_data['text_numeric'] = pd.to_numeric(phoneme_data['text'], errors='coerce')
            phoneme_data = phoneme_data.dropna(subset=['text_numeric'])
            for _, row in phoneme_data.iterrows():
                voiced_data.append({
                    'phoneme': phoneme,
                    'VOT': row['text_numeric']
                })
        # 过滤出清辅音的数据
        for phoneme in self.voiceless_stops:
            phoneme_data = self.df[self.df['label'] == phoneme].copy()
            phoneme_data['text_numeric'] = pd.to_numeric(phoneme_data['text'], errors='coerce')
            phoneme_data = phoneme_data.dropna(subset=['text_numeric'])
            for _, row in phoneme_data.iterrows():
                voiceless_data.append({
                    'phoneme': phoneme,
                    'VOT': row['text_numeric']
                })
        voiced_df = pd.DataFrame(voiced_data)
        voiceless_df = pd.DataFrame(voiceless_data)
        if voiced_df.empty and voiceless_df.empty:
            print("错误: 没有找到符合条件的数据")
            return
        # 设置绘图风格
        plt.style.use('default')
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        # 绘制浊辅音小提琴图
        if not voiced_df.empty:
            sns.violinplot(data=voiced_df, x='phoneme', y='VOT', ax=ax1, palette='Blues')
            ax1.set_title('Voiced', fontsize=14, fontweight='bold')
            ax1.set_xlabel('segment', fontsize=12)
            ax1.set_ylabel('VOT (ms)', fontsize=12)
            # 在浊辅音图上添加数据点
            sns.stripplot(data=voiced_df, x='phoneme', y='VOT', ax=ax1, 
                         color='black', alpha=0.5, jitter=True, size=3)
        # 绘制清辅音小提琴图
        if not voiceless_df.empty:
            sns.violinplot(data=voiceless_df, x='phoneme', y='VOT', ax=ax2, palette='Reds')
            ax2.set_title('Voiceless', fontsize=14, fontweight='bold')
            ax2.set_xlabel('segment', fontsize=12)
            ax2.set_ylabel('VOT (ms)', fontsize=12)
            # 在清辅音图上添加数据点
            sns.stripplot(data=voiceless_df, x='phoneme', y='VOT', ax=ax2, 
                         color='black', alpha=0.5, jitter=True, size=3)
        # 调整布局
        plt.tight_layout()
        # 保存或显示图片
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"小提琴图已保存到: {save_path}")
        return fig, (ax1, ax2)

# 使用示例
if __name__ == "__main__":
    # 使用方法
    processor = TextGridProcessor("./data/wk2/")
    processor.plot_vot_violin(save_path="vot_violin_plot.png")