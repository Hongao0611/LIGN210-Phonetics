import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Ellipse
import matplotlib.transforms as transforms

class TextGridProcessor:
    def __init__(self, directory_path, output_path=None):
        """
        初始化TextGrid处理器
        
        Args:
            directory_path (str): 包含TextGrid文件的目录路径
        """
        self.directory_path = directory_path
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
        pattern = re.compile(r'^\d+-[a-zA-Z_]+\.TextGrid$', re.IGNORECASE)
        textgrid_files = []
        for file in os.listdir(self.directory_path):
            if pattern.match(file):
                textgrid_files.append(os.path.join(self.directory_path, file))
        return textgrid_files
    
    def parse_textgrid_file(self, file_path):
        """
        解析单个TextGrid文件，提取vowel tier的信息。
        格式："<vowel> F1=<F1 freqency> F2=<F2 frequency>"
        
        Args:
            file_path (str): TextGrid文件路径
            
        Returns:
            list: 包含vowel信息的字典列表，如[{vowel:o, F1:569, F2:1028},{vowel:i, F1:468, F2: 798}]
        """
        intervals_data = []
        filename = os.path.basename(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except Exception as e:
            try:
                with open(file_path, 'r', encoding='utf-16') as file:
                    content = file.read()
            except Exception as e2:
                print(f"e1: {e}\ne2: {e2}")
        # 改进的正则表达式，更好地处理特殊字符和格式变化
        interval_pattern = re.compile(
            r'intervals\s*\[\d+\]:\s*xmin\s*=\s*([\d.]+)\s*xmax\s*=\s*([\d.]+)\s*text\s*=\s*"([^"]*)"',
            re.IGNORECASE | re.DOTALL
        )
        
        matches = interval_pattern.findall(content)
        interval_sequence = 0
        
        for xmin, xmax, text in matches:
            interval_sequence += 1
            
            # 处理文本内容，去除引号并清理
            # text = text.strip().strip('"')
            
            # 只处理有内容的interval
            if text and text.strip():
                # 改进的解析逻辑：使用正则表达式匹配F1和F2模式
                # 匹配格式：<任意字符> F1=<数字> F2=<数字>
                pattern = re.compile(
                    r'^(.+?)\s+F1=(\d+)\s+F2=(\d+)$',
                    re.IGNORECASE
                )
                
                match = pattern.match(text)
                
                if match:
                    # 成功匹配F1/F2格式
                    vowel = match.group(1).strip()
                    try:
                        f1 = int(match.group(2))
                        f2 = int(match.group(3))
                    except (ValueError, TypeError):
                        f1 = None
                        f2 = None
                    
                    intervals_data.append({
                        'filename': filename,
                        'interval_sequence': interval_sequence,
                        'xmin': float(xmin),
                        'xmax': float(xmax),
                        'text': text,
                        'vowel': vowel,
                        'F1': f1,
                        'F2': f2,
                        'duration': float(xmax) - float(xmin)
                    })
                else:
                    # 没有匹配F1/F2格式，但有文本内容
                    # 检查是否可能是只有元音标注的情况
                    if len(text) <= 5:  # 假设元音标注不会太长
                        intervals_data.append({
                            'filename': filename,
                            'interval_sequence': interval_sequence,
                            'xmin': float(xmin),
                            'xmax': float(xmax),
                            'text': text,
                            'vowel': text,
                            'F1': None,
                            'F2': None,
                            'duration': float(xmax) - float(xmin)
                        })
                    else:
                        # 其他格式的文本内容
                        intervals_data.append({
                            'filename': filename,
                            'interval_sequence': interval_sequence,
                            'xmin': float(xmin),
                            'xmax': float(xmax),
                            'text': text,
                            'vowel': None,
                            'F1': None,
                            'F2': None,
                            'duration': float(xmax) - float(xmin)
                        })
            else:
                # 空interval
                intervals_data.append({
                    'filename': filename,
                    'interval_sequence': interval_sequence,
                    'xmin': float(xmin),
                    'xmax': float(xmax),
                    'text': "",
                    'vowel': None,
                    'F1': None,
                    'F2': None,
                    'duration': float(xmax) - float(xmin)
                })
        
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
            print(f"处理文件: {os.path.basename(file_path)}, 提取 {len(intervals)} 个intervals")
        print(f"处理完成! 总共提取了 {total_intervals} 个intervals")
        # 创建DataFrame
        df = pd.DataFrame(data)
        return df
    
    def save_to_csv(self):
        """
        将处理结果保存为CSV文件
        
        Returns:
            str: 保存的文件路径
        """
        if self.df.empty:
            print("没有数据可保存，请先调用 process_directory() 方法")
            return None
        self.df.to_csv(self.output_path, index=False, encoding='utf-8')
        print(f"数据已保存到: {self.output_path}")
        return self.output_path
    
    def transform_by_label(self):
        """
        按照vowel列变换，每一行为一种vowel的F1、F2列汇总值。
        Returns:
            df: cols 'vowel', 'count', 'F1_max', 'F1_min', 'F1_mean', 'F1_sd', 'F2_max', 'F2_min', 'F2_mean', 'F2_sd'
        """
        if self.df.empty or 'vowel' not in self.df.columns:
            print("数据为空或没有vowel列")
            return pd.DataFrame()
        
        # 过滤掉vowel为空的数据
        vowel_data = self.df[self.df['vowel'].notna()].copy()
        
        if vowel_data.empty:
            print("没有有效的vowel数据")
            return pd.DataFrame()
        
        # 按vowel分组计算统计量
        grouped = vowel_data.groupby('vowel').agg({
            'F1': ['count', 'max', 'min', 'mean', 'std'],
            'F2': ['max', 'min', 'mean', 'std']
        }).round(2)
        
        # 扁平化列名
        grouped.columns = [
            'count', 'F1_max', 'F1_min', 'F1_mean', 'F1_sd',
            'F2_max', 'F2_min', 'F2_mean', 'F2_sd'
        ]
        
        # 重置索引
        result_df = grouped.reset_index()
        
        print("Vowel统计汇总:")
        print(result_df)
        return result_df

    def plot_vowel_space(self, save_path=None, figsize=(14, 12)):
        """
        声学元音空间图
        
        Args:
            save_path (str, optional): 图片保存路径
            figsize (tuple): 图片大小
        """
        if self.df.empty or 'vowel' not in self.df.columns:
            print("没有数据可绘制")
            return
        
        # 过滤有效数据
        plot_data = self.df[
            (self.df['vowel'].notna()) & 
            (self.df['F1'].notna()) & 
            (self.df['F2'].notna())
        ].copy()
        
        if plot_data.empty:
            print("没有有效的元音数据可绘制")
            return
        
        # 创建图形和子图
        fig = plt.figure(figsize=figsize)
        gs = fig.add_gridspec(2, 2, width_ratios=[3, 1], height_ratios=[3, 1])
        
        # 主图：声学元音空间
        ax_main = fig.add_subplot(gs[0, 0])
        
        # 获取元音统计信息
        vowel_stats = self.transform_by_label()
        
        # 在主图上绘制
        vowels = sorted(plot_data['vowel'].unique())
        colors = plt.cm.viridis(np.linspace(0, 1, len(vowels)))
        
        # 为每个元音绘制
        for i, vowel in enumerate(vowels):
            vowel_data = plot_data[plot_data['vowel'] == vowel]
            stats = vowel_stats[vowel_stats['vowel'] == vowel].iloc[0]
            
            # 计算均值和标准差
            mean_f1 = stats['F1_mean']
            mean_f2 = stats['F2_mean']
            std_f1 = stats['F1_sd']
            std_f2 = stats['F2_sd']
            
            # 绘制散点（大小基于数据点数量）
            point_size = min(100, 20 + len(vowel_data) * 2)
            scatter = ax_main.scatter(vowel_data['F1'], vowel_data['F2'], 
                                    c=[colors[i]], label=f"{vowel} (n={len(vowel_data)})", 
                                    s=point_size, alpha=0.7, edgecolors='white', linewidth=1)
            
            # 绘制1SD和2SD椭圆
            for scale, linestyle, alpha in [(1, '--', 0.5), (2, ':', 0.3)]:
                ellipse = Ellipse(xy=(mean_f1, mean_f2), 
                                width=std_f1 * scale * 2, 
                                height=std_f2 * scale * 2,
                                edgecolor=colors[i], 
                                facecolor='none', 
                                linestyle=linestyle, 
                                linewidth=1.5,
                                alpha=alpha)
                ax_main.add_patch(ellipse)
            
            # 在均值位置添加标签
            ax_main.annotate(vowel, (mean_f1, mean_f2), 
                           xytext=(10, 10), textcoords='offset points',
                           fontsize=12, fontweight='bold',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.9),
                           arrowprops=dict(arrowstyle='->', color=colors[i], alpha=0.7))
        
        # 设置主图属性
        ax_main.set_xlabel('F1 (Hz)', fontsize=12, fontweight='bold')
        ax_main.set_ylabel('F2 (Hz)', fontsize=12, fontweight='bold')
        # ax_main.set_title('Enhanced Acoustic Vowel Space', fontsize=14, fontweight='bold')
        ax_main.grid(True, alpha=0.3)
        ax_main.xaxis.tick_top()
        ax_main.yaxis.tick_right()
        ax_main.xaxis.set_label_position('top')
        ax_main.yaxis.set_label_position('right')
        ax_main.invert_xaxis()
        ax_main.invert_yaxis()
        ax_main.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"增强图形已保存到: {save_path}")
        
        return fig, ax_main


# 使用示例
if __name__ == "__main__":
    # 使用方法
    processor = TextGridProcessor("./data/wk3/")
    
    # 如果数据已处理，可以调用绘图方法
    if not processor.df.empty:
        # 生成统计汇总
        summary = processor.transform_by_label()
        # 绘制声学元音空间图
        processor.plot_vowel_space(save_path="./data/wk3/vowel_space.png")