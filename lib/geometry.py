
# Portals, triangles and the like

import numpy as np

radPERe6degree = np.pi / (180*10**6)

def e6LLtoRads(pts):
    pts = pts.astype(float)
    pts *= radPERe6degree
    return pts

def radstoxyz(pts,R=1):
    # Converts degree latitude/longitude to xyz coords
    # Returns corresponding n x 3 array

    pts = pts.reshape([-1,2])

    lat = pts[:,0]
    lng = pts[:,1]

    # The radius of the latitude line
    r = np.cos(lat)

    x = np.cos(lng)*r
    y = np.sin(lng)*r
    z = np.sin(lat)
    
    xyz = np.column_stack([x,y,z])
    xyz *= R
    return xyz

def xyztorads(pts,R=1):
    pts = pts.reshape([-1,3])
    pts = pts/R
    x = pts[:,0]
    y = pts[:,1]
    z = pts[:,2]

    lat = np.arcsin(z)
    lng = np.arctan2(y,x)

    return np.column_stack([lat,lng])

def greatArcAng(x,y):
    '''
    x,y should be in latitude/longitude
    Great arc angle between x and y (in radians)
    '''

    # If either is a single point (not in a list) return a 1-d array
    flatten = y.ndim==1 or x.ndim==1

    # Formula taken from Wikipedia, accurate for distances great and small
    x = x.reshape([-1,2])
    y = y.reshape([-1,2])
    
    nx = x.shape[0]
    ny = y.shape[0]

    # After reshaping, arithmetic operators produce distance-style matrices
    latx = np.tile(x[:,0],[ny,1])
    lngx = np.tile(x[:,1],[ny,1])
    laty = np.tile(y[:,0],[nx,1]).T
    lngy = np.tile(y[:,1],[nx,1]).T

    dlng = np.abs(lngx-lngy)

    sinx = np.sin(latx)
    cosx = np.cos(latx)

    siny = np.sin(laty)
    cosy = np.cos(laty)
    
    sind = np.sin(dlng)
    cosd = np.cos(dlng)

    numer = np.sqrt( (cosx*sind)**2 + (cosy*sinx-siny*cosx*cosd)**2 )
    denom = siny*sinx + cosy*cosx*cosd

    # great arc angle containing x and y
    angles = np.arctan2(numer,denom)

    if flatten:
        angles.shape = -1

    return angles

def sphereDist(x,y,R=6371000):
    sigma = greatArcAng(x,y)
    return R*sigma

def sphereTriContains(pts,x):
    '''
    pts is a 3 x 3 array representing vertices of a triangle
        pts[i] contains the x,y,z coords of vertex i
    x is a 2-array representing the test point

    points should be represented in xyz format

    returns True iff x is inside the triangle
        yes, three points make two triangles, but we assume the small one

    behavior in border cases ont guaranteed
    '''
    x = x.reshape([-1,3])

    # Find vectors orthogonal to the planes through origin and triangle sides

    crosses = np.cross( pts[[1,2,0]] , pts[[2,0,1]] )

    xsign = np.dot( crosses,x.T )
    psign = np.sum(crosses*pts,1).reshape([3,1])

    # Check whether opposite vertex is always on same side of plane as x
    return np.all( xsign*psign > 0,0)

def planeDist(x,y):
    x = x.reshape([-1,2])
    y = y.reshape([-1,2])

    return np.sqrt(np.array([ [sum( (a-b)**2 ) for a in y] for b in x ]))

