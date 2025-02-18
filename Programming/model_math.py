import os
import numpy as np


# =============================================================================
# Константы
# =============================================================================

# Параметры моделирования
TIME_STEP = 0.02       # [с] шаг времени для каждого обновления симуляции
COUNT_SKIP = 50        # интервал записи данных
# Физические константы
G = 6.67e-11           # [м^3/(кг*с^2)] гравитационная постоянная
P0 = 101325            # [Па] атмосферное давление на уровне моря
M_AIR = 0.02898        # [кг/моль] молярная масса воздуха
R_UNIVERSAL = 8.314    # [Дж/(моль*K)] универсальная газовая постоянная
R_SPECIFIC = 287.05    # [Дж/(кг*K)] удельная газовая постоянная для сухого воздуха
T0 = 288.2             # [K] опорная температура
# Параметры Земли (упрощённые/масштабированные)
EARTH_MASS = 5.29e22   # [кг] (масштабированное значение)
EARTH_RADIUS = 600000  # [м] радиус Земли
EARTH_ANG_VEL = 2.91e-4  # [рад/с] угловая скорость Земли
# Параметры первой ступени ракеты "Молния‑М"
DRY_MASS_FIRST_STAGE = 14800      # [кг] сухая масса первой ступени (примерное значение)
FUEL_MASS_FIRST_STAGE = 160000      # [кг] масса топлива первой ступени (примерное значение)
Q_FIRST_STAGE = 336         # [кг/с] номинальная скорость расхода топлива первой ступени
F0_FIRST_STAGE = 3252000         # [Н] тяга на уровне моря первой ступени
F1_FIRST_STAGE = 4000000        # [Н] тяга в вакууме первой ступени
I0_FIRST_STAGE = 313                    # [с] вакуумный удельный импульс первой ступени
I1_FIRST_STAGE = 256                    # [с] удельный импульс на уровне моря первой ступени
# Параметры второй ступени (маршевой двигатель) ракеты "Молния‑М"
DRY_MASS_SECOND_STAGE = 6500            # [кг] сухая масса второй ступени
FUEL_MASS_SECOND_STAGE = 90100   # [кг] масса топлива второй ступени (примерное значение)
Q_SECOND_STAGE = 85    # [кг/с] номинальная скорость расхода топлива второй ступени
F0_SECOND_STAGE = 941000            # [Н] тяга второй ступени (работает в вакууме)
F1_SECOND_STAGE = 745000            # [Н] тяга второй ступени (без атмосферных изменений)
I0_SECOND_STAGE = 309                   # [с] удельный импульс второй ступени
I1_SECOND_STAGE = 243                   # [с] (не используется, так как двигатель работает в вакууме)
# Полезная нагрузка: модуль "Луна‑10" (примерное значение)
OTHER_MASS = 35183
# [кг] масса полезной нагрузки (Луна‑10)
# Аэродинамические свойства (приблизительно)
C_D = 0.115                           # коэффициент сопротивления
A_EFF = 1.77                          # [м²] эффективная площадь поперечного сечения


# =============================================================================
# Ракета (Математическая модель)
# =============================================================================

