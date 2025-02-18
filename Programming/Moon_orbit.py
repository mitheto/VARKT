import krpc
import time
import math


control_data = krpc.connect(name='To_the_moon')
sc = control_data.space_center
vessel = control_data.space_center.active_vessel
ap = vessel.auto_pilot
control = vessel.control
ut = control_data.add_stream(getattr, sc, 'ut')
sc.rails_warp_factor = 0


if 2 * vessel.orbit.radius > 1250000:
    control.sas = True
    print('Стабилизация активна. Режим против движения')
    control.sas_mode = sc.SASMode.retrograde
    sc.warp_to(ut() + vessel.orbit.time_to_periapsis - 10)


while 2 * vessel.orbit.radius > 1250000:
    R = vessel.orbit.radius
    G_Mun = vessel.orbit.body.gravitational_parameter
    a1 = vessel.orbit.semi_major_axis
    a2 = R
    v1 = math.sqrt(G_Mun * ((2.0 / R) - (1.0 / a1)))
    v2 = math.sqrt(G_Mun * ((2.0 / R) - (1.0 / a2)))
    delta_v = v1 - v2
    if delta_v < 0:
        break

    Actual_Delta_V = 0
    control.sas_mode = sc.SASMode.retrograde
    time.sleep(10)
    control.throttle = 1

    while (delta_v > Actual_Delta_V):
        R = vessel.orbit.radius
        a1 = vessel.orbit.semi_major_axis
        Actual_Delta_V = v1 - (G_Mun * ((2/R) - (1/a1)))**(1/2)
        # print("Текущая delta_v:", Actual_Delta_V, "из требуемой", delta_v)
    control.throttle = 0

control.sas_mode = sc.SASMode.anti_radial
print('Поворот аппарата к Муне')
time.sleep(3)
print('Отделение ступени')
control.activate_next_stage()

print('Активация исследовательского оборудования')
