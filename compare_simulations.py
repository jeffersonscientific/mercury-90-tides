#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Script that run a mercury simulation and test if the outputs and binaries have correct behaviour. 
# The goal is to compare with a given version of the code, either an old one, the previous or current one.

__author__ = "Christophe Cossou <cossou@obs.u-bordeaux1.fr>"
__date__ = "3 august 2014"
__version__ = "$Revision: 3.0 $"

import sys
import os
import difflib # To compare two strings
import subprocess # To launch various process, get outputs et errors, returnCode and so on.
import pdb # To debug
import glob # to get list of file through a given pattern
from mercury import * # In order to create a simulation via python

NEW_TEST = "example_simulation"
PREVIOUS_TEST = "old_simulation"
REVISION = "HEAD"
PROGRAM_NAME = "mercury"

OUTPUT_FILENAMES = ["xv.out"]
CLOSE_FILENAMES = ["ce.out"]
ASCII_FILES = ["info.out", "big.dmp", "small.dmp", "param.dmp", "restart.dmp", "big.tmp", "small.tmp", "param.tmp", "restart.tmp"]

# Parameters
force_source = False # To force the compilation of every module
force_simulation = False # To force generation of simulation outputs for the "old" version of the code

isProblem = False
problem_message = """Script that run a mercury simulation and test if the outputs and binaries have 
correct behaviour. The goal is to compare with a given version of the code, 
either an old one, the previous or current one. By default, we take the 
current version of the code (the first time) and compare with the non 
committed modifications. but one can force the change of reference version by 
using the "rev=xxx" option. Without changing the code, one can force the 
comparison with a different simulation (the one in "example_simulation" will be 
copied in the other folder) by using the "force" option.

The script can take various arguments :
(no spaces between the key and the values, only separated by '=')
 * help : display a little help message on HOW to use various options
 * force : To force generation of outputs for the 'old' program (after copying
           simulation files from the example)
 * actual : To force copying HEAD simulation, compyling it, then generating 
            simulation outputs
 * faq : Display possible problems that might occurs during comparison
 * rev=%s : (previous, actual, current) are possible. Else, every 
            Git ID syntax is OK. The reference revision for the 
            comparison with actual code

 Example : 
(examples are ordered. From the more common, to the more drastic.)
> compare_simulations.py #only generate new outputs, do nothing 
                         for the old one
> compare_simulations.py force # copy inputs in old folder, then 
                               generate outputs for both binaries
> compare_simulations.py actual # compile HEAD, copy inputs in old folder,
                                then generate outputs for for both binaries
> compare_simulations.py rev=cdabb998 # compile the given revision, copy input 
                                      in old folder then generate outputs 
                                      for both binaries""" % REVISION

isFAQ = False
faq_message = """* If you have differences, ensure that all 
your modules have been compiled with 'test' options. 
To make sure of that:
> Makefile.py test force

Once this is done, make:
> Makefile.py force
to recompile all module with speed options.
"""

value_message = "/!\ Warning: %s does not need any value, but you defined '%s=%s' ; value ignored."

# We get arguments from the script
for arg in sys.argv[1:]:
  try:
    (key, value) = arg.split("=")
  except:
    key = arg
    value = None
  if (key == 'force'):
    force_simulation = True
    if (value != None):
      print(value_message % (key, key, value))
  elif (key == 'actual'):
    force_source = True
    force_simulation = True
    REVISION = "HEAD"
    if (value != None):
      print(value_message % (key, key, value))
  elif (key == 'help'):
    isProblem = True
    if (value != None):
      print(value_message % (key, key, value))
  elif (key == 'faq'):
    isFAQ = True
    if (value != None):
      print(value_message % (key, key, value))
  elif (key == 'rev'):
    # If a revision is specified, we force the actualisation of source code, compilation and simulation.
    force_source = True
    force_simulation = True
    if (value in ['actual', 'current']):
      REVISION = "HEAD"
    elif (value in ['previous']):
      REVISION = "HEAD^"
    else:
      REVISION = value
  else:
    print("the key '%s' does not match" % key)
    isProblem = True

if isProblem:
  print(problem_message)
  exit()

if isFAQ:
  print(faq_message)
  exit()


