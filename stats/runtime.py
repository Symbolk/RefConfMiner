# library & dataset
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

# df = sns.load_dataset('runtimes')
csv_data = pd.read_csv("runtimes.csv", delimiter=';')
# df = pd.concat([row[row['runtime'] < 5000] for row in csv_data])
# filter the extreme values to inspect the major distribution
df = csv_data[(csv_data['runtime']) < 10000]

intelli = df[(df['merge_tool'] == "IntelliMerge")]
jfst = df[(df['merge_tool'] == "JFSTMerge")]
print('Average running time:')
print('IntelliMerge\t' + str(intelli['runtime'].mean()) + 'ms')
print('jFSTMerge\t' + str(jfst['runtime'].mean()) + 'ms')

print('Median running time:')
print('IntelliMerge\t' + str(intelli['runtime'].median()) + 'ms')
print('jFSTMerge\t' + str(jfst['runtime'].median()) + 'ms')

plt.figure(figsize=(16, 5))
# Just switch x and y
# sns.violinplot(y="repo_name", x="runtime", hue="merge_tool", data=df, palette="Set2", split=True, scale="count", inner="box", scale_hue=False, bw=.2)
sns.violinplot(y=df["merge_tool"], x=df["runtime"], cut=0, inner="box")
# sns.violinplot(y=df["merge_tool"], x=df["runtime"], cut=2, inner="box")
# sns.boxplot("runtime", "merge_tool", data=df)
# sns.stripplot("runtime", "merge_tool", data=df, jitter=True)
# sns.violinplot(x="merge_tool", y="runtime", data=df)
plt.show()
# plt.savefig('runtimes.png')
