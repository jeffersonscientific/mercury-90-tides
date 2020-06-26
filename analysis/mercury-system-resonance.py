#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Version 1.2

# The script will calculate the resonances between each final planets. We base our study on 'element.out'
# That means that all the planets we are interested in are still there at the end of the simulation. Thus
# we do not have to take care of the time of ejection/collision for each planet (we only take care 
# of the last values for each planet, and this could cause problem if we would have done calculations between values (for 2 planets)
# that refeered to different times during the simulation)

import pdb # Pour le debug
import numpy as np
from fractions import Fraction
import pylab as pl
import autiwa
import sys # to get access to arguments of the script

################
## Parameters ##
################
NOM_FICHIER_PLOT = "system_resonances"
OUTPUT_EXTENSION = "pdf"

DENOMINATOR_LIMIT = 30 # Maximum value allowed of the denominator when we want to get a fraction from a decimal value
NUMBER_OF_VALUES = 100 # sampling for period ratio around the given value
UNCERTAINTY = 5 # In percentage
NB_LAST_POINTS = 50 # Number of points we want to test the libration of angles.

# the threshold of the standard deviation of a resonant angle, 
# below which we consider there is libration and thus, a resonance.
STD_THRESHOLD = 40 

# Extreme angles for angle folding. We will apply a mod 2pi to all angles, 
# but theses values determines between wich values we will constrains the angles.
ANGLE_MIN = - 180.
ANGLE_MAX = 180.

def plot_res():
  # We chose the number of plot in x and y axis for the p.multi
  # environment in order to plot ALL the resonant angles and have x and
  # y numbers as close on from another as possible. There are q+1
  # resonant angles, the period ratio and w1 - w2, i.e q+3 plots
  nb_plots_x = 1
  nb_plots_y = 1
  while (nb_plots_x * nb_plots_y < q+2):
    if (nb_plots_x == nb_plots_y):
      nb_plots_y += 1
    else:
      nb_plots_x += 1
  
  # on trace les plots

  pl.figure(1) 
  pl.clf() # On cree des sous plots. Pour subplot(311), Ca signifie qu'on a 2 lignes, 3 colonnes, et que le subplot 
  # courant est le 1e. (on a donc 2*3=6 plots en tout)

  # We create a variable to store the index of the subplot
  subplot_index = nb_plots_x * 100 + nb_plots_y * 10
  pl.suptitle("resonance "+str(res.numerator)+":"+str(res.denominator)+" between "+name[planet]+" and "+name[planet+1])

  subplot_index += 1
  pl.subplot(subplot_index)
  pl.plot(t_inner, delta_longitude)
  pl.xlabel(unicode("time [years]",'utf-8'))
  pl.ylabel(unicode("w2 - w1",'utf-8'))
  #~ pl.legend()
  pl.grid(True)

  for i in range(q+1):
    subplot_index += 1
    pl.subplot(subplot_index)
    pl.plot(t_inner, phi[i])
    pl.xlabel(unicode("time [years]",'utf-8'))
    pl.ylabel(unicode("φ"+str(i),'utf-8'))
    #~ pl.legend()
    pl.grid(True)
  
  pl.show()

###############################################
## Beginning of the program
###############################################

# We get arguments from the script

#~ pdb.set_trace()
isProblem = False
problem_message = "AIM : Display in a m = f(a) diagram, all the planets of the current mercury simulation" + "\n" + \
"The script can take various arguments :" + "\n" + \
"(no spaces between the key and the values, only separated by '=')" + "\n" + \
" * cz=1 (The position of a convergence zone in AU)" + "\n" + \
"   cz=[[1,60],[4,30]] (the list of mass (earth mass) and zero torque position (in AU) successively)" + "\n" + \
" * ext=png (The extension for the output files)" + "\n" + \
" * help : display this current message"

for arg in sys.argv[1:]:
  try:
    (key, value) = arg.split("=")
  except:
    key = arg
  if (key == 'ext'):
    OUTPUT_EXTENSION = value
  elif (key == 'cz'):
    CZ = eval(value)
  elif (key == 'help'):
    print(problem_message)
    exit()
  else:
    print("the key '"+key+"' does not match")
    isProblem = True

if isProblem:
  print(problem_message)

uncertainty = 0.01 * float(UNCERTAINTY)

# To each planet named "planet01" exist a "planet01.aei" file that contains its coordinates with time.
name = [] # the name of the planets in the current simulation. 
a = [] # semi major axis (in AU)
e = [] # eccentricity
mass = [] # mass in earth mass

table = open("element.out", 'r')

# We get rid of the header
for i in range(5):
  table.readline()

lines = table.readlines()
table.close()

nb_planets = len(lines)

for line in lines:
  datas = line.split()
  name.append(datas[0])
  a.append(float(datas[1]))
  e.append(float(datas[2]))
  mass.append(float(datas[4]))

a = np.array(a)
e = np.array(e)

