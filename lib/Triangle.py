
import geometry
np = geometry.np

class Deadend(Exception):
    def __init__(self,s):
        self.explain = s

def try_ordered_edge(a,p,q,reversible):
    if a.has_edge(p,q) or a.has_edge(q,p):
        return

    if reversible and a.out_degree(p) > a.out_degree(q):
        p,q = q,p

    if a.out_degree(p) >= 8:
        if not reversible:
            raise(Deadend('%s already has 8 outgoing'%p))
        if a.out_degree(q) >= 8:
            raise(Deadend('%s and %s already have 8 outgoing'%(p,q)))
        p,q = q,p
    
    m = a.size()
    a.add_edge(p,q,{'order':m,'reversible':reversible,'fields':[]})
    a.edgeStack.append( (p,q) )

class Triangle:
    def __init__(self,verts,a,exterior=False):
        '''
        verts should be a 3-list of Portals
        verts[0] should be the final one used in linking
        exterior should be set to true if this triangle has no triangle parent
            the orientation of the outer edges of exterior Triangles do not matter
        '''
        # If this portal is exterior, the final vertex doesn't matter
        self.verts = list(verts)
        self.a = a
        self.exterior = exterior

        if exterior:
            # Randomizing should help prevent perimeter nodes from getting too many links
            final = np.random.randint(3)
            tmp = self.verts[final]
            self.verts[final] = self.verts[0]
            self.verts[0] = tmp

        self.pts = np.array([a.node[p]['xyz'] for p in verts])
        self.children = []
        self.contents = []
        self.center = None

    def findContents(self,candidates=None):
        if candidates == None:
            candidates = xrange(self.a.order())
        for p in candidates:
            if p in self.verts:
                continue
            if geometry.sphereTriContains(self.pts,self.a.node[p]['xyz']):
                self.contents.append(p)

    def randSplit(self):
        if len(self.contents) == 0:
            return
        
        p = self.contents[np.random.randint(len(self.contents))]
        
        self.splitOn(p)

        for child in self.children:
            child.randSplit()

    def nearSplit(self):
        # Split on the node closest to final
        if len(self.contents) == 0:
            return
        contentPts = np.array([self.a.node[p]['pos'] for p in self.contents])
        displaces = contentPts - self.a.node[self.verts[0]]['pos']
        dists = np.sum(displaces**2,1)
        closest = np.argmin(dists)

        self.splitOn(self.contents[closest])

        for child in self.children:
            child.nearSplit()

    def splitOn(self,p):
        # 'opposite' is the child that does not share the final vertex
        # Because of the build order, it's safe for this triangle to believe it is exterior
        opposite  =  Triangle([self.verts[1],p,\
                               self.verts[2]],self.a,True)
        # The other two children must also use my final as their final
        adjacents = [\
                     Triangle([self.verts[0],\
                               self.verts[2],p],self.a),\
                     Triangle([self.verts[0],\
                               self.verts[1],p],self.a)\
                    ]
        
        self.children = [opposite]+adjacents
        self.center = p

        for child in self.children:
            child.findContents(self.contents)

    def tostr(self):
        # Just a string representation of the triangle
        return str([self.a.node[self.verts[i]]['name'] for i in range(3)])

    def buildFinal(self):
#        print 'building final',self.tostr()
        if self.exterior:
            # Avoid making the final the link origin when possible
            try_ordered_edge(self.a,self.verts[1],\
                               self.verts[0],self.exterior)
            try_ordered_edge(self.a,self.verts[2],\
                               self.verts[0],self.exterior)
        else:
            try_ordered_edge(self.a,self.verts[0],\
                               self.verts[1],self.exterior)
            try_ordered_edge(self.a,self.verts[0],\
                               self.verts[2],self.exterior)

        if len(self.children) > 0:
            for i in [1,2]:
                self.children[i].buildFinal()

    def buildExceptFinal(self):
#        print 'building EXCEPT final',self.tostr()
        if len(self.children) == 0:
#            print 'no children'
            p,q = self.verts[2] , self.verts[1]
            try_ordered_edge(self.a,p,q,True)
            return

        # Child 0 is guaranteed to be the one opposite final
        self.children[0].buildGraph()

        for child in self.children[1:3]:
            child.buildExceptFinal()

    def buildGraph(self):
#        print 'building',self.tostr()
        # A first generation triangle could have its final vertex's edges already completed by neighbors. This will cause the first generation to be completed when the opposite edge is added which complicates  completing inside descendents. This could be solved by choosing a new final vertex (or carefully choosing the order of completion of first generation triangles).
        if (                                                \
            self.a.has_edge(self.verts[0],self.verts[1]) or \
            self.a.has_edge(self.verts[1],self.verts[0])    \
           ) and                                            \
           (                                                \
            self.a.has_edge(self.verts[0],self.verts[2]) or \
            self.a.has_edge(self.verts[2],self.verts[0])    \
           ):
#            print 'Final vertex completed!!!'
            raise Deadend('Final vertex completed by neighbors')
        self.buildExceptFinal()
        self.buildFinal()

    def contains(self,pt):
        return np.all(np.sum(self.orths*(pt-self.pts),1) < 0)

    # Attach to each edge a list of fields that it completes
    def markEdgesWithFields(self):
        edges = [(0,0)]*3
        for i in range(3):
            p = self.verts[i-1]
            q = self.verts[i-2]
            if not self.a.has_edge(p,q):
                p,q = q,p
            # The graph should have been completed by now, so the edge p,q exists
            edges[i] = (p,q)

        edgeOrders = [self.a.edge[p][q]['order'] for p,q in edges]

        lastInd = np.argmax(edgeOrders)
        # The edge that completes this triangle
        p,q = edges[lastInd]

        self.a.edge[p][q]['fields'].append(self.verts)

        for child in self.children:
            child.markEdgesWithFields()

    def edgesByDepth(self,depth):
        # Return list of edges of triangles at given depth
        # 0 means edges of this very triangle
        # 1 means edges splitting this triangle
        # 2 means edges splitting this triangle's children 
        # etc.
        if depth == 0:
            return [ (self.verts[i],self.verts[i-1]) for i in range(3) ]
        if depth == 1:
            if self.center == None:
                return []
            return [ (self.verts[i],self.center) for i in range(3) ]
        return [e for child in self.children\
                  for e in child.edgesByDepth(depth-1)]




