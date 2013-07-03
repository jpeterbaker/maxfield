
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
    # Formula taken from Wikipedia, accurate for distances great and small
    x = x.reshape([-1,2])
    y = y.reshape([-1,2])
    
    latx,lngx = x[:,0],x[:,1]
    laty,lngy = y[:,0],y[:,1]

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
    return np.arctan2(numer,denom)

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
    return np.sqrt(np.sum((x-y)**2,1))

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

