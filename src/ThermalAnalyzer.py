import numpy as np
import sys
import argparse
import logging
from PreprocessGDS import PreprocessGDS
from Visualizer import Visualizer
from ThermalSolver import ThermalSolver 
from pathlib import Path
from matplotlib import pyplot as plt

class ThermalAnalyzer:
  def __init__(self):
    self.preprocessGds = PreprocessGDS()
    self.visualizer = Visualizer()
    self.simulator = ThermalSolver()

  def run(self,):
    self.parseInputArguments()
    if self.args.AnalysisMode== 'preprocessGDS':
      self.PreprocessGdsOptions()
        
    elif self.args.AnalysisMode== 'simulate':
      self.SimulateOptions()
    elif self.args.AnalysisMode== 'visualize':
      self.VisualizeOptions()

  
  def PreprocessGdsOptions(self):
    if self.args.jsonFile is not None:
      self.modeJsonPreprocess()
    elif self.args.gdsFile is not None:
      self.modeGdsPreprocess()
    else:
      self.logger.critical("Undefined state for Prepocessign GDS.")
  
  def VisualizeOptions(self):
    if self.args.npzFile is not None:
      if self.args.R is None:
        self.parserVisualize.error("--resolution is a required argument with --emissivity")
        return 
      self.visualizer.visualizeEmmissivity(self.args.npzFile, self.args.R)
    if (self.args.lvt is not None or 
        self.args.lvh is not None or
        self.args.lvw is not None ):
      if self.args.solFile is None:
        self.parserVisualize.error('''--solution is a required argument with -lvt,
                                      -lvh, -lvw''')
        return
      if not self.args.solFile.is_file():
       self.logger.error('''Solution file does not exist, please provide a valid
                           file to --solution''')
       return
      self.visualizer.loadSolutionFile(self.args.solFile, self.args.outDir)
      if self.args.lvw:
        self.visualizer.visualizeLvW(self.args.t_point)
      if self.args.lvh:
        self.visualizer.visualizeLvH(self.args.t_point)
      if self.args.lvt:
        self.visualizer.visualizeLvT()
    plt.show()


  def SimulateOptions(self):
    self.logger.debug("t_max %e"%self.args.t_max)
    self.logger.debug("t_step %e"%self.args.t_step)
    self.logger.debug("pw_lamp %e"%self.args.pw_lamp)
    if self.args.npzFile is not None:
      self.simulator.build(self.args.npzFile, self.args.R, self.args.outDir)  
    elif self.args.test is not None:
      self.simulator.buildTest(self.args.test, self.args.R, self.args.outDir)  
    self.simulator.runSolver(self.args.t_max, self.args.t_step, self.args.pw_lamp)
      
  def modeJsonPreprocess(self):
    self.logger.critical("Reading from JSON is not yet implmented.")
    #outDir = self.args.outDir
    #jsonFile = self.args.jsonFile
    #self.preprocessGds.createNpzFromJson( jsonFile, outDir)


  def modeGdsPreprocess(self):
    outDir = self.args.outDir
    gdsFile = self.args.gdsFile
    self.preprocessGds.createNpzFromGDS( gdsFile, outDir)

    
    
  def create_logger(self, log_file=None,severity=None):
    # Create a custom logger
    logging.addLevelName(25,'STATUS')
    logger = logging.getLogger('TAZ')
    # Create handlers
    c_handler = logging.StreamHandler()
    if severity is None:
      logger.setLevel('STATUS')
      c_handler.setLevel('STATUS')
    else:
      logger.setLevel(severity)
      c_handler.setLevel(severity)
    # Create formatters and add it to handlers
    c_format = logging.Formatter('[%(name)s][%(levelname)s] %(message)s')
    c_handler.setFormatter(c_format)
    
    # Add handlers to the logger
    logger.addHandler(c_handler)
    # handle log file
    if log_file is not None:
      f_handler = logging.FileHandler(str(log_file.absolute()))
      if severity is None:
        f_handler.setLevel('INFO')
      else:
        f_handler.setLevel(severity)
      f_format = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s][%(message)s]')
      f_handler.setFormatter(f_format)
      logger.addHandler(f_handler)
    return logger

  def parseInputArguments(self):
    parser = argparse.ArgumentParser(prog = "ThermalAnalyzer",
              description = '''Thermal simulation and analysis for rapid 
                               thermal anealing (RTA).''')
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true",
              help = "Enables verbose mode with detailed information.")
    group.add_argument("-q", "--quiet", action="store_true",
              help = '''Supresses all informational messages and only
                        displays warnings and errors.''')
    group.add_argument("-d", "--debug", action="store_true",
              help = '''Displays additional debug messages for 
                        software debug. Warning: This can lead to 
                        significant increase in messages.''')
    parser.add_argument("-l", "--log_file", type=Path,
              help = "Log file for run.",dest='log')
    parser.set_defaults(func=lambda : parser.print_help())                        
    subparsers = parser.add_subparsers(
              title = "ThermalAnalyzer subcommands and analysis modes.",
              description="List of available modes for %(prog)s", 
              help=''' 
              For additional information of each subcommand run 
              %(prog)s <subcommand> --help''',
              dest='AnalysisMode')
    subparsers.required = True
    parserSim = subparsers.add_parser("simulate", 
              description="Thermal simualation mode",
              help=''' Setup the tool in thermal simulation mode to run analysis
              on the provided GDS.
              ''')
    group_sim = parserSim.add_mutually_exclusive_group(required=True)
    group_sim.add_argument("-g","--preprocessedGDS", type=Path, dest='npzFile',
                              help = '''Path to the preprocessed NPZ file for
                                        simulation ''')
    group_sim.add_argument("-t","--testcase",type=int,dest='test',
                            choices=[1,2,3], help =''' Run predefined
                            testcases''')
    parserSim.add_argument("-r","--resolution", type=int, dest='R', required=True,
                              help = ''' Lateral resolution in um (int) for simulation''')
    parserSim.add_argument("-tm","--time_max", type=float, dest='t_max', required=True,
                              help = ''' Maximum time for the simulation''')
    parserSim.add_argument("-ts","--time_step", type=float, dest='t_step', required=True,
                              help = ''' Time step resolution for the simulation''')
    parserSim.add_argument("-tp","--time_pulse", type=float, dest='pw_lamp', required=True,
                              help = ''' Time duration of the lamp pulse for the simulation''')
    parserSim.add_argument("-o",'--outDir', type=Path, dest='outDir',
                              help = ''' Destination directory for output
                              solution files. The command will create the directory
                              if it does not exists''')

    #### Visualize options
    parserVisualize = subparsers.add_parser("visualize", 
              description="GDS visualizetion",
              help=''' Set of suboptions for visualizing the inputs/outputs ''')
    group_emmis = parserVisualize.add_argument_group('Emmissivty',
                          'Necessary arguments to generate emissivity plots')
    group_emmis.add_argument("-e","--emissivity", type=Path, dest='npzFile',
                              help = '''Path to the preprocessed NPZ file for
                                        emissivty plot''')
    group_emmis.add_argument("-r","--resolution", type=int, dest='R',
                              help = '''Resolution in um (int) for emissivity plot''')
    parserVisualize.add_argument('-o','--outDir', type=Path, dest='outDir',
              help = '''Destination directory to store the figure. The command
              will create the directory if it does not exists''')
    group_temp = parserVisualize.add_argument_group('Temperature plots',
                          'Necessary arguments to generate temperature plots')
    group_temp.add_argument("-t","--time_point", type=float, dest='t_point',
                              help = '''Time point at which to plot the result''')
    group_temp.add_argument("-lvw","--lenVwidth", action="store_true",
                              dest='lvw', help = '''Plot length vs width for the 
                              provided time point''')
    group_temp.add_argument("-lvt","--lenVtime", action="store_true",
                              dest='lvt', help = '''Plot length vs time for the
                              along the center of the design''')
    group_temp.add_argument("-lvh","--lenVheight", action="store_true",
                              dest='lvh', help = '''Plot length vs height for the 
                              provided time point along the center of the design''')
    group_temp.add_argument("-s","--solution", type=Path, dest='solFile',
                              help = '''Path to the generated solution file from
                              simulate''')


    #### preprocess GDS options
    parserGdsPreprocess = subparsers.add_parser("preprocessGDS", 
              description="GDS pre-processing ",
              help=''' Preprocess the GDSII/JSON file to a
              preprocessed NPZ file that can be used by the other subcommands ''')
    group_preproc = parserGdsPreprocess.add_mutually_exclusive_group(required=True)
    group_preproc.add_argument("-j", "--json", type=Path, dest='jsonFile',
              help = "Load GDS information from a JSON file.")
    group_preproc.add_argument("-g", "--gds",  type=Path, dest='gdsFile',
              help = 'Load GDS information from a GDSII file.')
    parserGdsPreprocess.add_argument('-o','--outDir', type=Path,
              dest='outDir', required=True,
              help = '''Destination directory for output NPZ files. The command
              will create the directory if it does not exists''')
    self.parser = parser
    self.parserVisualize = parserVisualize
    self.parserGdsPreprocess = parserGdsPreprocess
    args = parser.parse_args()
    if args.verbose:
      severity = 'INFO'
    elif args.quiet:
      severity = 'WARNING'
    elif args.debug:
      severity = 'DEBUG'

    else:
      severity = None
    self.logger = self.create_logger( log_file = args.log,
                                      severity = severity)
    self.args = args

if __name__ == "__main__":
  therm_anlyzr = ThermalAnalyzer()
  therm_anlyzr.run()
