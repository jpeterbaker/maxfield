
import geometry
np = geometry.np

import orderedTSP

# Number of meters one could walk in the time it takes to make a link
# This is ignored by branch-and-bound
#linkTime = 5
#
#def getGreedyAgentOrder(a,nagents,orderedEdges):
#    '''
#    a is a digraph
#        node have 'pos' property with location
#    nagents is the number of agents
#    orderedEdges maps i to the ith edge to be made
#
#    this greedily minimizes wait time (equating distance with time)
#    the player who has the most time to spare is assigned the link
#
#     THIS FUNCTION IS NOT AS GOOD AS BRANCH-AND-BOUND
#    '''
#    m = len(orderedEdges)
#
#    # movements[i][j] will be the index (in orderedEdges) of the jth edge that agent i should make
#    movements = dict([ (i,[]) for i in range(nagents) ])
#
#    # The ammount of time that has elapsed
#    curtime = 0.
#
#    # Last time at which the agents made links
#    lastActTime = np.zeros(nagents)
#    
#    # agent locations
#    agentpos = np.empty([nagents,2])
#
#    # Find initial deployments: starts[i] is the agent who starts at node i
#    starts = {}
#    assigning = 0
#
#    e=0
#    for e in xrange(m):
#        p = orderedEdges[e][0]
#        if not p in starts:
#            # Nobody is at this link's head yet
#            movements[assigning].append(e)
#            starts[p] = assigning
#            
#            agentpos[assigning] = a.node[p]['geo']
#
#            assigning += 1
#            if assigning >= nagents:
#                break
#        else:
#            # the agent who is already at this link's head should make it
#            movements[starts[p]].append(e)
#
#    # No agents have actually moved yet
#
#    # continue from startup loop
#    for e in xrange(e+1,m):
#        p,q = orderedEdges[e]
#        ppos = a.node[p]['geo']
#
#        dists = geometry.sphereDist(agentpos,ppos)
#        radii = curtime-lastActTime # how far could they have moved
#        waits = dists-radii # how long will the team wait if this agent moves
#        waits[waits<0] = 0 # no time travel
#
#        mover = np.argmin(waits)
#        movements[mover].append(e)
#
#        agentpos[mover] = ppos
#        curtime += waits[mover] + linkTime
#        lastActTime[mover] = curtime
#    
#    return movements

def getAgentOrder(a,nagents,orderedEdges):
    '''
    returns visits
    visits[i] = j means agent j should make edge i
    '''
    geo = np.array([ a.node[i]['geo'] for i in xrange(a.order())])
    d = geometry.sphereDist(geo,geo)
#    print d
    order = [e[0] for e in orderedEdges]
    link2agent , times = orderedTSP.getVisits(d,order,nagents)

    print 'Plan can be completed in time it takes one agent to walk',times[-1],'meters'

    movements = [None]*nagents

    # I realize that switching between these formats all the time is stupid
    # Consistency hasn't been my highest priority
    for i in xrange(len(link2agent)):
        try:    
            movements[link2agent[i]].append(i)
        except:
            movements[link2agent[i]] = [i]

    return movements

#    m = a.size()
#
#    # link2agent[j] is the agent who makes link j
#    link2agent = [-1]*m
#    for i in range(nagents):
#        for j in movements[i]:
#            link2agent[j] = i
#
#    bestT = completionTime(a,movements)
#
#    sinceImprove = 0
#    i=0
#    while sinceImprove < m:
#        agent = link2agent[i]
#        
#        # for each of the other agents
#        for alt in range(agent-nagents+1,agent):
#
#            alt %= nagents
#            # see what happens if agent 'alt' makes the link
#            link2agent[i] = alt
#
#            T = completionTime(a,link2agent)
#
#            if T < bestT:
#                bestT = T
#                sinceImprove = 0
#                break
#        else:
#            # The loop exited normally, so no improvement was found
#            link2agent[i] = agent # restore the original plan
#            sinceImprove += 1
#
#        i = (i+1)%m
#
#    return movements
#
#
def improveEdgeOrder(a):
    '''
    Edges that do not complete any fields can be made earlier
    This method alters the graph a such that
        The relative order of edges that complete fields is unchanged
        Edges that do not complete fields may only be completed earlier
        Where possible, non-completing edges are made immediately before another edge with same origin
    '''
    m = a.size()
    # If link i is e then orderedEdges[i]=e
    orderedEdges = [-1]*m

    for p,q in a.edges_iter():
        orderedEdges[a.edge[p][q]['order']] = (p,q)

    for j in xrange(1,m):
        p,q = orderedEdges[j]
        # Only move those that don't complete fields
        if len(a.edge[p][q]['fields']) > 0:
            continue

#        print j,p,q,a.edge[p][q]['fields']

        origin = orderedEdges[j][0]
        # The first time this portal is used as an origin
        i = 0
        while orderedEdges[i][0]!=origin:
            i+=1

        if i<j:
#            print 'moving %s before %s'%(orderedEdges[j],orderedEdges[i])
            # Move link j to be just before link i
            orderedEdges =  orderedEdges[   :i] +\
                           [orderedEdges[  j  ]]+\
                            orderedEdges[i  :j] +\
                            orderedEdges[j+1: ]
        #TODO else: choose the closest earlier portal
    
#    print 
    for i in xrange(m):
        p,q = orderedEdges[i]
#        print p,q,a.edge[p][q]['fields']
        a.edge[p][q]['order'] = i
#    print

if __name__=='__main__':
    pass