def makeLace(n):
    # sequence of perimeter nodes to hit for a lacing-style triangulation
    # begins with the edge 1,-1
    lace = np.arange(1,n//2)
    lace = np.vstack([lace,(-lace)%n])
    lace = lace.T.reshape(-1)
    lace = list(lace)
    if n%2==1:
        lace.append(n//2)
    return lace

def rotate(x):
    # rotate the vector(s) in a by one quarter turn counter-clockwise
    if x.ndim == 1:
        x[[0,1]] = [-x[1],x[0]]
    else:
        x[:,[0,1]] = x[:,[1,0]]
        x[:,0] *= -1

def norms(x):
    'Norm per row of x'
    return np.sqrt(np.sum(x**2,1))

def gnomonicProj(pts,ptsxyz=None):
    '''
    pts should be in lat/lng
    Uses the centroid of pts as the center, North Pole as positive y-direction
    This is only guaranteed to work if no two points are more than 90 degrees apart (great arcwise)
    This is about 9700 km across the surface of Earth
    '''
    if ptsxyz == None:
        ptsxyz = radstoxyz(pts)

    # We'll project onto the plane tangent at base
    basexyz = ptsxyz.mean(0)
    basexyz /= np.linalg.norm(basexyz)

    base = xyztorads(basexyz).reshape(-1)

    # We'll us the triangle base - portal - North Pole
    # The angles at these vertices are, respectively A - B - C
    # The corresponding lowercase letter is arc-angle of the opposite edge
    
    a = np.pi/2-pts[:,0]
    b = np.pi/2-base[0]
    c = greatArcAng(base,pts)
    C = base[1] - pts[:,1]

    # http://en.wikipedia.org/wiki/Spherical_trigonometry#Identities
    # A = arcsin[   sin(a)*sin(C)          /   sin(c)          ]
    # A = arccos[ { cos(a)-cos(c)*cos(b) } / { sin(c)*sin(b) } ]
    sinA = np.sin(a)*np.sin(C) / np.sin(c)
    cosA= (np.cos(a)-np.cos(c)*np.cos(b))/(np.sin(c)*np.sin(b))
    
    # arcsin can only fall in [-pi/2,pi/2]
    # we can find obtuse angles this way
    theta = np.arctan2(sinA,cosA)

    # Distance from base
    r = np.tan(c).reshape([-1,1])
    
    # theta measures counter-clockwise from north
    xy = np.column_stack([ -np.sin(theta) , np.cos(theta) ])*r
    return xy

def between(a,b,pts):
    # diff will be orthogonal to the line through a,b
    diff = pts[a]-pts[b]
    rotate(diff)
    
    # maximum inner product with diff
    c = np.argmax(np.dot(pts,diff))

    if c == a or c == b:
        return None
    else:
        return c

def getPerim(pts):
    # These are for planar points
    # This could cause problems if the playfield contains the North or South pole or any pont of the 180th meridian
    hix = np.argmax(pts[:,0])
    hiy = np.argmax(pts[:,1:])
    
    perim = {hix:hiy , hiy:hix}
    perimlist = []

    a = hix
    b = hiy
    
    aNeverChanged = True

    while a != hix or aNeverChanged:
        c = between(a,b,pts)
        if c == None:
            # there is no perimeter point between a and b
            # proceed to the next adjacent pair
            perimlist.append(a)
            a = b
            b = perim[b]

            aNeverChanged = False
        else:
            # c is on the perimeter after a
            # we will next look for another point between a,c
            perim[a] = c
            perim[c] = b
            b = c

    return perimlist

def arc(a,b,c):
    '''
    Finds the arc through three points in a plane
    returns z,r,ta,tb,tc

    z = [x,y] is the center of the arc
    r is the radius of the arc
    a = z+r*[cos(ta),sin(ta)]
    b = z+r*[cos(tb),sin(tb)]
    c = z+r*[cos(tc),sin(tc)]
    '''
    
    # center points on b
    ab = a-b
    cb = c-b
    ac = a-c

    # squared lengths
    slab =  ab[0]**2+ab[1]**2
    slcb =  cb[0]**2+cb[1]**2
    # length
    lac = (ac[0]**2+ac[1]**2)**.5

    # this is from wikipedia http://en.wikipedia.org/wiki/Circumscribed_circle
    D = 2*(ab[0]*cb[1]-ab[1]*cb[0])
    z = np.array([ cb[1]*slab - ab[1]*slcb ,\
                   ab[0]*slcb - cb[0]*slab ])/D + b

    # the angle a,b,c
    t = np.abs( np.arctan(ab[1]/ab[0]) - np.arctan(cb[1]/cb[0]) )

    # the angle a,z,c is 2*t
    # the angles a,c,z and c,a,z are equal (isosolecsescscs triangle)
    # a,c,z + c,a,z + a,z,c = 180
    acz = np.pi/2-t

    # d is the midpoint of ac
    lad = lac/2 # the length of ad

    # d,c,z is a right triangle with hypoteneuse az
    # and since a,c,z = a,d,z
    r = lad/np.cos(acz)

    az = a-z
    bz = b-z
    cz = c-z
    ta = np.arctan2(az[1],az[0])
    tb = np.arctan2(bz[1],bz[0])
    tc = np.arctan2(cz[1],cz[0])
    
    return z,r,ta,tb,tc


if __name__ == '__main__':
    a = np.array([1., 1])
    b = np.array([1.,-1])
    c = np.array([3., 1])

    z,r,ta,tb,tc = arc(a,b,c)
    print z,r
    print ta/np.pi
    print tb/np.pi
    print tc/np.pi
    z,r,ta,tb,tc = arc(a,c,b)
    print z,r
    print ta/np.pi
    print tb/np.pi
    print tc/np.pi

