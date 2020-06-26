#!/usr/bin/env python
# -*- coding: utf-8 -*-
# v1.1
# help launching some commands for all the sub-simulations of sub-sub-simulations of a given folder. 

import os
import pdb
import autiwa
import sys
import subprocess
import simulations_utilities
import mercury_utilities

# Get current working directory
rep_exec = os.getcwd()

NB_OUTPUTS = 2000
EXTENSION = 1e6 # extension of the simulation in years (for extend())

def regen_aei_files():
  """in the current working directory, 
  will generate element.in (param.in 
  must exist) and launch 'element'."""
  mercury_utilities.generateOutputs()

def change_nb_outputs():
  """will adapt the timestep between outputs in 
  'element.in' depending on the integration 
  time to fit the required number of outputs.
  'param.in' must exist. But the outputs files 
  will not be re-generated"""
  mercury_utilities.generateElementIN(nb_outputs=NB_OUTPUTS)

def erase_aei():
  """supress all the .aei files for each simulation"""
  
  command = "rm *.aei"
  (stdout, stderr, returnCode) = autiwa.lancer_commande(command)

def extend():
  """Will edit the param.* files to add 'extension' to the total integration time
  
  Parameters : extension (in years)
  """
  mercury_utilities.extend_simulation(extension=EXTENSION)

COMMANDS = {"regen_aei":regen_aei_files, 
"change_nb_outputs":change_nb_outputs,
"erase_aei":erase_aei,
"extend":extend
}

COMMANDS_HELP = ""
for (key, value) in COMMANDS.items():
  COMMANDS_HELP += "    # '%s' : %s\n" % (key, value.__doc__)

#    .-.     .-.     .-.     .-.     .-.     .-.     .-.     .-.     .-. 
#  .'   `._.'   `._.'   `._.'   `._.'   `._.'   `._.'   `._.'   `._.'   `.
# (    .     .-.     .-.     .-.     .-.     .-.     .-.     .-.     .    )
#  `.   `._.'   `._.'   `._.'   `._.'   `._.'   `._.'   `._.'   `._.'   .'
#    )    )                                                       (    (
#  ,'   ,'                                                         `.   `.
# (    (                     DEBUT DU PROGRAMME                     )    )
#  `.   `.                                                         .'   .' 
#    )    )                                                       (    (
#  ,'   .' `.   .' `.   .' `.   .' `.   .' `.   .' `.   .' `.   .' `.   `.
# (    '  _  `-'  _  `-'  _  `-'  _  `-'  _  `-'  _  `-'  _  `-'  _  `    )
#  `.   .' `.   .' `.   .' `.   .' `.   .' `.   .' `.   .' `.   .' `.   .'
#    `-'     `-'     `-'     `-'     `-'     `-'     `-'     `-'     `-'
isMeta = False # If we consider the current folder as a folder that list sub-meta-simulations where the simulations really are

commandKey = None

isProblem = False
problem_message = "AIM : Provide a simple script that can execute " + "\n" + \
"several commands easily for a lot of simulations at once." + "\n" + \
"\nARGUMENTS :" + "\n" + \
"(no spaces between the key and the values, only separated by '=')" + "\n" + \
" * help : display a little help message on HOW to use various options" + "\n" + \
" * meta : option that will consider the current folder as a folder that list meta simulation instead of simple simulations" + "\n" + \
" * nb_outputs=nb : [%i] To define the number of outputs we want for .aei files. Only used by the command 'change_nb_outputs'" % NB_OUTPUTS + "\n" + \
" * extension=nb : [%f] The time of extension for the simulations (in years). Only used by the command 'extend'" % EXTENSION + "\n" + \
" * command=commandName : option that will consider the current folder as a folder that list meta simulation instead of simple simulations" + "\n" + \
"   list of commands :\n" + \
COMMANDS_HELP + \
"\nEXAMPLE : "+ "\n" + \
" > mercury-meta-command.py meta nb_outputs=1000 command=regen_aei "+ "\n" + \
" In each sub folder, we will list the folders (sub-sub folders of the CWD) "+ "\n" + \
" and consider them as simulations. For each folder, we will generate the "+ "\n" + \
" .aei files. The option nb_outputs here will not we used, since only " + "\n" + \
" the command '' use it to modify element.in "+ "\n"


# We get arguments from the script
for arg in sys.argv[1:]:
  try:
    (key, value) = arg.split("=")
  except:
    key = arg
  if (key == 'command'):
    commandKey = value
  elif (key == 'meta'):
    isMeta = True
  elif (key == 'nb_outputs'):
    NB_OUTPUTS = int(value)
  elif (key == 'extension'):
    EXTENSION = float(value)
  elif (key == 'help'):
    isProblem = True
  else:
    print("the key '"+key+"' does not match")
    isProblem = True

if (commandKey == None):
  isProblem = True

if isProblem:
  print(problem_message)
  exit()

# We go in each sub folder of the current working directory

# If sub folders are meta simulation folders instead of folders, we list the meta simulation folder to run the test in each sub folder.
if (isMeta):
  meta_list = [dir for dir in os.listdir(".") if (os.path.isdir(dir))]
  meta_list.sort()
else:
  meta_list = ["."]

nb_meta = len(meta_list)
purcent_meta = 100. / float(nb_meta)

for (meta_i, meta) in enumerate(meta_list):
  os.chdir(meta)
  
  # For the evolving purcentage of the script, the purcent at which we start, 
  # who correspond to the number of meta simulation done before and the purcentage
  # associated to each meta simulation (only equally splitted depending on the 
  # total of meta simulation we must do
  purcent_offset = meta_i * purcent_meta 
  
  if (meta == '.'):
    absolute_parent_path = rep_exec
  else:
    absolute_parent_path = os.path.join(rep_exec, meta)
  
  # We get the list of simulations
  simu_list = [dir for dir in os.listdir(".") if (os.path.isdir(dir))]
  #autiwa.suppr_dossier(liste_simu,dossier_suppr)
  simu_list.sort()
  
  nb_simus = len(simu_list)
  
  for (simu_i, simu) in enumerate(simu_list):
    os.chdir(simu)
    purcent = purcent_offset + (simu_i + 1) / float(nb_simus) * purcent_meta
    sys.stdout.write("  %5.1f %% : %s                         \r" % (purcent, os.path.join(meta,simu)))
    sys.stdout.flush()
    
    # We execute te required command
    COMMANDS[commandKey]()
    
    # We get back in the parent directory
    os.chdir("..")
  
  # We get back in the parent directory
  os.chdir(rep_exec)

