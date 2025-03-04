import os
import numpy as np

# =============================================================================
# КОНСТАНТЫ И ПАРАМЕТРЫ (по документу)
# =============================================================================
TIME_STEP = 0.02
COUNT_SKIP = 50
G = 6.67e-11
P0 = 101325
M_AIR = 0.02898
R_UNIVERSAL = 8.314
R_SPECIFIC = 287.05
T0 = 288.15

# Параметры небесных тел
EARTH_MASS = 5.97e24
EARTH_RADIUS = 6.371e6
MOON_MASS = 7.34e22
MOON_RADIUS = 1.737e6

# Параметры ракеты
DRY_MASS_1 = 20000
FUEL_MASS_1 = 20000
F0_1 = 2.5e6
F1_1 = 2.0e6
I0_1 = 280

DRY_MASS_2 = 5000
FUEL_MASS_2 = 10000
F0_2 = 1e5
I0_2 = 310

PAYLOAD_MASS = 1500

# Аэродинамика
C_D = 0.12
A_EFF = 2.0

# Управление
ALPHA0 = np.deg2rad(90)
DELTA_ALPHA = np.deg2rad(0.5)
H_TRANSITION = 100000


# =============================================================================
# КЛАСС РАКЕТЫ
# =============================================================================
class Rocket:
    time = 0.0
    position = np.array([EARTH_RADIUS, 0.0, 0.0])
    velocity = np.array([0.0, 0.0, 0.0])
    stage = 0
    fuel_1 = FUEL_MASS_1
    fuel_2 = FUEL_MASS_2

    @classmethod
    def altitude(cls):
        return np.linalg.norm(cls.position) - EARTH_RADIUS

    @classmethod
    def gravity(cls):
        h = cls.altitude()
        if h < H_TRANSITION:
            return G * EARTH_MASS / (EARTH_RADIUS + h) ** 2
        return G * MOON_MASS / (MOON_RADIUS + h) ** 2

    @classmethod
    def temperature(cls, h):
        if h <= 11000:
            return T0 - 6.5 * h / 1000
        elif h <= 20000:
            return 216.65
        return 216.65

    @classmethod
    def pressure(cls, h):
        return P0 * np.exp(-M_AIR * cls.gravity() * h / (R_UNIVERSAL * cls.temperature(h)))

    @classmethod
    def density(cls, h):
        return cls.pressure(h) / (R_SPECIFIC * cls.temperature(h))

    @classmethod
    def total_mass(cls):
        if cls.stage == 0:
            return DRY_MASS_1 + DRY_MASS_2 + cls.fuel_1 + cls.fuel_2 + PAYLOAD_MASS
        elif cls.stage == 1:
            return DRY_MASS_2 + cls.fuel_2 + PAYLOAD_MASS
        return PAYLOAD_MASS

    @classmethod
    def current_angle(cls):
        return ALPHA0 + DELTA_ALPHA * cls.time


# =============================================================================
# МЕТОД РУНГЕ-КУТТЫ 4-го ПОРЯДКА
# =============================================================================
def runge_kutta_step(y, t, dt):
    def derivatives(y, t):
        pos = y[:3]
        vel = y[3:6]
        h = np.linalg.norm(pos) - EARTH_RADIUS
        mass = Rocket.total_mass()

        # Тяга
        if Rocket.stage == 0:
            F = F0_1 if h >= H_TRANSITION else F1_1
        else:
            F = F0_2

        # Направление тяги
        alpha = Rocket.current_angle()
        F_vec = np.array([
            F * np.sin(alpha),
            0.0,
            F * np.cos(alpha)
        ])

        # Гравитация
        pos_norm = np.linalg.norm(pos)
        g = -Rocket.gravity()
        g_vec = g * pos / pos_norm if pos_norm != 0 else np.zeros(3)

        # Аэродинамическое сопротивление
        v = np.linalg.norm(vel)
        drag_vec = np.zeros(3)
        if h < 100000 and v > 1e-3:
            rho = Rocket.density(h)
            F_drag = 0.5 * rho * v ** 2 * C_D * A_EFF
            drag_dir = vel / v
            drag_vec = -F_drag * drag_dir / mass

        # Суммарное ускорение
        acceleration = (F_vec / mass) + g_vec + drag_vec

        return np.concatenate([vel, acceleration])

    k1 = derivatives(y, t)
    k2 = derivatives(y + k1 * dt / 2, t + dt / 2)
    k3 = derivatives(y + k2 * dt / 2, t + dt / 2)
    k4 = derivatives(y + k3 * dt, t + dt)

    return y + (k1 + 2 * k2 + 2 * k3 + k4) * dt / 6


# =============================================================================
# ОСНОВНОЙ ЦИКЛ СИМУЛЯЦИИ
# =============================================================================
state = np.concatenate([Rocket.position, Rocket.velocity])
data_log = "time,altitude,speed\n"

for step in range(int(400 / TIME_STEP)):
    t = step * TIME_STEP
    state = runge_kutta_step(state, t, TIME_STEP)

    # Обновление состояния
    Rocket.position = state[:3]
    Rocket.velocity = state[3:6]
    Rocket.time = t

    # Отделение ступеней
    if Rocket.stage == 0 and Rocket.altitude() >= 48000:
        Rocket.stage = 1
        Rocket.fuel_1 = 0.0
        print(f"Отделение 1-й ступени: t={t:.1f}c, h={Rocket.altitude():.0f}м")

    # Запись данных
    if step % COUNT_SKIP == 0:
        data_log += f"{t:.2f},{Rocket.altitude():.1f},{np.linalg.norm(Rocket.velocity):.1f}\n"

# Сохранение результатов
os.makedirs("data", exist_ok=True)
with open("data/simulation_results.csv", "w") as f:
    f.write(data_log)
print("Симуляция успешно завершена. Результаты сохранены в data/simulation_results.csv")
