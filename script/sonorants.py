# read .txt file as TSV
import pandas as pd
df = pd.read_csv('data/sonorants/output.txt',sep='\t')
# filter out NA
df_filtered = df[df['soe'].notna()]
print(f"df rows:{len(df)}")
print(f"df_filtered rows:{len(df_filtered)}")
df_filtered.head()
# make IPA and group columns
print(df_filtered.columns.tolist())
df_filtered['IPA']=df_filtered['Label']
df_filtered['group_glottalization']=df_filtered['Label'].apply(lambda x: 'glottalization' if 'ʔ' in x else 'no')
df_filtered['group_POA']=df_filtered['IPA'].apply(lambda x: x.replace("ʔ",""))
df_filtered['duration']=df_filtered['seg_End'] - df_filtered['seg_Start']
df_clean = df_filtered[['Filename','duration','HNR05','soe','IPA','group_glottalization','group_POA']]
df_clean.head()
# descriptive statistics
with pd.ExcelWriter('sonorants.xlsx') as writer:    
    # group by POA
    numeric_stats_poa = df_clean.groupby(['group_POA']).agg({
        'duration': ['mean', 'std', 'min', 'max'],
        'HNR05': ['mean', 'std', 'min', 'max'],
        'soe': ['mean', 'std', 'min', 'max']
    }).round(1)
    numeric_stats_poa.to_excel(writer, sheet_name='By_POA')
    # group by IPA
    numeric_stats_ipa = df_clean.groupby(['IPA']).agg({
        'duration': ['mean', 'std', 'min', 'max'],
        'HNR05': ['mean', 'std', 'min', 'max'],
        'soe': ['mean', 'std', 'min', 'max']
    }).round(1)
    numeric_stats_ipa.to_excel(writer, sheet_name='By_IPA')
print("Saved to: sonorants.xlsx")