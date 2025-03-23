import matplotlib.pyplot as plt
import numpy as np
import json

plt.rcParams['font.family'] = 'Times New Roman'

def generate_data():
    with open("Func.json", "r") as fr:
        vul_threshols = json.load(fr)
    F1f = np.array([vul_threshols["1"]["F1f"], vul_threshols["2"]["F1f"],vul_threshols["3"]["F1f"],vul_threshols["4"]["F1f"],vul_threshols["5"]["F1f"]])
    F1s = np.array([vul_threshols["1"]["F1s"], vul_threshols["2"]["F1s"],vul_threshols["3"]["F1s"],vul_threshols["4"]["F1s"],vul_threshols["5"]["F1s"]])
   
    return F1f, F1s

thresholds = np.arange(1, 6, 1)
fig, ax = plt.subplots(figsize=(5, 5))

F1f, F1s = generate_data()
max_f1_index = np.argmax(F1f)
max_f1 = F1f[max_f1_index]
max_f1_threshold = thresholds[max_f1_index]
ax.plot(thresholds, F1f, label='F1f', marker='s', linewidth=2, color='#8ECFC9')
ax.plot(thresholds, F1s, label='F1s', marker='^', linewidth=2, color='#FA7F6F')

ax.set_xlabel('TopF')
ax.legend(loc='lower left')
ax.grid(True)
ax.set_xticks(np.arange(1, 6, 1))
ax.set_ylim(0, 1) 

plt.tight_layout()
pdf_path = 'TopF.pdf'
plt.savefig(pdf_path)

plt.show()