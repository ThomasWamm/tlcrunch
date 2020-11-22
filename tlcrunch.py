#!/usr/bin/python3
#
# tlcrunch - simple CPU benchmarking with Python
#
# Derived from a stripped-down 'TerraLunar',
# 2-D orbital mechanics simulation in Earth-Moon space.
# by Thomas during 2020 for learning Python & SWEng
#     2020-Nov-21 -- Derived from TerraLunar 0.1.2.1
#
# TerraLunar Mystery:  different CPUs give different results!
#
# Use simplified Newtonian physics and numerical integrations.
# F = ma = -GMm/r^2
# a = F/m = -GM/r^2
# v = v + dv = v + adt
# x = x + dx = x + vdt
# t = t + dt
#
# This should run on Linux, Windows, iOS, and MacOS with Python3.7+.

tlcrunch_version = "0.0.0"

import math
import time

print('\n')
print(f'____  tlcrunch ver {tlcrunch_version}:  simple CPU benchmarker  ____')

# Global objects for Earth, Moon, and one spacecraft...

# define a class to store a set of initial conditions...

class Initset:
    def __init__(self, moondegrees=60.0,
                 shipxmd=1.0,
                 shipymd=0.0,
                 shipvx=0.0,
                 shipvy=851.0,
                 dtime=10,
                 description='Default setup'):

        self.moondegrees = moondegrees
        self.shipxmd = shipxmd
        self.shipymd = shipymd
        self.shipvx = shipvx
        self.shipvy = shipvy
        self.dtime = dtime
        self.description = description

# A variety of interesting setups have been accumulated...

setuplib = (['moondeg','xmd','ymd','vx','vy','dt','Description'],
            [60.0, 1.1, 0.0, 0.0, 1000.0, 30, '9.4M steps to escape'],
            [60.0, 1.1, 0.0, 0.0, 1000.0, 60, '323k steps to lunar impact'],
            [60.0, 1.1, 0.0, 0.0, 1000.0, 1, 'escape within 1B steps; small dt'],
            [60.0, 1.1, 0.0, 0.0, 1000.0, 10, 'eventual lunar impact; medium dt'],
            [60.0, 1.1, 0.0, 0.0, 1000.0, 60, 'eventual lunar impact; big dt'],
            [60.0, 1.1, 0.0, 0.0, 1000.0, 30, '8M steps to escape'],
            [0.0, 0.017, 0.0, 0.0, 9200.0, 1, 'elliptical orbit'],
            [0.0, 0.017, 0.0, 0.0, 7900.0, 1, 'LEO = low Earth orbit'],
            [0.0, 0.10968811, 0.0, 0.0, 3074.7937, 1, 'geosynchronous orbit'],
            [0.0, 0.8491, 0.0, 0.0, 861.2724303351446, 10, 'just outside L1'],
            [0.0, 0.8491, 0.0, 0.0, 861.2724303351447, 10, 'outside 22M inside outside L1'],
            [0.0, 0.8491, 0.0, 0.0, 861.27243, 10, 'just below L1'],
            [0.0, 0.85, 0.0, 0.0, 870.0, 10, 'near L1'],
            [0.0, 0.90, 0.0, 0.0, 770.0, 10, 'distant lunar orbit'],
            [135.4, 0.0168, 0.0, 0.0, 11050.0, 1, 'escape with lunar assist'],
            [135.0, 0.0168, 0.0, 0.0, 11050.0, 1, 'Ranger direct lunar impact'],
            [0.0, 0.995, 0.0, 0.0, 2590.0, 10, 'Apollo 8 orbiting moon'],
            [135.0, 0.017, 0.0, 0.0, 10998.0, 1, 'Apollo 13 safe return'],
            [135.0, 0.017, 0.0, 0.0, 10990.0, 1, 'direct lunar impact'],
            [135.0, 0.017, 0.0, 0.0, 11000.0, 1, 'lost Apollo 13'],
            [130.0, 0.02, 0.0, 0.0, 10080.0, 10, '2-orbit lunar impact'],
            [60.0, 0.8, 0.0, 400.0, 1100., 50, 'failed L4; 11M steps to moon'],
            [60.0, 0.8, 0.0, 100.0, 1073., 10, 'eventual lunar impact #2'],
            [60.0, 1.0, 0.0, 0.0, 900.0, 101, 'lunar impact 1.5M loops'],
            [60.0, 1.0, 0.0, 0.0, 900.0, 60, 'many lunar interactions'],
            [60.0, 1.0, 0.0, 0.0, 900.0, 30, 'lunar impact, 2.2M steps'],
            [60.0, 1.0, 0.0, 0.0, 900.0, 10, 'temporary lunar orbits then impact'],
            [55.0, 3.0, 0.0, 0.0, 0.0, 10, 'non-fall to Earth from 3 moondistances.'],
            [40.0, 5.0, 0.0, 0.0, 0.0, 1, 'fall to Earth from 5 moondistances.'],
            [60.0, 0.9, 0.0, 0.0, 950.0, 60, '11.85M steps to Lunar Impact'],
            [60.0, 0.8, 0.0, 0.0, 1073., 10, 'lunar impact'],
            [60.0, 1.0, 0.0, 0.0, 923.0, 10, 'lunar impact, vy=921-926'])