period = a**1.5

# We initialize the arrays where we store the presence of resonances. 
# The value at the index 'i' represent the presence of a resonance between planet i and i+1
mean_motion_res = [None] * (nb_planets - 1)
longitude_res = [False] * (nb_planets - 1)
# You can't use the formulation above, because all the items will be linked, and an append, will add an element to all the sublists.
extra_mean_motion_res = [[] for i in range(nb_planets-1)] 

t_inner = [] # time in years
a_inner = [] # demi-grand axe en ua
g_inner = [] # argument of pericentre (degrees)
n_inner = [] # longitude of ascending node (degrees)
M_inner = [] # Mean anomaly (degrees)

t_outer = [] # time in years
a_outer = [] # demi-grand axe en ua
g_outer = [] # argument of pericentre (degrees)
n_outer = [] # longitude of ascending node (degrees)
M_outer = [] # Mean anomaly (degrees)

fichier_source = name[0]+".aei"
tableau = open(fichier_source, 'r')

# we skip the three first lines
for indice in range(3):
    tableau.readline()
# we store the fourth line that contains the description of all the columns
entete = tableau.readline()

lines = tableau.readlines()
tableau.close()

for ligne in lines[-NB_LAST_POINTS:]:
  colonne = ligne.split()
  
  try:
    ti = float(colonne[0])
    ai = float(colonne[1])
    gi = float(colonne[4])
    ni = float(colonne[5])
    Mi = float(colonne[6])
  except:
    pass
  t_outer.append(ti)
  a_outer.append(ai)
  g_outer.append(gi)
  n_outer.append(ni)
  M_outer.append(Mi)

# We convert to numpy arrays, to have faster calculations
a_outer = np.array(a_outer)
g_outer = np.array(g_outer)
n_outer = np.array(n_outer)
M_outer = np.array(M_outer)

#~ nb_planets=2
for planet in range(0, nb_planets-1):
  # We read the coordinates of the next planet and exchange the values between inner and outer
  t_inner = t_outer
  a_inner = a_outer
  g_inner = g_outer
  n_inner = n_outer
  M_inner = M_outer
  
  t_outer = [] # time in years
  a_outer = [] # demi-grand axe en ua
  g_outer = [] # argument of pericentre (degrees)
  n_outer = [] # longitude of ascending node (degrees)
  M_outer = [] # Mean anomaly (degrees)
  
  fichier_source = name[planet+1]+".aei"
  tableau = open(fichier_source, 'r')

  # we skip the three first lines
  for indice in range(3):
      tableau.readline()
  # we store the fourth line that contains the description of all the columns
  entete = tableau.readline()
  
  lines = tableau.readlines()
  tableau.close()
  
  for ligne in lines[-NB_LAST_POINTS:]:
    colonne = ligne.split()
    
    try:
      ti = float(colonne[0])
      ai = float(colonne[1])
      gi = float(colonne[4])
      ni = float(colonne[5])
      Mi = float(colonne[6])
    except:
      pass
    t_outer.append(ti)
    a_outer.append(ai)
    g_outer.append(gi)
    n_outer.append(ni)
    M_outer.append(Mi)
  
  a_outer = np.array(a_outer)
  g_outer = np.array(g_outer)
  n_outer = np.array(n_outer)
  M_outer = np.array(M_outer)
  
  # We get the various possible resonance between the two planets
  periodRatio = period[planet+1] / period[planet]
  
  periodMin = periodRatio * (1 - uncertainty)
  periodMax = periodRatio * (1 + uncertainty)
  
  # We do not want period ratios less than 1 (this only happens for coorbitals I think)
  if (periodMin < 1.):
    periodMin = 1.
  
  periodWidth = periodMax - periodMin
  deltaPeriod = periodWidth/NUMBER_OF_VALUES
  
  
  periods = [periodMin + deltaPeriod * i for i in range(NUMBER_OF_VALUES)]

  resonances = []
  for period_i in periods:
    fraction = Fraction(period_i).limit_denominator(DENOMINATOR_LIMIT)
    #print(fraction)
    resonances.append(fraction)

  # We exclude all values that appears several time to only keep one occurence of each value
  resonances = list(set(resonances))
  #~ resonances = [Fraction(9,8)]
  
  # For each resonance we check if this one exist between the two considered planets
  for res in resonances:
    outer_period_nb = res.denominator
    inner_period_nb = res.numerator
    
    # Resonances are usually displayed as (p+q):p where q is the order of
    # the resonance. We retreive thoses parameters
    p = outer_period_nb
    q = inner_period_nb - outer_period_nb

    # We calculate the resonant angles
    long_of_peri_inner = g_inner + n_inner
    mean_longitude_inner = M_inner + long_of_peri_inner

    long_of_peri_outer = g_outer + n_outer
    mean_longitude_outer = M_outer + long_of_peri_outer

    phi = np.empty((q+1, NB_LAST_POINTS)) # we create an array, empty for the moment, that will contain all the resonant angles associated with the supposed resonance.

    temp_value = inner_period_nb * mean_longitude_outer - outer_period_nb * mean_longitude_inner

    for i in range(q+1):
      phi[i] = temp_value - i * long_of_peri_inner - (q - i) * long_of_peri_outer

    # We take modulo 2*pi of the resonant angle
    phi = phi%(360.)
    too_low = phi < ANGLE_MIN
    too_high = phi > ANGLE_MAX
    phi[too_low] = phi[too_low] + 360.
    phi[too_high] = phi[too_high] - 360.

    delta_longitude = long_of_peri_outer - long_of_peri_inner
    delta_longitude = delta_longitude%(360.)
    too_low = delta_longitude < ANGLE_MIN
    too_high = delta_longitude > ANGLE_MAX
    delta_longitude[too_low] = delta_longitude[too_low] + 360.
    delta_longitude[too_high] = delta_longitude[too_high] - 360.
    
    # If one of the std's is small (Typically, around 25, but 
    # I had once a 80 that was not a resonance, so I think a threshold around 40 is a good one)
    standard_deviation = min(phi.std(1))
      
    if (standard_deviation < STD_THRESHOLD):
      #~ pdb.set_trace()
      #~ pdb.set_trace()
      if (mean_motion_res[planet] == None):
        mean_motion_res[planet] = res
      else:
        # If there are several resonances, we store the smallest one (in number) 
        # as main resonance, and a list of all other resonances elsewhere.
        if (mean_motion_res[planet].numerator > res.numerator):
          extra_mean_motion_res[planet].append(mean_motion_res[planet])
          mean_motion_res[planet] = res
        else:
          extra_mean_motion_res[planet].append(res)
      
      print("resonance %i:%i between %s and %s : min(std) = %f" % (res.numerator, res.denominator, name[planet], name[planet+1], standard_deviation))
    
    if (delta_longitude.std() < STD_THRESHOLD):
      longitude_res[planet] = True
    
    #~ pdb.set_trace()
    
    #~ finir ça, il faut que je teste la libration là. Normalement, j'ai fait tout ce qui était nécessaire pour lire les fichiers, 
    #~ parcourir les planètes puis les résonnances. Penser que j'ai bloqué le nombre de planète à 2, histoire de pas avoir trop de 
    #~ calculs et de voir les erreurs directement.