class Rocket:
    """
    Представляет состояние и физику летательного аппарата.
    В этой модели:
      - Стадия 0 — на борту обе ступени: двигатели первой ступени работают до 118 с
        и двигатели второй ступени – до 287 с.
      - Стадия 1 — отсоединена первая ступень (остается вторая ступень с полезной нагрузкой).
      - Стадия 2 — отсоединена вторая ступень (остается только полезная нагрузка).
    Полезная нагрузка "Луна‑10" добавляется как OTHER_MASS.
    """
    # Начальные условия: расположена на поверхности Земли с начальной касательной скоростью
    time = 0.0
    position = [ EARTH_RADIUS, 0, 0]
    velocity = [0, 0,  EARTH_ANG_VEL *  EARTH_RADIUS]
    
    # Фиксированные управляющие установки (для упрощения)
    throttle = 1.0
    steering = 90.0  # базовое значение для расчёта направления тяги
    
    # Стадия: 0 — обе ступени, 1 — первая ступень отсоединена, 2 — вторая ступень отсоединена
    stage = 0
    fuel_first_stage =  FUEL_MASS_FIRST_STAGE
    fuel_second_stage =  FUEL_MASS_SECOND_STAGE

     
    def altitude():
        """Возвращает текущую высоту над поверхностью Земли [м]."""
        return  length(Rocket.position) -  EARTH_RADIUS

     
    def gravity():
        """Возвращает ускорение свободного падения на текущей высоте [м/с²]."""
        alt = Rocket.altitude()
        return  G *  EARTH_MASS / ( EARTH_RADIUS + alt)**2

     
    def temperature():
        """Возвращает атмосферную температуру [K] по кусочно-линейной модели."""
        h = Rocket.altitude()
        if h <= 11000:
            return  T0 - 6.5 * h / 1000
        elif h <= 20000:
            return  T0 - 71.5
        elif h <= 50000:
            return  T0 - 71.5 + 54 * (h - 20000) / 30000
        elif h <= 80000:
            return  T0 - 17.5 - 72.1 * (h - 50000) / 30000
        elif h <= 100000:
            return  T0 - 89.6
        return 1000

     
    def pressure_at_altitude():
        """
        Возвращает атмосферное давление [Па] на текущей высоте.
        (Экспоненциальное затухание используется до 100 км.)
        """
        h = Rocket.altitude()
        if h <= 100000:
            return  P0 * np.exp(- M_AIR * Rocket.gravity() * h /
                                         ( R_UNIVERSAL * Rocket.temperature()))
        return 0

     
    def density():
        """Возвращает плотность воздуха [кг/м³] на текущей высоте."""
        return Rocket.pressure_at_altitude() / ( R_SPECIFIC * Rocket.temperature())

     
    def orbital_velocity():
        """
        Возвращает вектор орбитальной скорости [м/с] в текущем положении,
        предполагая круговое движение из-за вращения Земли.
        """
        angle =  find_angle(Rocket.position)
        r =  length(Rocket.position)
        return [-np.cos(angle) *  EARTH_ANG_VEL * r,
                0,
                np.sin(angle) *  EARTH_ANG_VEL * r]

     
    def relative_speed():
        """
        Возвращает скорость [м/с] ракеты относительно локальной орбитальной скорости.
        """
        orb_vel = Rocket.orbital_velocity()
        rel_vel = [Rocket.velocity[i] - orb_vel[i] for i in range(3)]
        return  length(rel_vel)

     
    def total_mass():
        """
        Вычисляет общую массу [кг] аппарата.
          - При стадии 0 включает: топливо первой ступени, топливо второй ступени,
            сухие массы обеих ступеней и полезную нагрузку.
          - При стадии 1 масса первой ступени отсоединена; остаётся топливо второй ступени,
            сухая масса второй ступени и полезная нагрузка.
          - При стадии 2 остаётся только полезная нагрузка.
        """
        if Rocket.stage == 0:
            return (Rocket.fuel_first_stage + Rocket.fuel_second_stage +
                     DRY_MASS_FIRST_STAGE +  DRY_MASS_SECOND_STAGE +
                     OTHER_MASS)
        elif Rocket.stage == 1:
            return (Rocket.fuel_second_stage +
                     DRY_MASS_SECOND_STAGE +
                     OTHER_MASS)
        elif Rocket.stage == 2:
            return  OTHER_MASS
        return  OTHER_MASS

     
    def effective_I_first(pa):
        """
        Возвращает эффективный удельный импульс [с] для первой ступени,
        интерполируя между вакуумными и уровнем моря значениями.
        """
        return  I0_FIRST_STAGE - ( I0_FIRST_STAGE -  I1_FIRST_STAGE) * pa /  P0

     
    def effective_I_second(pa):
        """
        Возвращает эффективный удельный импульс [с] для второй ступени,
        интерполируя между вакуумными и уровнем моря значениями.
        """
        return  I0_SECOND_STAGE - ( I0_SECOND_STAGE -  I1_SECOND_STAGE) * pa /  P0


# =============================================================================
# Вспомогательные функции для работы с векторами
# =============================================================================

def length(v):
    """Возвращает Евклидову норму вектора v."""
    return np.sqrt(v[0]**2 + v[1]**2 + v[2]**2)

 
