#! /usr/bin/env python
"""
Usage:
  makePlan.py [-b] [-n <agent_count>] <input_file> [<output_directory>] [<output_file>]

Description:
  This is for Ingress. If you don't know what that is, you're lost.

  input_file:
      One of two types of files:

      - .csv formatted as portal name,lat,lng,keys

          portal name should not contain commas
          lat and lng should be the portal's global coordinates
              e.g. the Big Ben portal is at 51.500775,-0.124466
          keys is the number of keys you have for the portal

      - .pkl an output from a previous run of this program

          this can be used to make the same plan with a different number of agents

  output_directory:
      directory in which to put all output (default is the working directory)

  output_file:
      name for a .pkl file containing information on the plan

      if you use this for the input file, the same plan will be produced with the
      number of agents you specify (default: "lastPlan.pkl")

Options:
  -b         Make maps blue instead of green
  -n agents  Number of agents [default: 1]

"""

import re
import sys
from docopt import docopt
import networkx as nx
from lib import maxfield,PlanPrinter,geometry,agentOrder
import pickle

args = sys.argv


# We could take many samples in an attempt to reduce number of keys to farm
# This is the number of samples to take since the last improvement
EXTRA_SAMPLES = 1

if len(args) < 3:
    print '''
    -----Introduction-----

    This is for Ingress. If you don't know what that is, you're lost.

    -----Usage-----

    >> python makePlan.py agent_count input_file [output_directory] [output_file]
    
    agent_count: Number of agents for which to make a plan
    
    input_file:  One of two types of files:
                   .csv formatted as portal name,latE6,lngE6,keys
                        
                        portal name should not contain commas
                        lat and lng should be the portal's global coordinates
                            e.g. the Big Ben portal is at 51.500775,-0.124466
                        keys is the number of keys you have for the portal
                   
                   .pkl an output from a previous run of this program
                        this can be used to make the same plan with a different number of agents

    output_directory: directory in which to put all output
                      default is the working directory

    output_file: name for a .pkl file containing information on the plan
                 if you use this for the input file, the same plan will be produced with the number of agents you specify
                 default: "lastPlan.pkl"
    '''
    exit()

def main():
    args = docopt(__doc__)

    np = geometry.np

    #GREEN = 'g'
    #BLUE  = 'b'
    GREEN = '#3BF256' # Actual faction text colors in the app
    BLUE  = '#2ABBFF'
    #GREEN = (0.0 , 1.0 , 0.0 , 0.3)
    #BLUE  = (0.0 , 0.0 , 1.0 , 0.3)
    COLOR = GREEN

    if args['-b']:
        COLOR = BLUE

    output_directory = ''
    if args['<output_directory>'] != None:
        output_directory = args['<output_directory>']
        if output_directory[-1] != '/':
            output_directory += '/'

    output_file = 'lastPlan.pkl'
    if args['<output_file>'] != None:
        output_file = args['<output_file>']
        if not output_file[-3:] == 'pkl':
            print 'WARNING: output file should end in "pkl" or you cannot use it as input later'

    nagents = int(args['-n'])
    if nagents <= 0:
        print 'Numer of agents should be positive'
        exit()

    input_file = args['<input_file>']

    if input_file[-3:] != 'pkl':
        a = nx.DiGraph()

        locs = []
        #                             ------------- URL -------------
        #                      name  ;       lat      ,  lng         ;     keys
        urlpat = re.compile('^([^;]*);.*ll=([-0-9\.]+),([-0-9\.]+)\s*;?\s*(\d+)?')
        #                      name  ;     lat         ;     lng         ;     keys
        cvspat = re.compile('^([^;]*);\s*([-0-9\.]+)\s*;\s*([-0-9\.]+)\s*;?\s*(\d+)?')
        i = 0
        # each line should be id,name,lat,long,keys
        with open(input_file,'r') as fin:
            for line in fin:
                m = urlpat.match(line)
                if m == None:
                    m = cvspat.match(line)
                if m == None:
                # TODO allow other line formats
                    break
                g = m.groups()
#                print g

                a.add_node(i)
                a.node[i]['name'] = g[0]

                locs.append( np.array([float(g[1]),float(g[2])] ))

                if g[3] == None:
                    a.node[i]['keys'] = 0
                else:
                    a.node[i]['keys'] = int(g[3])

                i += 1

        n = a.order() # number of nodes

        locs = np.array(locs,dtype=float)
#        print locs

        # This part assumes we're working with decimal latitude-longitude data
        locs = geometry.LLtoRads(locs)
        xyz  = geometry.radstoxyz(locs)
        xy   = geometry.gnomonicProj(locs,xyz)

        for i in xrange(n):
            a.node[i]['geo'] = locs[i]
            a.node[i]['xyz'] = xyz [i]
            a.node[i]['xy' ] = xy  [i]
            
        maxfield.maxFields(a)

        '''
        # EXTRA_SAMPLES attempts to get graph with few missing keys
        # Try to minimuze TK + 2*MK where
        #  TK is the total number of missing keys
        #   MK is the maximum number of missing keys for any single portal
        bestgraph = None
        bestlack = np.inf
        bestTK = np.inf
        bestMK = np.inf

        sinceImprove = 0

        while sinceImprove<EXTRA_SAMPLES:
            b = a.copy()

            sinceImprove += 1

            if not maxfield.maxFields(b):
                print 'Randomization failure\nThe program may work if you try again. It is more likely to work if you remove some protals.'
                continue

            TK = 0
            MK = 0
            for j in xrange(n):
                keylack = max(b.in_degree(j)-b.node[j]['keys'],0)
                TK += keylack
                if keylack > MK:
                    MK = keylack
            
            weightedlack = TK+2*MK

            if weightedlack < bestlack:
                sinceImprove = 0
                print 'IMPROVEMENT:\n\ttotal: %s\n\tmax:   %s\n\tweighted: %s'%\
                       (TK,MK,weightedlack)
                bestgraph = b
                bestlack  = weightedlack
                bestTK  = TK
                bestMK  = MK
            else:
                print 'this time:\n\ttotal: %s\n\tmax:   %s\n\tweighted: %s'%\
                       (TK,MK,weightedlack)

            if weightedlack == 0:
                print 'KEY PERFECTION'
                bestlack  = weightedlack
                bestTK  = TK
                bestMK  = MK
                break

#            if all([ b.node[i]['keys'] <= b.out_degree(i) for i in xrange(n) ]):
#                print 'All keys used. Improvement impossible'
#                break
#            print '%s tries since improvement'%sinceImprove

        if bestgraph == None:
            print 'EXITING RANDOMIZATION LOOP WITHOUT SOLUTION!'
            print ''
            exit()

        print 'Choosing plan requiring %s additional keys, max of %s from single portal'%(bestTK,bestMK)

        a = bestgraph
        '''

        # Attach to each edge a list of fields that it completes
        for t in a.triangulation:
            t.markEdgesWithFields()

        agentOrder.improveEdgeOrder(a)

        with open(output_directory+output_file,'w') as fout:
            pickle.dump(a,fout)
    else:
        with open(input_file,'r') as fin:
            a = pickle.load(fin)
    #    agentOrder.improveEdgeOrder(a)
    #    with open(output_directory+output_file,'w') as fout:
    #        pickle.dump(a,fout)

    PP = PlanPrinter.PlanPrinter(a,output_directory,nagents,COLOR)
    PP.keyPrep()
    PP.agentKeys()
    PP.planMap()
    PP.agentLinks()

    # These make step-by-step instructional images
    #PP.animate()
    #PP.split3instruct()

if __name__ == "__main__":
    sys.exit(main())

