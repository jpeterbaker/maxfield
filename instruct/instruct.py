# This is just a script to draw a diagram showing that links must be made into but not out of fields

import matplotlib.pyplot as plt
from numpy import array

#                 0 1 2 3 4
portals = array([[0,1,1,2],\
                 [0,1,2,0]])

# Shifts to represent the triangle in different places
quads = array([[0,0],\
               [3,0],\
               [0,3],\
               [3,3]])

def pltedge(p,q,quad,style='k-'):
    plt.plot(portals[0,[p,q]]+quads[quad,0],\
             portals[1,[p,q]]+quads[quad,1],style)

###################### Links go into but not out of fields ######################

for quad in [0,1]:
    plt.plot(portals[0]+quads[quad,0],\
             portals[1]+quads[quad,1],'bo')

for quad in [0,1]:
    pltedge(0,1,quad)
    pltedge(0,2,quad)
    pltedge(0,3,quad)
    pltedge(1,3,quad)
    pltedge(2,3,quad)

# plt.arrow( x, y, dx, dy, **kwargs )
plt.arrow(1,1.1,0, 0.7,head_width=.05,head_length=.05,ec='k',fc='k')
plt.arrow(4,1.9,0,-0.7,head_width=.05,head_length=.05,ec='k',fc='k')

# an X through the impossible link
plt.plot([.9,1.1],[1.3,1.6],'r-',lw=2)

plt.axis([-.5,5.5,-1,2.5])
plt.axis('off')

plt.text(1,-.5,'NO' ,ha='center',size=30)
plt.text(4,-.5,'YES',ha='center',size=30)

plt.savefig('explainIncoming.png')
plt.clf()

###################### Link order can change field count ######################

BLUE      = ( 0 , 0 , 1 , 0.4 )
INVISIBLE = ( 0 , 0 , 0 , 0   )

from matplotlib.patches import Polygon

# returns the points in a shrunken toward their centroid
def shrink(a):
    centroid = a.mean(1).reshape([2,1])
    return  centroid + .8*(a-centroid)

# Plot a slightly shrunken triangle
def pltface(p,q,r,quad):
    shift = quads[quad].reshape([2,1])
    tri = portals[:,[p,q,r]]+shift
    tri = shrink(tri)

    plt.gca().add_patch(Polygon(tri.T , fc=BLUE, ec=INVISIBLE))

for quad in range(4):
    plt.plot(portals[0]+quads[quad,0],\
             portals[1]+quads[quad,1],'bo')

# Plot ubiquitous links and face
for quad in range(4):
    pltedge(0,1,quad)
    pltedge(0,2,quad)
    pltedge(0,3,quad)
    pltedge(1,3,quad)

    pltface(0,1,3,quad)

# Complete two of them
for quad in [1,3]:
    pltedge(1,2,quad)
    pltedge(2,3,quad)

    pltface(0,1,2,quad)
    pltface(3,1,2,quad)

# Draw large triangle on two
for quad in [0,1]:
    pltface(0,2,3,quad)

# Draw the other small face
pltface(0,1,2,2)

# Partially complete the others
pltedge(2,3,0)
pltedge(1,2,2)

# Draw pending links
pltedge(1,2,0,'k--')
pltedge(3,2,2,'k--')

# Draw transition arrows
plt.arrow(2,4,.9,0,head_width=.05,head_length=.1,ec='k',fc='k')
plt.arrow(2,1,.9,0,head_width=.05,head_length=.1,ec='k',fc='k')

plt.text(6,4,'3 fields',size=20)
plt.text(6,1,'4 fields',size=20)

plt.axis([-.5,6.5,-.5,5.5])
plt.axis('off')

plt.savefig('explainOrder.png')

