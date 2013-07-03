
import matplotlib.pyplot as plt
import geometry
np = geometry.np
import agentOrder

def commaGroup(n):
    # Returns a string of n with commas in place
    s = str(n)
    return ','.join([ s[max(i,0):i+3] for i in range(len(s)-3,-3,-3)][::-1])

class PlanPrinter:
    def __init__(self,a,outputDir,nagents):
        self.a = a
        self.n = a.order() # number of nodes
        self.m = a.size()  # number of links
        self.nagents = nagents
        self.outputDir = outputDir

        # if the ith link to be made is (p,q) then orderedEdges[i] = (p,q)
        self.orderedEdges = [None]*self.m
        for e in a.edges_iter():
            self.orderedEdges[a.edge[e[0]][e[1]]['order']] = e

        # movements[i][j] is the index (in orderedEdges) of agent i's jth link
        self.movements = agentOrder.getAgentOrder(a,nagents,self.orderedEdges)

        # link2agent[i] is the agent that will make the ith link
        self.link2agent = [-1]*self.m
        for i in range(nagents):
            for e in self.movements[i]:
                self.link2agent[e] = i

        # keyneeds[i,j] = number of keys agent i needs for portal j
        self.agentkeyneeds = np.zeros([self.nagents,self.n],dtype=int)
        for i in xrange(self.nagents):
            for e in self.movements[i]:
                p,q = self.orderedEdges[e]
                self.agentkeyneeds[i][q] += 1

        self.names = np.array([a.node[i]['name'] for i in xrange(self.n)])
        # The alphabetical order
        self.nameOrder = np.argsort(self.names)

        self.maxNameLen = max([len(a.node[i]['name']) for  i in xrange(self.n)])

    def keyPrep(self):
        with open(self.outputDir+'keyPrep.txt','w') as fout:
            rowFormat = '{0:{maxlen}}{1:>15}  {2:>15}\n'
            fout.write(rowFormat.format(\
                'Portal',\
                'Keys Needed',\
                'Keys Lacked',\
                maxlen=self.maxNameLen\
            ))
            for i in self.nameOrder:
                keylack = max(self.a.in_degree(i)-self.a.node[i]['keys'],0)
                fout.write(rowFormat.format(\
                    self.names[i],\
                    self.a.in_degree(i),\
                    keylack,\
                    maxlen=self.maxNameLen\
                ))

        unused   = set(xrange(self.n))
        infirst  = []
        outfirst = []

        for p,q in self.orderedEdges:
            if p in unused:
                outfirst.append(self.names[p])
                unused.remove(p)
            if q in unused:
                infirst.append(self.names[q])
                unused.remove(q)

        with open(self.outputDir+'ownershipPrep.txt','w') as fout:
            fout.write('First link is incoming\n')
            fout.write('These should be at full resonators before linking\n')
            fout.write('Other portals can be filled when first agent arrives\n')
            for s in infirst:
                fout.write('  %s\n'%s)


    def agentKeys(self):
        rowFormat = '{0:{maxlen}}{1:6}\n'
        for agent in range(self.nagents):
            with open(self.outputDir+'keys_for_agent_%s_of_%s.txt'\
                    %(agent+1,self.nagents),'w') as fout:
                fout.write('Keys for Agent %s of %s\n\n'%(agent+1,self.nagents))
                for portal in self.nameOrder:
                    if self.agentkeyneeds[agent,portal] <= 0:
                        continue
                    fout.write(rowFormat.format(\
                        self.names[portal],\
                        self.agentkeyneeds[agent,portal],\
                        maxlen=self.maxNameLen\
                    ))

    def planMap(self):
        xy = np.array([self.a.node[i]['xy'] for i in xrange(self.n)])

        xmin = xy[:,0].min()
        xmax = xy[:,0].max()
        ymin = xy[:,1].min()
        ymax = xy[:,1].max()

        xylims = np.array([xmin,xmax,ymin,ymax])
        xylims *= 1.1

        # Plot labels aligned to avoid other portals
        for i in xrange(self.n):
            plt.plot(xy[i,0],xy[i,1],'go')

            displaces = xy[i] - xy
            displaces[i,:] = np.inf

            nearest = np.argmin(np.abs(displaces).sum(1))

            if xy[nearest,0] < xy[i,0]:
                ha = 'left'
            else:
                ha = 'right'
            if xy[nearest,1] < xy[i,1]:
                va = 'bottom'
            else:
                va = 'top'
            
            plt.text(xy[i,0],xy[i,1],self.names[i],ha=ha,va=va)


        plt.title('Portal Positions')

#        plt.plot(0,0,'r*')
        fig = plt.gcf()
        plt.axis('off')
        fig.set_size_inches(6.5,9)
        plt.axis(xylims)
        plt.savefig(self.outputDir+'MasterMap.png')
#        plt.show()
        plt.clf()

        # Draw the map with all edges in place and labeled
