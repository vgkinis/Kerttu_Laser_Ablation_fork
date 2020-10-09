import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


df_fast_room = pd.read_csv('run_test_2020-09-16 10:03:33.235213+02:00.csv', names = ['datetime', 'epoch_t', 'pos'])
df_slow_room = pd.read_csv('run_test_2020-09-14 18:38:25.378193+02:00.csv', names = ['datetime', 'epoch_t', 'pos'])

df2_fast_room = pd.read_csv('run_test_2020-09-18 10:54:47.531724+02:00.csv', names = ['datetime', 'epoch_t', 'pos'])
df2_slow_room = pd.read_csv('run_test_2020-09-18 12:15:41.553016+02:00.csv', names = ['datetime', 'epoch_t', 'pos'])

df_fast_cold = pd.read_csv('run_test_2020-09-16 14:28:01.953228+02:00.csv', names = ['datetime', 'epoch_t', 'pos'])
df_slow_cold = pd.read_csv('run_test_2020-09-16 13:01:21.555372+02:00.csv', names = ['datetime', 'epoch_t', 'pos'])


plt.scatter(df_fast_room['epoch_t'],df_fast_room['pos'], color = "green", label = "14.28 mm/s at room temp", marker = "+")
plt.plot(df_fast_room['epoch_t'],df_fast_room['pos'], color = "green", marker = "+")

plt.scatter(df_slow_room['epoch_t'],df_slow_room['pos'], color = "orange", label = "1 mm/s at room temp", marker = "+")
plt.plot(df_slow_room['epoch_t'],df_slow_room['pos'], color = "orange", marker = "+")

plt.scatter(df2_fast_room['epoch_t'],df2_fast_room['pos'], color = "gray", label = "14.28 mm/s at room temp", marker = "+")
plt.plot(df2_fast_room['epoch_t'],df2_fast_room['pos'], color = "gray", marker = "+")

plt.scatter(df2_slow_room['epoch_t'],df2_slow_room['pos'], color = "yellow", label = "1 mm/s at room temp", marker = "+")
plt.plot(df2_slow_room['epoch_t'],df2_slow_room['pos'], color = "yellow", marker = "+")

plt.scatter(df_slow_cold['epoch_t'],df_slow_cold['pos'], color = "blue", label = "1 mm/s in the freezer", marker = "+")
plt.plot(df_slow_cold['epoch_t'],df_slow_cold['pos'], color = "blue", marker = "+")

plt.scatter(df_fast_cold['epoch_t'],df_fast_cold['pos'], color = "purple", label = "2.52 mm/s in the freezer", marker = "+")
plt.plot(df_fast_cold['epoch_t'],df_fast_cold['pos'], color = "purple", marker = "+")

plt.title("")
plt.xlabel("epoch time")
plt.xticks(np.arange(min(df_slow_room['epoch_t']), max(df_slow_room['epoch_t'])+1, 5))
plt.ylabel("position", rotation = 0)
plt.legend()
plt.show()