# We display the resonances

# We generate a list of colors
tmp = autiwa.colorList(nb_planets)
colors = [ '#'+li for li in autiwa.colorList(nb_planets)]


markersize_prefactor = 6 / (min(mass)**0.33)
for planet in range(nb_planets):
  # We display a circle for the planet
  pl.plot(a[planet], mass[planet], 'o', color=colors[planet], markersize=int(markersize_prefactor * (mass[planet])**0.33))

ylims = list(pl.ylim())
xlims = list(pl.xlim())

# We display the convergence zone
if (vars().has_key('CZ')):
  if (type(CZ) == list):
    pl.plot(CZ[1], CZ[0], '-.', color="#000000")
  elif (type(CZ) in [float, int]):
    pl.plot([CZ, CZ], ylims, '-.', color="#000000")

for planet in range(0, nb_planets-1):
  x_position = (a[planet] + a[planet+1]) / 2.
  y_position = (mass[planet] + mass[planet+1]) / 2.
  
  # If there is resonance between the two planets, we display something
  if (mean_motion_res[planet] != None):
    # We construct the text for the main resonance
    res = str(mean_motion_res[planet].numerator)+":"+str(mean_motion_res[planet].denominator)
    if (longitude_res[planet]):
      res += "*"
    
    pl.plot([a[planet], a[planet+1]], [mass[planet], mass[planet+1]], 'k-')
    pl.plot([x_position, x_position], [y_position, ylims[1]], 'k:')
    pl.text(x_position, ylims[1], " "+res, horizontalalignment='center', verticalalignment='bottom', rotation='vertical', size=8)
  
  # We display, along the vertical line between the resonance and the text toward the main resonance value, the extra resonances if needed.
  if (len(extra_mean_motion_res[planet]) != 0):
    extra_res = str(extra_mean_motion_res[planet][0].numerator)+":"+str(extra_mean_motion_res[planet][0].denominator)
    for res in extra_mean_motion_res[planet][1:]:
      extra_res += " ; "+str(res.numerator)+":"+str(res.denominator)
    pl.text(x_position, (ylims[1]+y_position)/2., extra_res, horizontalalignment='left', verticalalignment='center', rotation='vertical', size=7)
    
#~ pl.ylim(-1, 1)
pl.xlabel("a [AU]")
pl.ylabel("mass [Earths]")
pl.savefig(NOM_FICHIER_PLOT+'.'+OUTPUT_EXTENSION, format=OUTPUT_EXTENSION)

pl.show()

# TODO
# add an option to plot resonances at a different time of the evolution.


