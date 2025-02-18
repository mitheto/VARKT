import pandas as pd
import matplotlib.pyplot as plt

# Загрузка данных из первого файла
data1 = pd.read_csv(r'C:\Users\Данила\Downloads\math_stats.csv', delimiter=',')
time1 = data1['time']
altitude1 = data1['altitude']
speed1 = data1['speed']

# Загрузка данных из второго файла (замените путь на актуальный)
data2 = pd.read_csv(r'C:\Users\Данила\Desktop\telemetry.csv', delimiter=',')
time2 = data2['time']
altitude2 = data2['altitude']
speed2 = data2['speed']

# Создание графиков
plt.figure(figsize=(18, 6))

# График зависимости высоты от скорости
plt.subplot(1, 3, 1)
plt.plot(speed1, altitude1, label='Мат.модель', color='blue')
plt.plot(speed2, altitude2, label='Симуляция', color='cyan', linestyle='--')
plt.xlabel('Скорость (м/с)')
plt.ylabel('Высота (м)')
plt.title('Зависимость высоты от скорости')
plt.grid(True)
plt.legend()

# График зависимости времени от высоты
plt.subplot(1, 3, 2)
plt.plot(time1, altitude1, label='Мат.модель', color='green')
plt.plot(time2, altitude2, label='Симуляция', color='lime', linestyle='--')
plt.xlabel('Время (с)')
plt.ylabel('Высота (м)')
plt.title('Зависимость времени от высоты')
plt.grid(True)
plt.legend()

# График зависимости времени от скорости
plt.subplot(1, 3, 3)
plt.plot(time1, speed1, label='Мат.модель', color='red')
plt.plot(time2, speed2, label='Симуляция', color='orange', linestyle='--')
plt.xlabel('Время (с)')
plt.ylabel('Скорость (м/с)')
plt.title('Зависимость времени от скорости')
plt.grid(True)
plt.legend()

# Отображение графиков
plt.tight_layout()
plt.show()