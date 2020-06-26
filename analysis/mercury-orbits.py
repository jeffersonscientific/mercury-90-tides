#!/usr/bin/env python
# -*- coding: utf-8 -*-
# v1.0
# To display the orbits of the planets in the system in the (x,y) plane

from math import *
import pylab as pl
import os, pdb, autiwa
import numpy as np
import sys # to be able to retrieve arguments of the script
import mercury

BINARY_FOLDER = '$HOME/bin/mercury'
FRAME_PREFIX = "frame_"
OUTPUT_EXTENSION = 'png'

NB_POINTS = 50 # Number of points for the display of circles
NB_FRAMES = 2
NB_P_ORBITS = 1 # The number of orbits to display in case of tail

isTail = True # There is a part where this boolean is changed automatically if the timestep between two output is to huge.
isReferenceFrame = False # If we display orbits in the reference frame of a given planet
###############################################
## Beginning of the program
###############################################


# We get arguments from the script

isProblem = False
problem_message = "The script can take various arguments :" + "\n" + \
"(no spaces between the key and the values, only separated by '=')" + "\n" + \
" * t_max=1e3 : the end of the output (in years)" + "\n" + \
" * t_min=1e4 : the beginning of the output (in years)" + "\n" + \
" * ref=BIG_0001.aei : to display the orbits in the rotating frame of BIG_0001 planet" + "\n" + \
" * forceCircle : to display circle instead of real orbits if the output interval is huge\n" + \
" * zoom=1. : the farthest location in the disk that will be displayed (in AU)" + "\n" + \
" * frames=%d : the number of frames you want" % NB_FRAMES + "\n" + \
" * ext=%s : The extension for the output files" % OUTPUT_EXTENSION

for arg in sys.argv[1:]:
  try:
    (key, value) = arg.split("=")
  except:
    key = arg
  if (key == 't_min'):
    t_min = float(value)
  elif (key == 't_max'):
    t_max = float(value)
  elif (key == 'forceCircle'):
    isTail = True
  elif (key == 'frames'):
    NB_FRAMES = int(value)
  elif (key == 'ext'):
    OUTPUT_EXTENSION = value
  elif (key == 'zoom'):
    plot_range = float(value)
  elif (key == 'ref'):
    isReferenceFrame = True
    referenceFrame = value
    NB_P_ORBITS = 20
  elif (key == 'help'):
    print(problem_message)
    exit()
  else:
    print("the key '"+key+"' does not match")
    isProblem = True

if isProblem:
  print(problem_message)

if (NB_FRAMES <= 1):
  print("The number of frames cannot be lower than 2")
  NB_FRAMES = 2
  
####################
# We erase old output files, add 'x, y and z' to the outputs values, and generate new output files
####################

autiwa.lancer_commande("rm *.aei element.out")

elementin = mercury.Element()
elementin.read()
elementin.set_format_sortie(" a21e e21e i8.4 g8.4 n8.4 l8.4 m21e x21e y21e z21e")
elementin.write()

(stdout, stderr, returnCode) = autiwa.lancer_commande(os.path.join(BINARY_FOLDER, "element"))
if (returnCode != 0):
  print("Unable to Launch 'element'")

####################
# On recupere la liste des fichiers planetes.aei
####################
(process_stdout, process_stderr, return_code) = autiwa.lancer_commande("ls *.aei")
if (return_code != 0):
  print("the command return an error "+str(return_code))
  print(process_stderr)
  exit()
  
liste_aei = process_stdout.split("\n")
liste_aei.remove('') # we remove an extra element that doesn't mean anything
nb_planete = len(liste_aei)

if isReferenceFrame:
  for (ID_planet, planet) in enumerate(liste_aei):
    if (planet == referenceFrame):
      ID_reference = ID_planet

####################
# On lit, pour chaque planete, le contenu du fichier et on stocke les variables qui nous interessent.
####################
t = [] # temps en annee
a = [] # the semi major axis in AU
m = [] # mass in earth mass
x = [] # x cartesian coordinate in AU
y = [] # y cartesian coordinate in AU
z = [] # z cartesian coordinate in AU


# On recupere les donnees orbitales
for planete in range(nb_planete):
  
  fichier_source = liste_aei[planete]
  tableau = open(fichier_source, 'r')
  
  tp = [] # time in year
  ap = [] # the Semi-major axis in AU
  mp = [] # mass in earth mass
  xp = [] # x en ua
  yp = [] # y en ua
  zp = [] # z en ua
  
  tappend = tp.append
  aappend = ap.append
  mappend = mp.append
  xappend = xp.append
  yappend = yp.append
  zappend = zp.append
  
  # 3 lines of header
  for indice in range(3):
    tableau.readline()

  entete = tableau.readline()
  for ligne in tableau:
    colonne = ligne.split()
    

    # In case of ejection, prevent the scrip to crash. "avoid problem of NaN and ******"
    try:
      ti = float(colonne[0])
      ai = float(colonne[1])
      mi = float(colonne[7]) / 3.00374072e-6 # in solar mass
      xi = float(colonne[8])
      yi = float(colonne[9])
      zi = float(colonne[10])
      
      # We must append inside the 'try' to avoid appending a value twice. The problem should occurs before anyway, when trying to convert into float
      tappend(ti)
      aappend(ai)
      mappend(mi)
      xappend(xi)
      yappend(yi)
      zappend(zi)
    except:
      pass
  tableau.close()
  
  t.append(np.array(tp))
  a.append(np.array(ap))
  m.append(np.array(mp))
  x.append(np.array(xp))
  y.append(np.array(yp))
  z.append(np.array(zp))

# The separation between outputs is not always the same because the real output interval in mercury and element might be slightly different.
delta_t = (t[0][-1] - t[0][0]) / float(len(t[0]))

