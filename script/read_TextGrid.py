import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the TSV file
df = pd.read_csv('data/wk4/mean_f0_results.tsv', sep='\t', encoding='utf-16')

# Define the tone categories we're interested in
tone_categories = ['H', 'M', 'L', 'HL', 'LH']

# Filter data for the specified tone categories
df_filtered = df[df['Segment label'].isin(tone_categories)]

# Extract F0 columns (F0_1 to F0_20)
f0_columns = [f'F0_{i}' for i in range(1, 21)]

# Convert F0 values to numeric, handling 'undefined' values
for col in f0_columns:
    df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')

# Create normalized duration (x-axis: 0 to 1)
normalized_time = np.linspace(0, 1, 20)

# Set up the plot
plt.figure(figsize=(12, 8))

# Define colors for each tone category
colors = {'H': 'red', 'M': 'blue', 'L': 'green', 'HL': 'purple', 'LH': 'orange'}

# Count samples per category
sample_counts = df_filtered['Segment label'].value_counts()

# Plot each tone category
for tone in tone_categories:
    tone_data = df_filtered[df_filtered['Segment label'] == tone]
    
    # Extract F0 values for this tone category
    f0_values = tone_data[f0_columns].values
    
    # Calculate mean and standard deviation across segments
    mean_f0 = np.nanmean(f0_values, axis=0)
    std_f0 = np.nanstd(f0_values, axis=0)
    
    # Get sample count for this tone
    count = sample_counts.get(tone, 0)
    
    # Plot the mean line with label including sample count
    plt.plot(normalized_time, mean_f0, 
             color=colors[tone], 
             linewidth=2, 
             label=f'{tone} (n={count})',
             marker='o', 
             markersize=4)
    
    # Add error bars (1 SD) as gray shaded area
    plt.fill_between(normalized_time, 
                     mean_f0 - std_f0, 
                     mean_f0 + std_f0, 
                     alpha=0.3, 
                     color='gray')

# Customize the plot with larger font sizes
plt.xlabel('Normalized Duration', fontsize=20)
plt.ylabel('Pitch (Hz)', fontsize=20)
plt.title('Mean F0 with Error Bars (±1 SD) for Tone Categories', fontsize=20, pad=20)
plt.legend(title='Tone Category', fontsize=18, title_fontsize=18)
plt.grid(True, alpha=0.3)

# Increase tick label sizes
plt.xticks(fontsize=18)
plt.yticks(fontsize=18)

# Set axis limits if needed
plt.ylim(bottom=120)

# Adjust layout and display
plt.tight_layout()
plt.show()

# Optional: Print some statistics
print("Number of segments per tone category:")
print(df_filtered['Segment label'].value_counts().sort_index())