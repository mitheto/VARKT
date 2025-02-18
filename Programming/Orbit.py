import krpc
import time
import math
import csv

# Целевой апоцентр
t_altitude = 100000


# Подключение к серверу kRPC
control_data = krpc.connect(name='Orbital launch')
vessel = control_data.space_center.active_vessel
ap = vessel.auto_pilot
control = vessel.control


# Установка нужных переменных
ut = control_data.add_stream(getattr, control_data.space_center, 'ut')
altitude = control_data.add_stream(getattr, vessel.flight(), 'mean_altitude')
apoapsis = control_data.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
periapsis = control_data.add_stream(getattr, vessel.orbit, 'periapsis_altitude')
stage_4_fuel = vessel.resources_in_decouple_stage(stage=3, cumulative=False)
Solid_Fuel = control_data.add_stream(stage_4_fuel.amount, 'SolidFuel')
Solid_Fuel_Sep = False

with open('../Telemetry/telemetry.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Time (s)', 'Altitude (m)', 'VerticalSpeed (m/s)', 'HorizontalSpeed (m/s)'])

    flight_info = vessel.flight(vessel.orbit.body.reference_frame)



# Настройка автопилота и стартовой тяги
control.throttle = 1
time.sleep(1)
ap.target_pitch_and_heading(90, 90)
ap.target_roll = -90
ap.engage()


# Запуск корабля
print('5')
time.sleep(1)
print('4')
time.sleep(1)
print('3')
time.sleep(1)
print('2',)
time.sleep(1)
print('1')
time.sleep(1)
print('ПОЕХАЛИ!')
control.activate_next_stage()

start_time = time.time()
t = time.time() - start_time

altitude = flight_info.mean_altitude
vertical_speed = flight_info.vertical_speed
horizontal_speed = flight_info.horizontal_speed
pitch = vessel.flight().pitch
heading = vessel.flight().heading

writer.writerow([f'{t:.3f}',
                f'{altitude:.3f}',
                f'{vertical_speed:.3f}',
                f'{horizontal_speed:.3f}'])



# Первый гравитационный манёвр
for angle_change_step in range(1, 10):
    while altitude() < 10000 + (angle_change_step - 1) * 3333:
        if not Solid_Fuel_Sep and Solid_Fuel() < 0.1:
            control.activate_next_stage()
            Solid_Fuel_Sep = True
            print('Ускорители успешно отделены')
        continue
    new_angle = angle_change_step * 10
    ap.target_pitch_and_heading(90 - new_angle, 90)


# Работа главного двигателя до достижения апоцентра
while apoapsis() < t_altitude:
    pass
control.activate_next_stage()
control.throttle = 0
time.sleep(1)
print('Требуемая высота апоцентра достигнута')
control.activate_next_stage()


# Планирование выхода на круговую орбиту
# (Используется формула vis-viva)
print('Планирование выхода на круговую орбиту')
G_Kerbin = vessel.orbit.body.gravitational_parameter
R = vessel.orbit.apoapsis
a1 = vessel.orbit.semi_major_axis
a2 = R
v1 = math.sqrt(G_Kerbin * ((2.0 / R) - (1.0 / a1)))
v2 = math.sqrt(G_Kerbin * ((2.0 / R) - (1.0 / a2)))
delta_v = v2 - v1


# Расчёт времени сгорания
# (Используется формула Циолковского )
F = vessel.available_thrust
Isp = vessel.specific_impulse * 9.82  # Удельный импульс
m0 = vessel.mass  # Масса корабля
m1 = m0 / math.exp(delta_v/Isp)
flow_rate = F / Isp
burn_time = (m0 - m1) / flow_rate


# Отключение автопилота, включение стабилизации
ap.disengage()
print('Автопилот отключён')
control.sas = True
print('Стабилизация включена')


# До включения двигателя
print('Ожидание позиции включения двигателя')
burn_ut = ut() + vessel.orbit.time_to_apoapsis - (burn_time/2)
lead_time = 10
control_data.space_center.warp_to(burn_ut - lead_time)


# Направление корабля для совершения манёвра
control.sas_mode = control_data.space_center.SASMode.prograde
print('Стабилизация в режиме "по движению" ')


# Гравитационный манёвр
print('Двигатель готов')
time_to_apoapsis = control_data.add_stream(getattr, vessel.orbit, 'time_to_apoapsis')
while time_to_apoapsis() - (burn_time/2) > 1:
    pass
print('Двигатель включён')
control.throttle = 1.0
time.sleep(burn_time + 2)
print('Корабль успешно вышел на', altitude() // 1000, 'километровую орбиту')
control.throttle = 0


# Конец программы выхода на околокербальскую орбиту
control.sas = False
print('Стабилизация отключена')
vessel.control.solar_panels = True
print('Солнечные батареи раскрыты')