def angle(v1, v2):
    """
    Возвращает угол (в радианах) между векторами v1 и v2.
    """
    len1, len2 =  length(v1),  length(v2)
    if len1 and len2:
        dot = v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]
        cos_angle = np.round(dot/(len1*len2), 5)
        return np.arccos(cos_angle)
    return 0.0

 
def project_vector_onto_vector(v1, v2):
    """Возвращает проекцию вектора v1 на вектор v2."""
    dot = v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]
    denom = v2[0]**2 + v2[1]**2 + v2[2]**2
    return [v2[0]*dot/denom, v2[1]*dot/denom, v2[2]*dot/denom]

 
def project_vector_onto_plane(v, normal):
    """Возвращает проекцию вектора v на плоскость, перпендикулярную вектору normal."""
    len_v =  length(v)
    len_n =  length(normal)
    angle_val =  angle(v, normal)
    return [
        v[0] - normal[0] * len_v * np.cos(angle_val) / len_n,
        v[1] - normal[1] * len_v * np.cos(angle_val) / len_n,
        v[2] - normal[2] * len_v * np.cos(angle_val) / len_n
    ]

 
def rotate_vector(v, angle_deg):
    """
    Поворачивает вектор v в плоскости x-z на угол angle_deg (в градусах).
    """
    angle_rad = np.deg2rad(angle_deg)
    if v[2] < 0:
        alpha = np.arctan(v[0]/v[2]) - angle_rad + np.pi
    elif v[2] > 0:
        alpha = np.arctan(v[0]/v[2]) - angle_rad
    else:
        alpha = -angle_rad
    return [np.sin(alpha), 0, np.cos(alpha)]

 
def find_angle(v):
    """
    Возвращает угол вектора v относительно оси z (в плоскости x-z).
    """
    if v[2] < 0:
        return np.arctan(v[0]/v[2]) + np.pi
    elif v[2] > 0:
        return np.arctan(v[0]/v[2])
    else:
        return np.pi/2


