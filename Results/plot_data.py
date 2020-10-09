import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


df_slow_room = pd.read_csv('run_test_2020-09-24 16:10:06.549038+02:00.csv', names = ['abs_pos', 'velocity', 'step_time'])
df_slow_cold = pd.read_csv('run_test_2020-09-25 12_12_24.066609+02_00.csv', names = ['abs_pos', 'velocity', 'step_time'])

plt.plot(df_slow_room['step_time'],df_slow_room['abs_pos'], color = "orange", label = "1 mm/s at room temp, stepper 1", marker = '+')
plt.plot(df_slow_cold['step_time'],df_slow_cold['abs_pos'], color = "blue", label = "1 mm/s in the freeer, stepper 1", marker = '+')


"""df_fast_room = pd.read_csv('run_test_2020-09-24 16:40:44.562283+02:00.csv', names = ['abs_pos', 'velocity', 'step_time'])
df_fast_cold = pd.read_csv('run_test_2020-09-25 10:30:41.219696+02:00.csv', names = ['abs_pos', 'velocity', 'step_time'])
df2_fast_cold = pd.read_csv('run_test_2020-09-25 11:05:05.487542+02:00.csv', names = ['abs_pos', 'velocity', 'step_time'])
df3_fast_cold = pd.read_csv('run_test_2020-09-25 13_15_34.119017+02_00.csv', names = ['abs_pos', 'velocity', 'step_time'])
df4_fast_cold = pd.read_csv('run_test_2020-09-25 14_18_32.054655+02_00.csv', names = ['abs_pos', 'velocity', 'step_time'])
df5_fast_cold = pd.read_csv('run_test_2020-09-25 15_38_16.038431+02_00.csv', names = ['abs_pos', 'velocity', 'step_time'])

plt.plot(df_fast_room['step_time'],df_fast_room['abs_pos'], color = "orange", label = "1 mm/s at room temp, stepper 1", marker = '+')
plt.plot(df_fast_cold['step_time'],df_fast_cold['abs_pos'], color = "blue", label = "1 mm/s in the freezer, stepper 1", marker = '+')
plt.plot(df2_fast_cold['step_time'],df2_fast_cold['abs_pos'], color = "purple", label = "1 mm/s in the freezer, stepper 1", marker = '+')
plt.plot(df3_fast_cold['step_time'],df3_fast_cold['abs_pos'], color = "green", label = "1 mm/s in the freezer, stepper 1", marker = '+')
plt.plot(df4_fast_cold['step_time'],df4_fast_cold['abs_pos'], color = "gray", label = "1 mm/s in the freezer, stepper 1", marker = '+')
plt.plot(df5_fast_cold['step_time'],df5_fast_cold['abs_pos'], color = "black", label = "1 mm/s in the freezer, stepper 2", marker = '+')"""


plt.title("")
plt.xlabel("step time")
#plt.xticks(np.arange(min(df_fast_room['step_time']), max(df_fast_room['step_time'])+1, 100))
plt.ylabel("position", rotation = 0)
plt.legend()
plt.show()