def grabsetup(i):   # return one setup from library
    return Initset(moondegrees=setuplib[i][0],
                   shipxmd=setuplib[i][1],
                   shipymd=setuplib[i][2],
                   shipvx=setuplib[i][3],
                   shipvy=setuplib[i][4],
                   dtime=setuplib[i][5],
                   description=setuplib[i][6])

def parseparams(d):   # extract setup from json dictionary object
    return Initset(moondegrees=d['moondeg'],
                   shipxmd=d['xmd'],
                   shipymd=d['ymd'],
                   shipvx=d['vx'],
                   shipvy=d['vy'],
                   dtime=d['dt'],
                   description=d['Description'])

def grabsnap():   # grab parameter snapshot to enable logging and replays
    snapdict = {'moondeg': math.degrees(moonangle),
                'xmd': shipx/moondistance,
                'ymd': shipy/moondistance,
                'vx': shipvx,
                'vy': shipvy,
                'dt': dtime,
                'Description': 'Snapshot from: ' + inz.description}
    return snapdict


# Display the available initial condition setups...

i = 1
columns = 2    # for smaller displays, e.g. mobiles
columns = 3    # for larger displays
columns = 1    # for maximum simplicity
while i < len(setuplib):
    for j in range(i, min(i+columns, len(setuplib))):
        print(f'{j:2d} {setuplib[j][-1]:40}', end='')
    print()
    i += columns

# Now ask the user (thru console I/O) to choose one of the setups...

query = None
while query is None:
    query = input("Choose an initial setup: ")
    if query == '':     # <Enter> is convenient
        query = 1
    else:
        try:
            query = int(query)
        except:
            print("Enter a number to choose initial setup.")
            query = None

setupnum = query
if setupnum < 1:
    setupnum = 1
if setupnum > len(setuplib)-1:
    setupnum = len(setuplib)-1

inz = grabsetup(setupnum)

# All the graphics have been stripped out since the original TerraLunar.
# For the numerical physics model, use MKS units:  meter, kilogram, second.
# Use the average Earth-Moon distance as a unit for scaling.

moondistance = 3.84399e8

# Set up initial conditions in our simulated universe...
# Earth is at origin of 2-dimensional x-y coordinate plane.

earthrad = 6.3781e6   # radius of Earth in meters
earthx = 0.0
earthy = 0.0

moonrad = 1.7374e6   # radius of Moon in meters

moonangle = math.radians(inz.moondegrees)  # calculate with radians
moonx = earthx + moondistance*math.cos(moonangle)
moony = earthy + moondistance*math.sin(moonangle)

shipstatus = 'in orbit'