def run(commande):
  """lance une commande qui sera typiquement soit une liste, soit une 
  commande seule. La fonction renvoit un tuple avec la sortie, 
  l'erreur et le code de retour"""
  if (type(commande)==list):
    process = subprocess.Popen(commande, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  elif (type(commande)==str):
    process = subprocess.Popen(commande, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
  else:
    raise TypeError("The command is neither a string nor a list.")
  (process_stdout, process_stderr) = process.communicate()
  returncode = process.poll()
  # there is .poll() or .wait() but I don't remember the difference. For some kind of things, one of the two was not working
  return (process_stdout, process_stderr, returncode)

def clean():
  """Delete all outputs files for a given nautilus simulation"""
  run("rm *.tmp")
  run("rm *.dmp")
  run("rm *.out")

def ASCIICompare(original, new):
  """function that compare and print differences between to strings that are compared line by line."""
  
  modified = ["+ ", "- ", "? "]
  
  # We want lists, because difflib.Differ only accept list of lines.
  original = original.split("\n")
  new = new.split("\n")
  
  d = difflib.Differ()

  result = list(d.compare(original, new))
  
  differences = []
  line_number_original = 0
  line_number_new = 0
  for line in result:
    if (line[0:2] == "  "):
      line_number_original += 1
      line_number_new += 1
    elif (line[0:2] == "- "):
      line_number_original += 1
      differences.append("[ori] l"+str(line_number_original)+" :"+line[2:])
    elif (line[0:2] == "+ "):
      line_number_new += 1
      differences.append("[new] l"+str(line_number_new)+" :"+line[2:])
    elif (line[0:2] == "? "):
      differences.append("      l"+str(max(line_number_new, line_number_original))+" :"+line[2:])

  # We print separately because it is more convenient if we want to store in a file instead.
  if (differences != []):
    return "\n".join(differences)
  else:
    return None

def compare2files(ori_files,new_files):
  """Function that will use compare to see differences between 'original' 
  that is thought to be a variable and 'new_file' that is the name of a 
  file to read then use as input
  """
  no_diff = []
  diff = []
  
  for (original, new) in zip(ori_files, new_files):
    f_old = open(original, 'r')
    old_lines = f_old.readlines()
    f_old.close()
    
    f_new = open(new, 'r')
    new_lines = f_new.readlines()
    f_new.close()
    
    
    difference = ASCIICompare(''.join(old_lines), ''.join(new_lines))
    if (difference == None):
      no_diff.append(new)
    else:
      diff.append([new, difference])
  
  # Now we output results
  if (diff != []):
    for (file, comp) in diff:
      print("\nFor "+file)
      print(comp)
      
    if (no_diff != []):
      print "No differences seen on :",', '.join(no_diff)
  else:
    print("Everything OK")  
  
  return 0

def compare2Binaries(ori_files, new_files):
  """Function that will use compare to see differences between 'original' 
  that is thought to be a variable and 'new_file' that is the name of a 
  file to read then use as input
  """
  no_diff = []
  diff = []
  
  for (original, new) in zip(ori_files, new_files):
    (stdout, stderr, returnCode) = run("md5sum %s" % original)
    md5_ori = stdout.split()[0]
    
    (stdout, stderr, returnCode) = run("md5sum %s" % new)
    md5_new = stdout.split()[0]
    
    if (md5_new != md5_ori):
      diff.append(original)
    else:
      no_diff.append(original)
  
  # Now we output results
  if (diff != []):
    for filename in diff:
      print("\ndifferences with binary  %s" % filename)
      
    if (no_diff != []):
      print("No differences seen on :%s" % ', '.join(no_diff))
  else:
    print("Everything OK")
  
  return 0

def initialising_input_objects(algorithm):
  """Generation of base simulation.
  Create the objects, then generate the corresponding input files
  in the current working directory.
  """
  mercury = BodyCart("big",name="MERCURY", x=-3.83966017419175965E-01, y=-1.76865300855700736E-01, z=2.07959213998758705E-02,
  vx=5.96286238644834141E-03, vy=-2.43281292146216750E-02, vz=-2.53463209848734695E-03, m=1.66013679527193009E-07,
  r=20.0e0, d=5.43)
  venus = BodyCart("big",name="VENUS", x=6.33469157915745540E-01, y=3.49855234102151691E-01, z=-3.17853172088953667E-02,
  vx=-9.84258038001823571E-03, vy=1.76183746921837227E-02, vz=8.08822351013463794E-04, m=2.44783833966454430E-06,
  r=20.0e0, d=5.24)
  earthmoo = BodyCart("big", name="EARTHMOO", x=2.42093942183383037E-01, y=-9.87467766698604366E-01, z=-4.54276292555233496E-06,
  vx=1.64294055023289365E-02, vy=4.03200725816140870E-03, vz=1.13609607260006795E-08, m=3.04043264264672381E-06,
  r=20.0e0, d=5.52)
  mars = BodyCart("big", name="MARS", x=2.51831018120174499E-01, y=1.52598983115984788E+00, z=2.57781137811807781E-02,
  vx=-1.32744166042475433E-02, vy=3.46582959610421387E-03, vz=3.98930013246952611E-04, m=3.22715144505386530E-07,
  r=20.0e0, d=3.94)
  jupiter = BodyCart("big", name="JUPITER", x=4.84143144246472090E+00, y=-1.16032004402742839E+00, z=-1.03622044471123109E-01,
  vx=1.66007664274403694E-03, vy=7.69901118419740425E-03, vz=-6.90460016972063023E-05, m=9.54791938424326609E-04,
  r=3.0e0, d=1.33)
  saturn = BodyCart("big", name="SATURN", x=8.34336671824457987E+00, y=4.12479856412430479E+00, z=-4.03523417114321381E-01,
  vx=-2.76742510726862411E-03, vy=4.99852801234917238E-03, vz=2.30417297573763929E-05, m=2.85885980666130812E-04,
  r=3.0e0, d=0.70)
  uranus = BodyCart("big", name="URANUS", x=1.28943695621391310E+01, y=-1.51111514016986312E+01, z=-2.23307578892655734E-01,
  vx=2.96460137564761618E-03, vy=2.37847173959480950E-03, vz=-2.96589568540237556E-05, m=4.36624404335156298E-05,
  r=3.0e0, d=1.30)
  neptune = BodyCart("big", name="NEPTUNE", x=1.53796971148509165E+01, y=-2.59193146099879641E+01, z=1.79258772950371181E-01,
  vx=2.68067772490389322E-03, vy=1.62824170038242295E-03, vz=-9.51592254519715870E-05, m=5.15138902046611451E-05,
  r=3.0e0, d=1.76)
  pluto = BodyCart("big", name="PLUTO", x=-1.15095623952731607E+01, y=-2.70779438829451422E+01, z=6.22871533567077229E+00,
  vx=2.97220056963797431E-03, vy=-1.69820233395912967E-03, vz=-6.76798264809371094E-04, m=7.39644970414201173E-09,
  r=3.0e0, d=1.1)
  
  apollo = BodyAst("small", name="APOLLO", a=1.4710345, e=.5600245, I=6.35621, 
  g=285.63908, n=35.92313, M=15.77656, ep=2450400.5)
  jason = BodyAst("small", name="JASON", a=2.2157309, e=.7644575, I=4.84834, 
  g=336.49610, n=169.94137, M=293.37226, ep=2450400.5)
  khufu = BodyAst("small", name="KHUFU", a=0.9894948, e=.4685310, I=9.91298, 
  g=54.85927, n=152.64772, M=66.69818, ep=2450600.5)
  minos = BodyAst("small", name="MINOS", a=1.1513383, e=.4127106, I=3.93863, 
  g=239.50170, n=344.85893, M=8.93445, ep=2450400.5)
  orpheus = BodyAst("small", name="ORPHEUS", a=1.2091305, e=.3226805, I=2.68180, 
  g=301.55128, n=189.79654, M=28.31467, ep=2450400.5)
  toutatis = BodyAst("small", name="TOUTATIS", a=2.5119660, e=.6335854, I=0.46976, 
  g=274.82273, n=128.20968, M=50.00728, ep=2450600.5)
  
  solarSystem = PlanetarySystem(bodies=[mercury, venus, earthmoo, mars, jupiter, saturn, uranus, 
  neptune, pluto, apollo, jason, khufu, minos, orpheus, toutatis], m_star=1.0, epoch=2451000.5)
  
  bigin = Big(solarSystem)
  bigin.write()
  
  smallin = Small(solarSystem)
  smallin.write()
  
  elementin = Element(format_sortie=" a8.5 e8.6 i8.4 g8.4 n8.4 l8.4 m13e ", coord="Cen", 
  output_interval=365.2e1, time_format="years", relative_time="yes")
  elementin.write()
  
  closein = Close(time_format="years", relative_time="yes")
  closein.write()
  
  paramin = Param(algorithme=algorithm, start_time=2451179.5, stop_time=2462502.5, output_interval=365.25e0, 
  h=8, accuracy=1.e-12, stop_integration="no", collisions="no", fragmentation="no", 
  time_format="years", relative_time="no", output_precision="medium", relativity="no", 
  user_force="no", ejection_distance=100, radius_star=0.005, central_mass=1.0, 
  J2=0, J4=0, J6=0, changeover=3., data_dump=500, periodic_effect=100)
  paramin.write()
  
  Files().write()
  Message().write()

##################
# Outputs of various binaries and tests to compare with the actual ones. 
# Theses outputs are those of the original version of mercury, that is, mercury6_2.for
##################


os.chdir(NEW_TEST)
# We clean undesirable files beforehand, because we will copy if necessary the input simulation files to the other folder. 
clean()
os.chdir("..")

# We create folder and force old simulation generation if this is the first time we run the script
if not(os.path.isdir(PREVIOUS_TEST)):
  os.mkdir(PREVIOUS_TEST)
  force_source = True
  force_simulation = True

# We delete old files, get the desired revision of the code, and the corresponding simulation files, compile it and so on.
if force_source:
  print("Preparing old binaries ...")
  run("rm %s/*" % PREVIOUS_TEST) # Delete all files in the test directory
  
  # Copy the given revision REVISION in the required sub-folder (PREVIOUS_TEST)
  ## REVISION can either be a given commit, or HEAD, or READ^ and so on. Any commit ID available in Git.
  #> @Warning Problems for comparison can occurs if output files changes format between the two revisions.
  ## This script is intended to compare recent version of the code, when outputs changes are not expected. When outputs changes,
  ## one must be carefull with implementation and do the test themselves.
  get_revision = "git archive %s --format=tar --prefix=%s/ | tar xf -" % (REVISION, PREVIOUS_TEST)
  
  print(get_revision)
  run(get_revision)
  
  # We retrieve the commit ID from the possible alias stored in 'REVISION'
  (REVISION_ID, dummy, returnCode) = run("git rev-parse %s" % REVISION)
  (HEAD_ID, dummy, returnCode) = run("git rev-parse HEAD")
  
  os.chdir(PREVIOUS_TEST)
  
  # We store information about old commit used for comparison, in the corresponding folder.
  revision_file = open("revision.in", 'w')
  revision_file.write("Old revision: %s\n" % REVISION)
  revision_file.write("Old revision ID: %s\n" % REVISION_ID)
  revision_file.write("Current revision ID (HEAD): %s\n(but uncommitted changes might exists)\n" % HEAD_ID)
  revision_file.close()
  
  # Compilation of previous code
  previous_compilation = "Makefile.py test"
  print(previous_compilation)
  (stdout, stderr, returnCode) = run(previous_compilation)
  
  if (returnCode != 0):
    print(stdout)
    print(stderr)
  
  os.chdir("..")

for algo in ["BS", "BS2", "MVS", "RADAU", "HYBRID"]:
		
	print("##########################################")
	sys.stdout.write("Running new binaries with %s ...\r" % algo)
	sys.stdout.flush()
	os.chdir(NEW_TEST)

	clean() # Suppress previous temporary files

	initialising_input_objects(algorithm=algo)

	(merc_new__stdout, merc_new__stderr, returnCode) = run("../%s" % PROGRAM_NAME)

	# list are sorted to ensure we compare the right files between actual and original outputs
	OUTPUT_FILENAMES.sort()
	CLOSE_FILENAMES.sort()

	os.chdir("..")
	print("Running new binaries with %s ...ok" % algo)

	# We run the old version simulation
	print("##########################################")
	os.chdir(PREVIOUS_TEST)
	# Copy of simulation files
	copy_files = "cp ../%s/* ." % NEW_TEST
	print(copy_files)
	run(copy_files)

	clean() # Suppress previous temporary files
	sys.stdout.write("Running old binaries with %s ...\r" % algo)
	sys.stdout.flush()
	(merc_or_stdout, merc_or_stderr, returnCode) = run("./%s" % PROGRAM_NAME)
	print("Running old binaries with %s ...ok" % algo)
	print("##########################################")

	# Go back in parent directory (containing the current code and test script)
	os.chdir("..")

	# We make the comparison

	diff = ASCIICompare(merc_or_stdout, merc_new__stdout)
	if (diff != None):
	  print("\nTest of mercury")
	  print("\tFor the Output of mercury")
	  print diff

	# We create names including the folder in which they are
	CLOSE_FILENAMES_NEW = [os.path.join(NEW_TEST, filename) for filename in CLOSE_FILENAMES]
	OUTPUT_FILENAMES_NEW = [os.path.join(NEW_TEST, filename) for filename in OUTPUT_FILENAMES]

	# We create names including the folder in which they are
	CLOSE_FILENAMES_OLD = [os.path.join(PREVIOUS_TEST, filename) for filename in CLOSE_FILENAMES]
	OUTPUT_FILENAMES_OLD = [os.path.join(PREVIOUS_TEST, filename) for filename in OUTPUT_FILENAMES]

	print("comparing outputs:")
	compare2Binaries(OUTPUT_FILENAMES_OLD, OUTPUT_FILENAMES_NEW)

	print("comparing close encounters:")
	compare2Binaries(CLOSE_FILENAMES_OLD, CLOSE_FILENAMES_NEW)


	# We include the folder name because we are in the parent folder.
	ASCII_OLD = [os.path.join(PREVIOUS_TEST, filename) for filename in ASCII_FILES]
	ASCII_NEW = [os.path.join(NEW_TEST, filename) for filename in ASCII_FILES]

	#~ pdb.set_trace()
	print("comparing ASCII files (info.out,...)")
	compare2files(ASCII_OLD, ASCII_NEW)
	print("##########################################")
