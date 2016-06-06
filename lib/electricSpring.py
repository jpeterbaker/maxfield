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

def edgeLabelPos(fixed,anchors):
    '''
    This is for choosing label positions
    Each portal and label is modeled as a particle with repelling charge
    The connection between label and object is modeled as a sping

    fixed:      positions of repelling objects that do not move (portals)
                a numpy array of portal positions: n x 2

    anchors:    positions to which labels should be attracted

    k:          the spring constant (proportional to the repelling force)

    returns labels: a numpy array of label positions
    '''
    n = fixed.shape[0]
    m = anchors.shape[0]

    scale = np.max([ fixed[:,0].max()-fixed[:,0].min() ,\
                     fixed[:,1].max()-fixed[:,1].min() ])

    # Normalize
    fixed = fixed.copy()/scale

    # If portals are uniformly distributed, I think this is sensible
    k = 10
    print 'k =',k

    # labels start near anchors
    labels = anchors/scale + np.random.randn(m,2)*n

    # labels are repeleld from all portals and labels
    charges = np.vstack([fixed,labels])

    MAXIT = 10

    count = 1
    delta = np.inf
    while delta > 0.001 and count<MAXIT:
        oldlabels = labels.copy()

        dx = np.column_stack([labels[:,0]]*(n+m)) - np.tile(charges[:,0],[m,1])
        dy = np.column_stack([labels[:,1]]*(n+m)) - np.tile(charges[:,1],[m,1])
        
        print
        print np.min(np.abs(dx)),np.max(np.abs(dx))
        print np.min(np.abs(dy)),np.max(np.abs(dy))

        # force is proportional to 1/dist^2 (normalization cancels one out)
        # distance cubed (combines force normalization with 1/d^2 factor)
        dists3 = (dx**2+dy**2)**1.5
        dists3[range(m),range(n,n+m)]=1 # avoid 0/0

        print np.min(np.abs(dists3)),np.max(np.abs(dists3))
        
        elecForces = np.column_stack([ np.sum(dx/dists3,1) ,\
                                       np.sum(dy/dists3,1) ])
        springForces = k*(anchors - labels)
        print np.max(np.abs(elecForces)),np.max(np.abs(springForces))
        forces = elecForces + springForces
        forces /= count*n

        labels += forces

        charges[n:,:] = labels
        delta = np.max(np.abs(forces))
        count += 1

    print 'ending delta =',delta
    if count >= MAXIT:
        print 'WARNING: label placement loop exiting after max iterations'
        
    return labels*scale

if __name__=='__main__':
    import matplotlib.pyplot as plt

    portals = np.array([[0.,0],[0,1],[1,0]])
    anchors = np.array([[0,.5],[.5,.5],[.5,0]])
    
    labelpos = edgeLabelPos(portals,anchors)

    n = portals.shape[0]

    plt.plot(portals[:,0],portals[:,1],'bo')
    for i in range(n):
        plt.plot([ portals[i-n,0],labelpos[i-n,0],portals[i-n+1,0] ]  ,\
                 [ portals[i-n,1],labelpos[i-n,1],portals[i-n+1,1] ],'r-')

    plt.show()
        
