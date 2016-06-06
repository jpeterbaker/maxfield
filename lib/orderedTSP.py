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
from sys import stdout
import branch_bound
np = branch_bound.np

MAX_BRANCHES = 15000

# This could be used if more splits are wanted than are possible
infState = branch_bound.InfState()

class OTSPstate:
    def __init__(self,d,order,nagents,visit2agent=[0],time=[0.],lastat=None,):
        '''
        d: distance matrix
        order: order in which nodes must be visited
        time: time at which the nodes were visited
        lastat[i,j]: the node where agent j most recently was at time[i]
        nagents: number of agents
        visit2agent[i] is the agent who makes visit i
        '''

        # This is the root
        if lastat is None:
            self.n = d.shape[0]

            lastat = [[None]*nagents]
            lastat[0][0] = 0

            # Make a "start location" that is at distance 0 from everywhere
            # Using index -1 for undeployed agents puts them at this "start"
        else:
            # "start" location has already been added but doesn't count
            self.n = d.shape[0] - 1

        self.d = d

        self.lastat = lastat

        self.order = order
        self.nagents = nagents
        self.visit2agent = visit2agent
        self.time = time
        self.m = len(time) # numer of visits that have already been made

        self.value = self.time[-1]

    def agentsNewTime(self,agent):
        # The time at which this agent could make the next visit
        
        # The index of the last visit this agent made
        lastvisit = self.lastat[-1][agent]

#        print len(self.time)
#        print self.d.shape
#        print 'agent',agent
#        print '  lastvisit',lastvisit

        # Assume agent's initial deployment is instantaneous
        if lastvisit is None:
            return self.time[-1]

        # The node at which agent made his last visit
        lastpos   = self.order[lastvisit]
        # The time at which agent was at lastpos
        lasttime  = self.time[lastvisit]
        # The node that needs to be visited next
        nextpos = self.order[self.m]

#        print '  lastat',self.lastat
#        print '  lastpos',lastpos
#        print '  lasttime',lasttime
#        print '  nextpos',nextpos

        t = max( self.time[-1] , lasttime + self.d[nextpos,lastpos] )
#        print '  t',t
        return t

        # He makes it either at the same time as the previous visit or as soon as he arrives at nextpos
        return max( self.time[-1] , lasttime + self.d[nextpos,lastpos] )

    def split(self,num):
        '''
        num: number of child states to produce
            (in the easiest case, this is the same as nagents)

        returns list of possible next states
        '''
#        print self.m,len(self.order)
        if self.m >= len(self.order):
            raise branch_bound.CantSplit()

        children = []
        for agent in range(self.nagents):
            newtime = self.agentsNewTime(agent)
            
            # Everyone's last known position is the same, except that agent is now at m
            newlast = list(self.lastat[-1])
            newlast[agent] = self.m

            try:

                children.append(OTSPstate(self.d,self.order,self.nagents,\
                                     self.visit2agent+[agent],\
                                     self.time+[newtime],\
                                     self.lastat+[newlast],\
                                    ))
            except TypeError as e:
                print self.visit2agent
                exit()
                
        if num < self.nagents:
            childorder = np.argsort([ child.value for child in children ])
            children = np.array(children)
            children = children[childorder[:num]]

        return children

    def calcTimes(self):
        '''
        Calculates self.time and self.lastat
            Uses data from self.d and self.visit2agent
        Assumes self.time[0] should be 0
        self.time and self.lastat are overwritten
        '''
        nvisits = len(self.order)

        # These could be pre-allocated if agentsNewTime didn't use negativ index

        # Same initialization as in __init__
        self.time        = [0.]
        self.m           = 1
        # Agent 0 makes visit 0
        self.lastat = [ [0]+[None]*(self.nagents-1) ]

        for i in xrange(1,nvisits):
            agent = self.visit2agent[i]

            t = self.agentsNewTime(agent)

            self.time.append(t)
            self.m += 1

            # Everyone has same position except for agent
            self.lastat.append(list(self.lastat[-1]))
            self.lastat[-1][agent] = i
            
        self.value = self.time[-1]
        return self.value


def getVisits(dists,order,nagents):
    '''
    dists:   a distance matrix
    order:   the order in which nodes must be visited
             duplicates allowed
    nagents: the number of agents available to make the visits
             
    returns visits,time
              visits[i] = j means the ith visit should be performed by agent j
              time[i] is the number of meters a person could have walked walk since the start when visit i is made 
    '''

    # This callback prints the number of iterations
    print 'Planning',len(order),'agent movements:'
    c = [0]
    def cb():
        c[0] += 1
        print c[0],
        stdout.flush()

    root = OTSPstate(dists,order,nagents)
    LO = MAX_BRANCHES // nagents
    state,value = branch_bound.branch_bound(root, LO , LO*nagents , cb)

    return state.visit2agent,state.time

if __name__=='__main__':
    import geometry
#    pts = np.array([[0,0],\
#                    [0,1],\
#                    [0,5]])
#    order = [0,2,1]
#    pts = np.array([[0,0],\
#                    [0,1],\
#                    [0,2],\
#                    [0,3],\
#                    [0,5]])
#    order = [0,4,1,2,3]
    pts = np.array([[0,0],\
                    [3,0],\
                    [4,0],\
                    [7,0]])
    order       = [0,2,1,3]
    visit2agent = [0,0,0,0]

    d = geometry.planeDist(pts,pts)

#    print getVisits(d,order,2)

    state = OTSPstate(d,order,2,visit2agent)
#    print state.calcTimes()

