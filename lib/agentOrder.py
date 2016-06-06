'''
This file is part of Maxfield.
Maxfield is a planning tool for helping Ingress players to determine
an efficient plan to create many in-game fields.

Copyright (C) 2015 by Jonathan Baker: babamots@gmail.com


Maxfield is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Maxfield is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Maxfield.  If not, see <http://www.gnu.org/licenses/>.
'''
import geometry
np = geometry.np

import orderedTSP

# Walking speed in m/s
WALKSPEED = 2

# Seconds it takes to communicate link completion
# An agent should report their consecutive links simultaneously
COMMTIME = 60

# Seconds to create a link
LINKTIME = 15

## DEPRECIATED ##
def getGreedyAgentOrder_DONT_USE_THIS_FUNCTION(a,nagents,orderedEdges):
    '''
    a is a digraph
        node have 'pos' property with location
    nagents is the number of agents
    orderedEdges maps i to the ith edge to be made

    this greedily minimizes wait time (equating distance with time)
    the player who has the most time to spare is assigned the link
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

def condenseOrder(order):
    '''
    order is a list of integers
    returns (s,mult)
        where
    mult[i] is the multiplicity of a sequence of repeated s[i]'s in order

    EXAMPLE:
        condenseOrder( [0,5,5,5,2,2,3,0] )
            returns
        ( [0,5,2,3,0] , [1,3,2,1,1] )
    '''
    s = []
    mult = []

    cur = order[0]
    count = 0
    for i in order:
        if i == cur:
            # Count the cur's in a row
            count += 1
        else:
            # Add cur and its count to the lists
            s.append(cur)
            mult.append(count)

            # Start counting the new entry
            cur   = i
            count = 1

    # The last sequence never entered the else
    s.append(cur)
    mult.append(count)

    return s,mult

def expandOrder(s,mult):
    '''
    returns a list with s[i] appearing multi[i] times (in place)

    This is the inverse of condenseOrder

    EXAMPLE:
        expandOrder( [0,5,2,3,0] , [1,3,2,1,1] )
            returns
        [0,5,5,5,2,2,3,0]
        
    '''
    m = len(s)
    n = sum(mult)
    order = [None]*n

    writeat = 0
    for i in xrange(m):
        count = mult[i]
        # Put in count occurences of s[i]
        order[writeat:writeat+count] = [s[i]]*count
        writeat += count

    return order

def getAgentOrder(a,nagents,orderedEdges):
    '''
    returns visits
    visits[i] = j means agent j should make edge i
    
    ALSO creates time attributes in a:
        
    Time that must be spent just walking
        a.walktime
    Time it takes to communicate completion of a sequence of links
        a.commtime
    Time spent navigating linking menu
        a.linktime
    '''
    geo = np.array([ a.node[i]['geo'] for i in xrange(a.order())])
    d = geometry.sphereDist(geo,geo)
#    print d
    order = [e[0] for e in orderedEdges]

    # Reduce sequences of links made from same portal to single entry
    condensed , mult = condenseOrder(order)

    link2agent , times = orderedTSP.getVisits(d,condensed,nagents)

    # Expand links made from same portal to original count
    link2agent = expandOrder(link2agent,mult)

    # If agents communicate sequential completions all at once, we avoid waiting for multiple messages
    # To find out how many communications will be sent, we count the number of same-agent link sequences
    condensed , mult = condenseOrder(link2agent)
    numCOMMs = len(condensed)

    # Time that must be spent just walking
    a.walktime = times[-1]/WALKSPEED
    # Waiting for link completion messages to be sent
    a.commtime = numCOMMs*COMMTIME
    # Time spent navigating linking menu
    a.linktime = a.size()*LINKTIME

    movements = [None]*nagents

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
    order = [0,5,5,5,2,2,1,0]
#    order = [5]*5
    s,mult = condenseOrder(order)
    print s
    print mult
    print order
    print expandOrder(s,mult)
'''
== Jonathan: maxfield $ python makePlan.py 4 almere/lastPlan.pkl almere/
Total time: 1357.37352334
== Jonathan: maxfield $ python makePlan.py 5 almere/lastPlan.pkl almere/
Total time: 995.599917771
== Jonathan: maxfield $ python makePlan.py 6 almere/lastPlan.pkl almere/
Total time: 890.389138077
== Jonathan: maxfield $ python makePlan.py 7 almere/lastPlan.pkl almere/
Total time: 764.127789228
== Jonathan: maxfield $ python makePlan.py 8 almere/lastPlan.pkl almere/
Total time: 770.827639967
'''
