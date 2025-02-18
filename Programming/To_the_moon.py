import krpc
import time
import math


control_data = krpc.connect(name='To_the_moon')
sc = control_data.space_center
vessel = control_data.space_center.active_vessel
ap = vessel.auto_pilot
control = vessel.control
ut = control_data.add_stream(getattr, control_data.space_center, 'ut')
control.antennas = True  # Раскрыть комуникационную антену


# Рассчёт нужного положения луны для запуска транзитного манёвра
# По Гомановской траектории
destSM = sc.bodies["Mun"].orbit.semi_major_axis  # Большая полуось Муны
hohmannSM = destSM / 2
Needed_Phase = 2 * math.pi * (1 / (2 * (destSM ** 3 / hohmannSM ** 3) ** (1 / 2)))
Optimal_Phase_Angle = 180 - Needed_Phase * 180 / math.pi + 19  # В градусах, муна перед кораблём
print('Оптимальная угол выхода:', Optimal_Phase_Angle)


# Расчёт текущего положения Муны Переменные
Phase_Angle = 9999
ap.engage()
ap.reference_frame = vessel.orbital_reference_frame
ap.target_direction = (0.0, 1.0, 0.0)  # Направление по движению
Angle_Dec = False  # Муна перед кораблём. то есть угол уменьшается
Prev_Phase = 0


# Непосредственно подсчёт
while abs(Phase_Angle - Optimal_Phase_Angle) > 1 or not Angle_Dec:
    Mun_R = sc.bodies["Mun"].orbit.radius
    Vessel_R = vessel.orbit.radius
    time.sleep(1)
    Mun_Pos = sc.bodies["Mun"].orbit.position_at(sc.ut, sc.bodies["Mun"].reference_frame)
    Vessel_Pos = vessel.orbit.position_at(sc.ut, sc.bodies["Mun"].reference_frame)
    Distance = ((Mun_Pos[0] - Vessel_Pos[0]) ** 2 + (Mun_Pos[1] - Vessel_Pos[1]) ** 2 + (Mun_Pos[2] - Vessel_Pos[2]) ** 2) ** (1 / 2)
    try:
        Phase_Angle = math.acos((Mun_R ** 2 + Vessel_R ** 2 - Distance ** 2) / (2 * Mun_R * Vessel_R))
    except:
        print("Невозможно рассчитать, подождите")
        continue
    Phase_Angle = Phase_Angle * 180 / math.pi
    if Prev_Phase - Phase_Angle > 0:
        Angle_Dec = True
        if abs(Phase_Angle - Optimal_Phase_Angle) > 30:
            sc.rails_warp_factor = 2
        elif abs(Phase_Angle - Optimal_Phase_Angle) > 10:
            sc.rails_warp_factor = 1
        else:
            sc.rails_warp_factor = 0
    else:
        Angle_Dec = False
        sc.rails_warp_factor = 3
    Prev_Phase = Phase_Angle
    print("Текущая фаза:", Phase_Angle)


# используется vis-viva
G_Kerbin = vessel.orbit.body.gravitational_parameter
R = vessel.orbit.radius
a1 = vessel.orbit.semi_major_axis
a2 = (sc.bodies["Mun"].orbit.radius + vessel.orbit.radius) / 2
v1 = math.sqrt(G_Kerbin * ((2.0 / R)-(1.0 / a1)))
v2 = math.sqrt(G_Kerbin * ((2.0 / R)-(1.0 / a2)))
delta_v = v2 - v1
Actual_Delta_V = 0
vessel.control.throttle = 1.0
ap.target_direction = (0.0, 1.0, 0.0)


# Манёвр (погрешность меньше 2 процентов) в среднем из десяти тестов
while (delta_v > Actual_Delta_V):
    R = vessel.orbit.radius
    a1 = vessel.orbit.semi_major_axis
    Actual_Delta_V = (G_Kerbin * ((2/R) - (1/a1))) ** (1/2) - v1
    print("Текущая delta_v:", Actual_Delta_V, "из требуемой", delta_v)

vessel.control.throttle = 0
vessel.auto_pilot.disengage()
