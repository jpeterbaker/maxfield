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
from Triangle import Triangle,Deadend

'''
Some things are chosen randomly:
    Each triangle's splitting portal
    Each triangle's "final node" (unless determined by parent)
This is the number of times to randomly rebuild each first generation triangle while attempting to get it right
'''
TRIES_PER_TRI = 1

def canFlip(degrees,keylacks,p,q):
    '''
    True iff reversing edge p,q is a paraeto improvement
        out-degree of q must be <8
        p must have a key surplus
    '''
    return (degrees[q,1] < 8) & (keylacks[p]<0)

def flip(a,p,q,degrees=None,keylacks=None):
    if not a.edge[p][q]['reversible']:
        print '!!!! Trying to reverse a non-reversible edge !!!!'
        print p,q
    # Give the reversed edge the same properties
    a.add_edge(q,p,a.edge[p][q])
    a.remove_edge(p,q)
    if degrees != None:
        degrees[p,0] += 1
        degrees[p,1] -= 1
        degrees[q,0] -= 1
        degrees[q,1] += 1

    if keylacks != None:
        keylacks[p] += 1
        keylacks[q] -= 1

def flipSome(a):
    '''
    Tries to make each in and out degree of a <=8 by reversing edges
    Only edges with the property reversible=True will be flipped
    Secondarily, tries to reduce the number of keys that need to be farmed
    '''
    n = a.order()
    degrees  = np.empty([n,2],dtype=int)
    keylacks = np.empty(n,dtype=int) # negative if there's a surplus

    # column 0 is in-degree, col 1 is out-degree
    for i in xrange(n):
        degrees[i,0] = a.in_degree(i)
        degrees[i,1] = a.out_degree(i)
        keylacks[i] = degrees[i,0]-a.node[i]['keys']

# This is commented out because plans are not submitted to this function without obeying the <8 outgoing rule
    # We can never make more than 8 outogoing links. Reducing these is first priority
#    manyout = (degrees[:,1]>8).nonzero()[0]
#    for p in manyout:
#        qs = list(a.edge[p].iterkeys())
#        for q in qs:
#            if a.edge[p][q]['reversible'] and canFlip(degrees,keylacks,p,q):
#                flip(a,p,q,degrees,keylacks)
#            if degrees[p,1] <= 8:
#                break
#        else:
#            # This runs if the for loop exits without the break
#            print 'Could not reduce OUT-degree sufficiently for %s'%p

    # It is difficult to gather more keys. Reducing key-gathering is next priority
    # We'll process the ones with the greatest need first
    needkeys = (keylacks>0).nonzero()[0]
    needkeys = needkeys[np.argsort(keylacks[needkeys])][::-1]
    for q in needkeys:
        for p,q2 in a.in_edges(q):
            if a.edge[p][q]['reversible'] and canFlip(degrees,keylacks,p,q):
                flip(a,p,q,degrees,keylacks)
            if keylacks[q] <= 0:
                break
#        else:
            # This runs if the for loop exits without the break
#            print 'Could not reduce IN-degree sufficiently for %s'%q


def removeSince(a,m,t):
    # Remove all but the first m edges from a (and .edge_stck)
    # Remove all but the first t Triangules from a.triangulation
    for i in xrange(len(a.edgeStack) - m):
        p,q = a.edgeStack.pop()
        try:
            a.remove_edge(p,q)
        except Exception:
            # The only exception should be from the edge having been reversed
            a.remove_edge(q,p)
#        print 'removing',p,q
#        print a.edgeStack
    while len(a.triangulation) > t:
        a.triangulation.pop()

def triangulate(a,perim):
    '''
    Recursively tries every triangulation in search a feasible one
        Each layer
            makes a Triangle out of three perimeter portals
            for every feasible way of max-fielding that Triangle
                try triangulating the two perimeter-polygons to the sides of the Triangle

    Returns True if a feasible triangulation has been made in graph a
    '''
    pn = len(perim)
    if pn < 3:
        # Base of recursion
        return True

    try:
        startStackLen = len(a.edgeStack)
    except AttributeError:
        startStackLen = 0
        a.edgeStack = []
    try:
        startTriLen = len(a.triangulation)
    except AttributeError:
        startTriLen = 0
        a.triangulation = []

#    odegrees = [a.out_degree(p) for p in perim
#    order = np.argsort(odegrees)

    # Try all possible first generation triangles with two edges on boundary that both use node i (using i as final vertex will cause no 2 first generation triangles to have same final vertex)
    for i in np.random.permutation(range(0,pn)):
#        print perim
#        print 'using %s as final'%perim[i]
        for j in xrange(TRIES_PER_TRI):
            t0 = Triangle(perim[[i,i-1,(i+1)%pn]],a,True)
            t0.findContents()
#            t0.randSplit() # Split triangle on a random portal
            t0.nearSplit() # Split triangle on the nearest portal
            try:
#                print 'trying to build'
                t0.buildGraph()
            except Deadend as d:
                # TODO when allowing suboptimal plans, this block would be unnecessary if first generation triangles were made in the right order: see Triangle.buildGraph
                # remove the links formed since beginning of loop
                removeSince(a,startStackLen,startTriLen)
#                print 'small fail'
            else:
                # This build was successful. Break from the loop
#                print 'build succeeded'
                break
        else:
            # The loop ended "normally" so this triangle failed
#            print 'big fail'
            continue

#        print 'continuing with',perim[range(i+1-pn,i)]
        if not triangulate(a,perim[range(i+1-pn,i)]): # i+1 through i-1
            # remove the links formed since beginning of loop
            removeSince(a,startStackLen,startTriLen)
            continue

        # This will be a list of the first generation triangles
        a.triangulation.append(t0)

        # This triangle and the ones to its sides succeeded
        return True

    # Could not find a solution
    return False
    
def maxFields(a):
    n = a.order()

    pts = np.array([ a.node[i]['xy'] for i in xrange(n) ])

    perim = np.array(geometry.getPerim(pts))
    if not triangulate(a,perim):
        return False
    flipSome(a)

    return True