def fixed_update():
    """
    Обновляет физику ракеты на каждом шаге симуляции.
    Учитывает работу двигателей:
      - Двигатели первой ступени работают до 118 с.
      - Двигатели второй ступени работают до 287 с.
    После 118 с происходит отсоединение первой ступени, а после 287 с – отсоединение второй ступени.
    """
    # Увеличиваем время симуляции
    Rocket.time +=  TIME_STEP
    # Отсоединение первой ступени после 118 с при высоте ≈48 км
    if Rocket.time >= 118 and Rocket.stage == 0:
        Rocket.stage = 1
        print(f"Отсоединение первой ступени в момент {Rocket.time:.2f} с, высота {Rocket.altitude():.2f} м")
    
    # Отсоединение второй ступени после 287 с при высоте ≈150 км
    if Rocket.time >= 287 and Rocket.stage == 1:
        print(f"Отсоединение второй ступени в момент {Rocket.time:.2f} с, высота {Rocket.altitude():.2f} м")
    
    old_velocity = Rocket.velocity.copy()
    
    # Получаем атмосферное давление
    pa = Rocket.pressure_at_altitude()
    
    # Расчёт отклонения (тангажа) от 0 до 70 градусов в период от 120 до 190 с
    if Rocket.time < 120:
        pitch_deviation = 0
    elif Rocket.time <= 190:
        pitch_deviation = ((Rocket.time - 120) / (190 - 120)) * 70
    else:
        pitch_deviation = 70
    
    # --- Тяга двигателей ---
    # Тяга первой ступени (активна до 118 с)
    thrust_first = 0
    consumption_first = 0
    if Rocket.time < 118 and Rocket.fuel_first_stage > 0:
        thrust_first =  F0_FIRST_STAGE - ( F0_FIRST_STAGE -  F1_FIRST_STAGE) * pa /  P0
        eff_I_first = Rocket.effective_I_first(pa)
        consumption_first =  Q_FIRST_STAGE *  I0_FIRST_STAGE / eff_I_first * Rocket.throttle *  TIME_STEP
    
    # Тяга второй ступени (активна до 287 с)
    thrust_second = 0
    consumption_second = 0
    if Rocket.time < 287 and Rocket.fuel_second_stage > 0:
        thrust_second =  F0_SECOND_STAGE - ( F0_SECOND_STAGE -  F1_SECOND_STAGE) * pa /  P0
        eff_I_second = Rocket.effective_I_second(pa)
        consumption_second =  Q_SECOND_STAGE *  I0_SECOND_STAGE / eff_I_second * Rocket.throttle *  TIME_STEP
    
    total_thrust = thrust_first + thrust_second
    acceleration = total_thrust / Rocket.total_mass()
    # Направление тяги: базовая установка (90 - steering) плюс поправка тангажа
    # При базовом значении Rocket.steering = 90, выражение (90-90)=0, т.е. первоначально отклонение отсутствует.
    thrust_direction =  rotate_vector(Rocket.position, (90 - Rocket.steering) + pitch_deviation)
    Rocket.velocity = [Rocket.velocity[i] + thrust_direction[i] * acceleration *  TIME_STEP for i in range(3)]
    
    # --- Гравитация ---
    pos_norm =  length(Rocket.position)
    gravity_vector = [Rocket.position[i] * Rocket.gravity() / pos_norm for i in range(3)]
    Rocket.velocity = [Rocket.velocity[i] - gravity_vector[i] *  TIME_STEP for i in range(3)]
    
    # --- Аэродинамическое сопротивление ---
    speed =  length(Rocket.velocity)
    if speed:
        drag_acc = (0.5 * Rocket.density() * speed**2 *  C_D *  A_EFF / Rocket.total_mass())
        Rocket.velocity = [Rocket.velocity[i] - (Rocket.velocity[i] * drag_acc *  TIME_STEP / speed) for i in range(3)]
    
    # --- Обработка столкновения с землёй ---
    if Rocket.altitude() <= 0:
        proj =  project_vector_onto_vector(Rocket.velocity, Rocket.position)
        if proj[0] != 0:
            Rocket.velocity =  project_vector_onto_plane(Rocket.velocity, Rocket.position)
    
    # --- Обновление положения (метод трапеций) ---
    Rocket.position = [Rocket.position[i] + (Rocket.velocity[i] + old_velocity[i]) *  TIME_STEP / 2 for i in range(3)]
    if Rocket.altitude() < 0:
        norm =  length(Rocket.position)
        Rocket.position = [Rocket.position[i] *  EARTH_RADIUS / norm for i in range(3)]
    
    # --- Расход топлива ---
    if Rocket.time < 118:
        Rocket.fuel_first_stage -= consumption_first
        if Rocket.fuel_first_stage < 0:
            Rocket.fuel_first_stage = 0
    if Rocket.time < 287:
        Rocket.fuel_second_stage -= consumption_second
        if Rocket.fuel_second_stage < 0:
            Rocket.fuel_second_stage = 0


# =============================================================================
# Основной цикл симуляции и запись данных
# =============================================================================

# Фиксированные управляющие установки для данной математической модели.
Rocket.throttle = 1.0
Rocket.steering = 90.0
# Создаём папку "data", если она не существует.
os.makedirs("data", exist_ok=True)
# Формируем заголовок для лог-файла: время, общая масса, высота, относительная скорость.
data_log = "time, mass, altitude, speed\n"
iteration_counter = 0
total_time = 287  # Общая длительность симуляции в секундах
total_iterations = int(total_time /  TIME_STEP)
for i in range(total_iterations):
    fixed_update()
    iteration_counter += 1
    # Записываем данные каждые COUNT_SKIP шагов
    if iteration_counter ==  COUNT_SKIP:
        log_line = (f"{Rocket.time:.2f}, {Rocket.total_mass():.2f}, "
                    f"{Rocket.altitude():.2f}, {Rocket.relative_speed():.2f}\n")
        data_log += log_line
        iteration_counter = 0
# Записываем лог в файл "data/MathModel_Stats.txt"
file_path = os.path.join("data", "MathModel_Stats.txt")
with open(file_path, "w", encoding="utf-8") as f:
    f.write(data_log)
print(f"Данные сохранены в {file_path}")