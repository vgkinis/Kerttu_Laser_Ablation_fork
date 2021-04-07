import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

stage = "s1200"


def plot_data(stage):
    plt.figure()
    f, (ax1, ax2) = plt.subplots(2, 1)

    files = os.listdir()
    files = list(filter(lambda x: stage in x, files))
    files = sorted(files, key=lambda x: int(x.split(stage + '.csv')[0].split("V")[1].replace("_","")))

    for filename in files:
        df = pd.read_csv(filename, names = ['pos', 'delay', 'time'])
        data_label = "V" + filename.split("V")[1].split("_")[0]
        ax1.scatter(df['time'],df['pos'], label = data_label, marker = "+")
        ax1.plot(df['time'],df['pos'], marker = "+")
        ax1.set_ylabel('position')

        ax2.scatter(df['time'],df['delay'], label = data_label, marker = "+")
        ax2.plot(df['time'],df['delay'], marker = "+")
        ax2.set_ylabel('speed (us)')

    plt.title("")
    plt.xlabel("time")
    plt.legend()
    plt.show()

plot_data(stage)