shipx = earthx + moondistance*inz.shipxmd
shipy = earthy + moondistance*inz.shipymd
d2e = math.hypot(shipx - earthx, shipy - earthy)
moonunits = d2e / moondistance
shipvx = inz.shipvx
shipvy = inz.shipvy

simtime = 0             # elapsed simulation time
dtime = inz.dtime       # time step for simulation
gravcon = -6.67430e-11
earthgrav = gravcon * 5.972e24
moongrav = gravcon * 7.342e22
# moon orbits counterclockwise 360 degrees/(27 days + 7 hr + 43 min + 12 sec)
moonstep = math.radians(360.*dtime/(27.*24*60*60 + 7.*3600 + 43.*60 + 12.))

orbits = 0     # to count orbits around Earth
steps = 0
starttime = time.time()   # includes CPU interruptions & some overheads
# starttime = time.process_time()   # this may be better

starttimestamp = time.asctime(time.localtime())
running = True

print('Started @ ' + starttimestamp)

# Top of big numerical integration simulation loop...
# This doesn't have to be efficient, for comparative benchmarking.

while running:     # break out on crashlanding or escape to deep space
    d2e = math.hypot(shipx - earthx, shipy - earthy)
    if d2e < earthrad:
        shipstatus = "Burned up in Earth atmosphere!"
        break

    d2m = math.hypot(shipx - moonx, shipy - moony)
    if d2m < moonrad:
        shipstatus = "Blasted new crater into Moon !"
        break

    s2eaccel = dtime * earthgrav / (d2e * d2e * d2e)
    s2maccel = dtime * moongrav / (d2m * d2m * d2m)
    shipvx += s2eaccel * (shipx - earthx) + s2maccel * (shipx - moonx)
    shipvy += s2eaccel * (shipy - earthy) + s2maccel * (shipy - moony)
    oldshipy = shipy  # to detect crossing of x-axis each orbit of Earth
    shipx += dtime * shipvx
    shipy += dtime * shipvy

    if oldshipy < earthy and shipy >= earthy:  # detect x-axis crossings
        orbits += 1
        snapshot = grabsnap()    # snapshot of current parameters

    moonangle += moonstep
    moonx = earthx + moondistance*math.cos(moonangle)
    moony = earthy + moondistance*math.sin(moonangle)

    velocity = math.hypot(shipvx, shipvy)
    escapevelocity = math.sqrt(-2.0 * (earthgrav + moongrav) / d2e)

    if (velocity > escapevelocity) and (d2e > 10 * moondistance):
        shipstatus = "Escape velocity !  Lost in space!"
        break

    simtime += dtime
    steps += 1
    # Bottom of big numerical integration loop; repeat until terminated.

running = False     # Simulation loop has exited. Output stats...

stoptime = time.time()   # includes CPU interruptions & some overheads
# stoptime = time.process_time()   # this may be better

endtimestamp = time.asctime(time.localtime())
print('Stopped @ ' + endtimestamp)   # sometimes I run it for days

elapsedtime = stoptime - starttime
if elapsedtime == 0:
    elapsedtime = 0.001

sps = int(steps / elapsedtime)    # steps per second = CPU performance
moonunits = d2e / moondistance    # useful for debugging
velocity = math.hypot(shipvx, shipvy)

print('\nShip status:  ' +  shipstatus)
print(f"Setup option was: {setupnum}: {inz.description}\n",
      f"{steps:,} steps in {elapsedtime:,.3f} seconds\n\n",
      f"steps per second = {sps:,}         orbits = {orbits}\n")

##snapshot = grabsnap()    # snapshot
##snapshot["Description"] = f"Final snapshot; {shipstatus}"
##print(snapshot)

# To detect variation in numerical results among different computers, 
# compute and print a mashup final result...

mashup = abs(shipx * shipy * shipvx * shipvy * moonangle)
print(f"Computation Summary Mashup = {mashup}\n")

exittimestamp = time.asctime(time.localtime())
print('Exited  @ ' + exittimestamp)   # sometimes I ignore it for days

# end.