# If the timestep between two outputs is to big, we do not display a tail, because the planet will have time to do more than one 
# orbit between two values 
if (delta_t > 10.):
  print("/!\ time between output will have the effect to display ugly orbits. \
  Try the option 'isTail=False', but orbits will be circle and not representative of reality")

# We get the array of reference time, i.e, one of the longuest list of time available in the list of planets. 
ref_len = 0
ref_id = 0
for planet in range(nb_planete):
  len_i = len(t[planet])
  if (len_i > ref_len):
    ref_len = len_i
    ref_id = planet
ref_time = t[ref_id]

# We get the index for the t_max value
if ('t_max' in locals()):
  id_max = int((t_max - ref_time[0]) / delta_t)
  t_max = ref_time[id_max]
else:
  id_max = ref_len - 1
  t_max = ref_time[-1]

# We get the index for the t_max value
if ('t_min' in locals()):
  id_min = int((t_min - ref_time[0]) / delta_t)
  t_min = ref_time[id_min]
else:
  id_min = 0
  t_min = ref_time[0]

if isReferenceFrame:
  x_ref = x[ID_reference]
  y_ref = y[ID_reference]
  
  omega = -2. * np.arctan(y_ref / (x_ref + np.sqrt(x_ref**2 + y_ref**2)))
  
  r = []
  for planet in range(nb_planete):
    ri = np.sqrt(x[planet]**2 + y[planet]**2)
    r.append(ri)
    theta = 2. * np.arctan(y[planet] / (x[planet] + ri))
    x[planet] = ri * np.cos(theta + omega)
    y[planet] = ri * np.sin(theta + omega)



# on trace les plots
autiwa.lancer_commande("rm %s*" % FRAME_PREFIX) # We delete the previous frames

delta_t_min = (t_max - t_min) / (float(NB_FRAMES -1.))
# Number of timestep between each frame
# real number to be as close as possible from the real value, and do not encounter rounding problems. 
# The conversion to an integer is done at the very end.
ts_per_frame = delta_t_min / delta_t 

# If there is too many frames for the outputs availables, we impose 1 output between each frames and reduce the total number of frames
if (ts_per_frame < 1):
  ts_per_frame = 1
  NB_FRAMES = id_max - id_min +1


# We generate a list of colors
tmp = autiwa.colorList(nb_planete)
colors = [ '#'+li for li in autiwa.colorList(nb_planete)]

if not(isTail):
  angles = [2 * pi / NB_POINTS * i for i in range(NB_POINTS)]
  angles.append(angles[0]) # we want to have a full circle, perfectly closed
  angles = np.array(angles)


fig = pl.figure()
plot_orbits = fig.add_subplot(1, 1, 1)
plot = plot_orbits.plot
MAX_LENGTH = len(str(NB_FRAMES)) # The maximum number of characters needed to display


for frame_i in range(1, NB_FRAMES+1):
  id_time = id_min + int(frame_i * ts_per_frame)
  t_frame = t_min + int(frame_i * ts_per_frame) * delta_t
  
  if (frame_i == NB_FRAMES - 1):
    id_time = id_max
    t_frame = t_max
  
  print("frame %*d : T = %#.2e years" % (MAX_LENGTH, frame_i, t_frame))
  

  plot_orbits.clear()

  # We put a yellow star to display the central body
  plot(0, 0, '*', color='yellow', markersize=20) 

  if isTail:
    idx_tail = [None] * nb_planete
    for planet in range(nb_planete):
      # If the planet is still in the system at that time, we display it, else, the 'except' make us pass to the next planet.
      try:
        
        tmp = a[planet][id_time]**1.5 # the period of the planet in years
        tmp = int(id_time - NB_P_ORBITS * tmp / delta_t + 2)
        # Negative index is not possible. So if the planet did not have the time to do one orbit, the tail will be artitificially put to 0
        if (tmp < 0):
          tmp = 0
        idx_tail[planet] = tmp
        plot(x[planet][idx_tail[planet]:id_time+1], y[planet][idx_tail[planet]:id_time+1], color=colors[planet], label='PLANETE'+str(planet))
        plot(x[planet][id_time], y[planet][id_time], 'o', color=colors[planet], markersize=int(5* (m[planet][id_time])**0.33))
      except:
        pass
        # The planet has been ejected
  else:
    # We draw circles for each orbit. This part might be used if a delta_t is more than one orbit of a planet.
    for planet in range(nb_planete):
      try:
        r = sqrt(x[planet][id_time]**2 + y[planet][id_time]**2)
        x_circ = r * np.cos(angles)
        y_circ = r * np.sin(angles)
        plot(x_circ, y_circ, color=colors[planet], label='PLANETE'+str(planet))
        plot(x[planet][id_time], y[planet][id_time], 'o', color=colors[planet], markersize=int(5* (m[planet][id_time])**0.33))
      except:
        pass
        #~ # The planet has been ejected
  plot_orbits.set_title("T = %#.2e years" % t_frame)
  plot_orbits.set_xlabel("x (in AU)")
  plot_orbits.set_ylabel("y (in AU)")
  
  pl.axis('equal')
  if ('plot_range' in vars()):
    # We draw transparent lines to force correct display. Else, he do not necessarily display all the planets...
    plot([-plot_range, plot_range], [0, 0], alpha=0.)
    plot([0, 0], [-plot_range, plot_range], alpha=0.)
    
  
  plot_orbits.grid(True)
  nom_fichier_plot = "%s%0*d" % (FRAME_PREFIX, MAX_LENGTH, frame_i)
  
  fig.savefig("%s.%s" % (nom_fichier_plot, OUTPUT_EXTENSION), format=OUTPUT_EXTENSION)

if (NB_FRAMES<3):
  pl.show()

