
import geometry
np = geometry.np

# Number of meters one could walk in the time it takes to make a link
linkTime = 20

def getAgentOrder(a,nagents,orderedEdges):
    '''
    a is a digraph
        node have 'pos' property with location
    nagents is the number of agents
    orderedEdges maps i to the ith edge to be made

    this greedily minimizes wait time (equating distance with time)
    '''
    m = len(orderedEdges)

    # movements[i][j] will be the index (in orderedEdges) of the jth edge that agent i should make
    movements = dict([ (i,[]) for i in range(nagents) ])

    # The ammount of time that has elapsed
    curtime = 0.

    # Last time at which the agents made links
    lastActTime = np.zeros(nagents)
    
    # agent locations
    agentpos = np.empty([nagents,2])

    # Find initial deployments: starts[i] is the agent who starts at node i
    starts = {}
    assigning = 0

    e=0
    for e in xrange(m):
        p = orderedEdges[e][0]
        if not p in starts:
            # Nobody is at this link's head yet
            movements[assigning].append(e)
            starts[p] = assigning
            
            agentpos[assigning] = a.node[p]['geo']

            assigning += 1
            if assigning >= nagents:
                break
        else:
            # the agent who is already at this link's head should make it
            movements[starts[p]].append(e)

    # No agents have actually moved yet

    # continue from startup loop
    for e in xrange(e+1,m):
        p,q = orderedEdges[e]
        ppos = a.node[p]['geo']

        dists = geometry.sphereDist(agentpos,ppos)
        radii = curtime-lastActTime # how far could they have moved
        waits = dists-radii # how long will the team wait if this agent moves
        waits[waits<0] = 0 # no time travel

        mover = np.argmin(waits)
        movements[mover].append(e)

        agentpos[mover] = ppos
        curtime += waits[mover] + linkTime
        lastActTime[mover] = curtime
    
    return movements

def improveEdgeOrder(a):
    '''
    Edges that do not complete any fields can be made earlier
    This method alters the graph a such that
        The relative of edges that complete fields is unchanged
        Edges that do not complete fields may only be completed earlier
        Where possible, non-completing edges are made immediately after another edge with same origin
    '''
    # TODO
    return