#        ptmap   = dict([(i,self.a.node[i]['xy'  ]) for i in xrange(self.n) ])
#        namemap = dict([(i,self.a.node[i]['name']) for i in xrange(self.n) ])
#
#        edgelabels = dict([ (e,self.a.edge[e[0]][e[1]]['order'])\
#                            for e in self.a.edges_iter() ])
#        nx.draw(self.a,ptmap,labels=namemap,\
#               font_color='k',\
#               font_weight='bold',\
#               edge_color='g',\
#               node_color=[(0.,1.,0.)],\
#               node_size=100)
#        nx.draw_networkx_edge_labels(self.a,ptmap,edgelabels)
#        plt.axis(xylims)
#        plt.show()
#        plt.clf()

    def agentLinks(self):
        # Total distance traveled by each agent
        agentdists = np.zeros(self.nagents)
        # Total experience for each agent
        agentexps  = np.zeros(self.nagents,dtype=int)

        for i in range(self.nagents):
            movie = self.movements[i]
            # first portal in first link
            curpos = self.a.node[self.orderedEdges[movie[0]][0]]['geo']
            for e in movie[1:]:
                p,q = self.orderedEdges[e]
                newpos = self.a.node[p]['geo']
                dist = geometry.sphereDist(curpos,newpos)
                agentdists[i] += dist
                curpos = newpos

                agentexps[i] += 313 + 1250*len(self.a.edge[p][q]['fields'])

        # Different formatting for the agent's own links
        plainStr = '%s makes %s fields\n  %s gets %s AP\n    %s\n    %s\n'
        hilitStr = '%s makes %s fields\n__%s gets %s AP\n    %s\n    %s\n'
        
        for agent in range(self.nagents):
            with open(self.outputDir+'links_for_agent_%s_of_%s.txt'\
                    %(agent+1,self.nagents),'w') as fout:

                fout.write('Complete link schedule issued to agent %s of %s\n'\
                    %(agent+1,self.nagents))
                
                fout.write('Total distance  : %s m\n'%int(agentdists[agent]))
                fout.write('Total experience: %s AP\n\n'%(agentexps[agent]))
                
                for i in xrange(self.m):
                    p,q = self.orderedEdges[i]
                    
                    linkagent = self.link2agent[i]

                    numfields = len(self.a.edge[p][q]['fields'])
                    ap = 313 + numfields*1250

                    if linkagent != agent:
                        fout.write(plainStr%(\
                            i,\
                            numfields,\
                            linkagent+1,\
                            ap,\
                            self.names[p],\
                            self.names[q]\
                        ))
                    else:
                        fout.write(hilitStr%(\
                            i,\
                            numfields,\
                            linkagent+1,\
                            ap,\
                            self.names[p],\
                            self.names[q]\
                        ))
    def animate(self):
        # show or save a sequence of images demonstrating how the plan would unfold
        from matplotlib.patches import Polygon

        fig = plt.figure()
        ax  = fig.add_subplot(111)

        GREEN     = ( 0.0 , 1.0 , 0.0 , 0.2)
        RED       = ( 1.0 , 0.0 , 0.0 , 0.5)
        INVISIBLE = ( 0.0 , 0.0 , 0.0 , 0.0 )

        portals = np.array([self.a.node[i]['xy'] for i in self.a.nodes_iter()]).T
        
        aptotal = 0

        edges   = []
        patches = []

        for i in xrange(self.m):
            p,q = self.orderedEdges[i]

            plt.plot(portals[0],portals[1],'go')

            for edge in edges:
                plt.plot(edge[0],edge[1],'g-')

            # We'll display the new fields in red
            newPatches = []
            for tri in self.a.edge[p][q]['fields']:
                coords = [ self.a.node[v]['xy'] for v in tri ]
                newPatches.append(Polygon(coords,facecolor=RED,\
                                                 edgecolor=INVISIBLE))
            
            aptotal += 313+1250*len(newPatches)

            newEdge = np.array([self.a.node[p]['xy'],self.a.node[q]['xy']]).T

            patches += newPatches
            edges.append(newEdge)

           # plt.arrow( x, y, dx, dy, **kwargs )
#            plt.arrow(              newEdge[0,0],\
#                                    newEdge[1,0],\
#                       newEdge[0,1]-newEdge[0,0],\
#                       newEdge[1,1]-newEdge[1,0],\
#                       fc="k", ec="k")#,head_width=0.0005,head_length=0.001 )
            
            plt.plot(newEdge[0],newEdge[1],'k-',lw=2)

            for patch in patches:
                ax.add_patch(patch)

            ax.set_title('AP:\n%s'%commaGroup(aptotal),ha='center')
            ax.axis('off')
            plt.savefig(self.outputDir+'frame_%s.png'%i)
            ax.cla()

            for patch in patches:
                patch.set_facecolor(GREEN)

        plt.plot(portals[0],portals[1],'go')
        for edge in edges:
            plt.plot(edge[0],edge[1],'g-')
        for patch in patches:
            ax.add_patch(patch)

        ax.set_title('AP:\n%s'%commaGroup(aptotal),ha='center')
        ax.axis('off')
        plt.savefig(self.outputDir+'frame_%s.png'%self.m)

    def instruct(self):
        portals = np.array([self.a.node[i]['xy'] for i in self.a.nodes_iter()]).T
        
        gen1 = self.a.triangulation

        oldedges = []

        depth = 0
        while True:
            # newedges[i][0] has the x-coordinates of both verts of edge i
            newedges = [ np.array([
                                self.a.node[p]['xy'] ,\
                                self.a.node[q]['xy']
                         ]).T\
                             for j in range(len(gen1)) \
                             for p,q in gen1[j].edgesByDepth(depth)\
                       ]

            if len(newedges) == 0:
                break
            
            plt.plot(portals[0],portals[1],'go')

            for edge in oldedges:
                plt.plot(edge[0],edge[1],'k-')

            for edge in newedges:
                plt.plot(edge[0],edge[1],'r-')
            
            oldedges += newedges

            plt.axis('off')
            plt.savefig(self.outputDir+'depth_%s.png'%depth)
            plt.clf()

            depth += 1

        plt.plot(portals[0],portals[1],'go')

        for edge in oldedges:
            plt.plot(edge[0],edge[1],'k-')

        plt.axis('off')
        plt.savefig(self.outputDir+'depth_%s.png'%depth)
        plt.clf()


