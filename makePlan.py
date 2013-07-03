
import sys

args = sys.argv

# Number of sample plans to take in attempt to reduce number of keys to farm
TRIES = 12

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
                        latE6 and lngE6 should be the portal's global coordinates
                        E6 means times 10^6 (no decimal)
                            e.g. the Big Ben portal is at 51500775,-124466
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

import networkx as nx
from lib import maxfield,PlanPrinter,geometry
np = geometry.np
import pickle

if len(args) < 4:
    output_directory = ''
else:
    output_directory = args[3]
    if output_directory[-1] != '/':
        output_directory += '/'

if len(args) < 5:
    output_file = 'lastPlan.pkl'
else:
    output_file = args[4]

    if not output_file[-3:] == 'pkl':
        print 'WARNING: output file should end in "pkl" or you cannot use it as input later'

nagents = int(args[1])
if nagents < 0:
    print 'Numer of agents should be positive'
    exit()

input_file = args[2]

if input_file[-3:] != 'pkl':
    a = nx.DiGraph()

    locs = []

    i = 0
    # each line should be id,name,lat,long,keys
    with open(input_file,'r') as fin:
        for line in fin:
            if line[0] == '%':
                break
            parts = line.split(',')
            
            a.add_node(i)
            a.node[i]['name'] = parts[0]

            locs.append( np.array(parts[1:3],dtype=int) )

            if len(parts) < 4:
                a.node[i]['keys'] = 0
            else:
                a.node[i]['keys'] = int(parts[3])
            
            i += 1

    n = a.order() # number of nodes

    locs = np.array(locs,dtype=float)

    # This part assumes we're working with E6 latitude-longitude data
    locs = geometry.e6LLtoRads(locs)
    xyz  = geometry.radstoxyz(locs)
    xy   = geometry.gnomonicProj(locs,xyz)

    for i in xrange(n):
        a.node[i]['geo'] = locs[i]
        a.node[i]['xyz'] = xyz [i]
        a.node[i]['xy' ] = xy  [i]

    # Make TRIES attempts to get graph with few missing keys
    # Try to minimuze TK + 2*MK where
    #   TK is the total number of missing keys
    #   MK is the maximum number of missing keys for any single portal
    bestgraph = None
    bestlack = np.inf

    for i in range(TRIES):
        b = a.copy()

        if not maxfield.maxFields(b):
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
            bestgraph = b
            bestlack  = weightedlack

        if weightedlack == 0:
            break

    if bestgraph == None:
        print 'EXITING RANDOMIZATION LOOP WITHOUT SOLUTION!'
        exit()

    a = bestgraph

    # Attach to each edge a list of fields that it completes
    for t in a.triangulation:
        t.markEdgesWithFields()

    with open(output_directory+output_file,'w') as fout:
        pickle.dump(a,fout)
else:
    with open(input_file,'r') as fin:
        a = pickle.load(fin)

PP = PlanPrinter.PlanPrinter(a,output_directory,nagents)
#PP.keyPrep()
#PP.agentKeys()
#PP.planMap()
#PP.agentLinks()
#PP.animate()
PP.instruct()

