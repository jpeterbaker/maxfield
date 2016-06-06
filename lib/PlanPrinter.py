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

# Sorry that this whole file is so messy. Input/output things are tough to make tidy.

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import geometry
np = geometry.np
import agentOrder
import networkx as nx
import electricSpring
import time

# returns the points in a shrunken toward their centroid
def shrink(a):
    centroid = a.mean(1).reshape([2,1])
    return  centroid + .9*(a-centroid)

def commaGroup(n):
    # Returns a string of n with commas in place
    s = str(n)
    return ','.join([ s[max(i,0):i+3] for i in range(len(s)-3,-3,-3)][::-1])

class PlanPrinter:
    def __init__(self,a,outputDir,nagents,color='#FF004D'):
        self.a = a
        self.n = a.order() # number of nodes
        self.m = a.size()  # number of links

        self.nagents = nagents
        self.outputDir = outputDir
        self.color = color

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
        makeLowerCase = np.vectorize(lambda s: s.lower())
        self.nameOrder = np.argsort(makeLowerCase(self.names))

        self.xy = np.array([self.a.node[i]['xy'] for i in xrange(self.n)])

        # The order from north to south (for easy-to-find labels)
        self.posOrder = np.argsort(self.xy,axis=0)[::-1,1]

        # The inverse permutation of posOrder
        self.nslabel = [-1]*self.n
        for i in xrange(self.n):
            self.nslabel[self.posOrder[i]] = i

        self.maxNameLen = max([len(a.node[i]['name']) for  i in xrange(self.n)])

    def keyPrep(self):
        rowFormat = '{0:11d} | {1:6d} | {2}\n'
        with open(self.outputDir+'keyPrep.txt','w') as fout:
            fout.write( 'Keys Needed | Lacked |                                  %s\n'\
                %time.strftime('%Y-%m-%d %H:%M:%S %Z'))
            for i in self.nameOrder:
                keylack = max(self.a.in_degree(i)-self.a.node[i]['keys'],0)
                fout.write(rowFormat.format(\
                    self.a.in_degree(i),\
                    keylack,\
                    self.names[i]\
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

        infirst.sort()
        outfirst.sort()

        with open(self.outputDir+'ownershipPrep.txt','w') as fout:
            fout.write("These portals' first links are incoming                 %s\n"\
                %time.strftime('%Y-%m-%d %H:%M:%S %Z'))
            fout.write('They should be at full resonators before linking\n\n')
            for s in infirst:
                fout.write('  %s\n'%s)

            fout.write("\nThese portals' first links are outgoing\n\n")
            fout.write('Their resonators can be applied when first agent arrives\n')
            for s in outfirst:
                fout.write('  %s\n'%s)


    def agentKeys(self):
        rowFormat = '%4s %4s %s\n'
        for agent in range(self.nagents):
            with open(self.outputDir+'keys_for_agent_%s_of_%s.txt'\
                    %(agent+1,self.nagents),'w') as fout:
                fout.write('Keys for Agent %s of %s                                   %s\n\n'\
                    %(agent+1,self.nagents, time.strftime('%Y-%m-%d %H:%M:%S %Z')))
                fout.write('Map# Keys Name\n')

                for portal in self.nameOrder:
                    
                    keys = self.agentkeyneeds[agent,portal]
                    if self.agentkeyneeds[agent,portal] == 0:
                        keys = ''
                        
                    fout.write(rowFormat%(\
                        self.nslabel[portal],\
                        keys,\
                        self.names[portal]\
                    ))

    def drawBlankMap(self):
        plt.plot(self.xy[:,0],self.xy[:,1],'o',ms=16,color=self.color)

        for i in xrange(self.n):
            plt.text(self.xy[i,0],self.xy[i,1],self.nslabel[i],\
                     fontweight='bold',ha='center',va='center',fontsize=10)

    def drawSubgraph(self,edges=None):
        '''
        Draw a subgraph of a
        Only includes the edges in 'edges'
        Default is all edges
        '''
        if edges is None:
            edges = range(self.m)

#        anchors = np.array([ self.xy[self.orderedEdges[e],:] for e in edges]).mean(1)
#        edgeLabelPos = electricSpring.edgeLabelPos(self.xy,anchors)
#
#        self.drawBlankMap()
#
#        for i in xrange(len(edges)):
#            j = edges[i]
#            p,q = self.orderedEdges[j]
#            plt.plot([ self.xy[p,0],edgeLabelPos[i,0],self.xy[q,0] ]  ,\
#                     [ self.xy[p,1],edgeLabelPos[i,1],self.xy[q,1] ],'r-')
#
#            plt.text(edgeLabelPos[i,0],edgeLabelPos[i,1],j,\
#                     ha='center',va='center')

### The code below works. It just uses networkx draw functions
        if edges is None:
            b = self.a
        else:
            b = nx.DiGraph()
            b.add_nodes_from(xrange(self.n))

            b = nx.DiGraph()
            b.add_nodes_from(xrange(self.n))

            for e in edges:
                p,q = self.orderedEdges[e]
                b.add_edge(p,q,{'order':e})

        edgelabels = dict([ (e,self.a.edge[e[0]][e[1]]['order'])\
                            for e in b.edges_iter() ])

        plt.plot(self.xy[:,0],self.xy[:,1],'o',ms=16,color=self.color)

        for j in xrange(self.n):
            i = self.posOrder[j]
            plt.text(self.xy[i,0],self.xy[i,1],j,\
                     fontweight='bold',ha='center',va='center')

        try:
            nx.draw_networkx_edge_labels(b,self.ptmap,edgelabels)
        except AttributeError:
            self.ptmap   = dict([(i,self.a.node[i]['xy']) for i in xrange(self.n) ])
            nx.draw_networkx_edge_labels(b,self.ptmap,edgelabels)

        # edge_color does not seem to support arbitrary colors easily
        if self.color == '#3BF256':
            nx.draw_networkx_edges(b,self.ptmap,edge_color='g')
        elif self.color == '#2ABBFF':
            nx.draw_networkx_edges(b,self.ptmap,edge_color='b')
        else:
            nx.draw_networkx_edges(b,self.ptmap,edge_color='k')
        plt.axis('off')

    def planMap(self):

        xmin = self.xy[:,0].min()
        xmax = self.xy[:,0].max()
        ymin = self.xy[:,1].min()
        ymax = self.xy[:,1].max()

        xylims = np.array([xmin,xmax,ymin,ymax])
        xylims *= 1.1

        # Plot labels aligned to avoid other portals
        for j in xrange(self.n):
            i = self.posOrder[j]
            plt.plot(self.xy[i,0],self.xy[i,1],'o',color=self.color)

            displaces = self.xy[i] - self.xy
            displaces[i,:] = np.inf

            nearest = np.argmin(np.abs(displaces).sum(1))

            if self.xy[nearest,0] < self.xy[i,0]:
                ha = 'left'
            else:
                ha = 'right'
            if self.xy[nearest,1] < self.xy[i,1]:
                va = 'bottom'
            else:
                va = 'top'
            
            plt.text(self.xy[i,0],self.xy[i,1],str(j),ha=ha,va=va)


        fig = plt.gcf()
        fig.set_size_inches(6.5,9)
        plt.axis(xylims)
        plt.axis('off')
        plt.title('Portals numbered north to south\nNames on key list')
        plt.savefig(self.outputDir+'portalMap.png')
#        plt.show()
        plt.clf()

        # Draw the map with all edges in place and labeled
        self.drawSubgraph()
#        self.drawBlankMap()
        plt.axis(xylims)
        plt.axis('off')
        plt.title('Portal and Link Map')
        plt.savefig(self.outputDir+'linkMap.png')
        plt.clf()

#        for agent in range(self.nagents):
#            self.drawSubgraph(self.movements[agent])
#            plt.axis(xylims)
#            plt.savefig(self.outputDir+'linkMap_agent_%s_of_%s.png'%(agent+1,self.nagents))
#            plt.clf()

    def agentLinks(self):

        # Total distance traveled by each agent
        agentdists = np.zeros(self.nagents)
        # Total number of links, fields for each agent
        agentlinkcount  = [0]*self.nagents
        agentfieldcount = [0]*self.nagents
        totalAP         = 0
        totalDist       = 0

        for i in range(self.nagents):
            movie = self.movements[i]
            # first portal in first link
            curpos = self.a.node[self.orderedEdges[movie[0]][0]]['geo']
            agentlinkcount[i] = len(movie)
            for e in movie[1:]:
                p,q = self.orderedEdges[e]
                newpos = self.a.node[p]['geo']
                dist = geometry.sphereDist(curpos,newpos)
#                print 'Agent %s walks %s to %s'%(i,dist,self.nslabel[p])
                agentdists[i] += dist
                curpos = newpos

                agentfieldcount[i] += len(self.a.edge[p][q]['fields'])
                totalAP += 313
                totalAP += 1250 * len(self.a.edge[p][q]['fields'])
                totalDist += dist

        # Different formatting for the agent's own links
#        plainStr = '{0:4d}{1:1s} {2: 5d}{3:5d} {4:s}\n            {5:4d} {6:s}\n\n'
        plainStr = '{0:4d}{1:1s} {2: 5d}{3:5d} {4:s} -> {5:d} {6:s}\n'
        hilitStr = '{0:4d}{1:1s} {2:_>5d}{3:5d} {4:s}\n            {5:4d} {6:s}\n\n'
        
        totalTime = self.a.walktime+self.a.linktime+self.a.commtime

        for agent in range(self.nagents):
            with open(self.outputDir+'links_for_agent_%s_of_%s.txt'\
                    %(agent+1,self.nagents),'w') as fout:

                fout.write('Complete link schedule issued to agent %s of %s           %s\n\n'\
                    %(agent+1,self.nagents,time.strftime('%Y-%m-%d %H:%M:%S %Z')))
                fout.write('\nLinks marked with * can be made EARLY\n')
                
                fout.write('----------- PLAN DATA ------------\n')
                fout.write('Minutes:                 %s minutes\n'%int(totalTime/60+.5))
                fout.write('Total Distance:          %s meter\n'%int(totalDist))
                fout.write('Total AP:                %s\n'%totalAP)
                fout.write('AP per Agent per minute: %0.2f AP/Agent/min\n'%float(totalAP/self.nagents/(totalTime/60+.5)))
                fout.write('AP per Agent per meter:  %0.2f AP/Agent/m\n'%float(totalAP/self.nagents/totalDist))

                agentAP = 313*agentlinkcount[agent] + 1250*agentfieldcount[agent]

                fout.write('----------- AGENT DATA -----------\n')
                fout.write('Distance traveled: %s m (%s %%)\n'%(int(agentdists[agent]),int(100*agentdists[agent]/totalDist)))
                fout.write('Links made:        %s\n'%(agentlinkcount[agent]))
                fout.write('Fields completed:  %s\n'%(agentfieldcount[agent]))
                fout.write('Total experience:  %s AP (%s %%)\n'%(agentAP,int(100*agentAP/totalAP)))


                fout.write('----------------------------------\n')
                fout.write('Link  Agent Map# Link Origin\n')
                fout.write('                 Link Destination\n')
                fout.write('----------------------------------\n')
                #             1234112345612345 name
                
                last_link_from_other_agent = 0
                for i in xrange(self.m):
                    p,q = self.orderedEdges[i]
                    
                    linkagent = self.link2agent[i]

                    # Put a star by links that can be completed early since they complete no fields
                    numfields = len(self.a.edge[p][q]['fields'])
                    if numfields == 0:
                        star = '*'
#                        print '%s %s completes nothing'%(p,q)
                    else:
                        star = ''
#                        print '%s %s completes'%(p,q)
#                        for t in self.a.edge[p][q]['fields']:
#                            print '   ',t

                    if linkagent != agent:
                        fout.write(plainStr.format(\
                            i,\
                            star,\
                            linkagent+1,\
                            self.nslabel[p],\
                            self.names[p],\
                            self.nslabel[q],\
                            self.names[q]\
                        ))
                        last_link_from_other_agent = 1
                    else:
                        if last_link_from_other_agent:
                            fout.write('\n')
                        last_link_from_other_agent = 0
                        fout.write(hilitStr.format(\
                            i,\
                            star,\
                            linkagent+1,\
                            self.nslabel[p],\
                            self.names[p],\
                            self.nslabel[q],\
                            self.names[q]\
                        ))
    def animate(self):
        # show or save a sequence of images demonstrating how the plan would unfold
        from matplotlib.patches import Polygon

        fig = plt.figure()
        ax  = fig.add_subplot(111)

        GREEN     = ( 0.0 , 1.0 , 0.0 , 0.3)
        BLUE      = ( 0.0 , 0.0 , 1.0 , 0.3)
        RED       = ( 1.0 , 0.0 , 0.0 , 0.5)
        INVISIBLE = ( 0.0 , 0.0 , 0.0 , 0.0 )

        portals = np.array([self.a.node[i]['xy'] for i in self.a.nodes_iter()]).T
        
        # Plot all edges lightly
        def dashAllEdges():
            for p,q in self.a.edges_iter():
                plt.plot(portals[0,[p,q]],portals[1,[p,q]],'k:')

        aptotal = 0

        edges   = []
        patches = []

        plt.plot(portals[0],portals[1],'go')
#        plt.plot(portals[0],portals[1],'bo')

        dashAllEdges()

        plt.title('AP:\n%s'%commaGroup(aptotal),ha='center')
        plt.axis('off')
        plt.savefig(self.outputDir+'frame_-1.png'.format(i))
        plt.clf()

        for i in xrange(self.m):
            p,q = self.orderedEdges[i]
#            print p,q,self.a.edge[p][q]['fields']

            plt.plot(portals[0],portals[1],'go')
#            plt.plot(portals[0],portals[1],'bo')

            # Plot all edges lightly
            dashAllEdges()

            for edge in edges:
                plt.plot(edge[0],edge[1],'g-')
#                plt.plot(edge[0],edge[1],'b-')

            # We'll display the new fields in red
            newPatches = []
            for tri in self.a.edge[p][q]['fields']:
#                print 'edge has a field'
                coords = np.array([ self.a.node[v]['xy'] for v in tri ])
                newPatches.append(Polygon(shrink(coords.T).T,facecolor=RED,\
                                                 edgecolor=INVISIBLE))
#                newPatches.append(Polygon(shrink(coords.T).T,facecolor=GREEN,\
#                                                 edgecolor=INVISIBLE))
#            print '%s new patches'%len(newPatches)
            
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
#            plt.plot(newEdge[0],newEdge[1],'g-')

            ax = plt.gca()
#            print 'adding %s patches'%len(patches)
            for patch in patches:
                ax.add_patch(patch)

            ax.set_title('AP:\n%s'%commaGroup(aptotal),ha='center')
            ax.axis('off')
            plt.savefig(self.outputDir+'frame_{0:02d}.png'.format(i))
            ax.cla()

            for patch in newPatches:
                patch.set_facecolor(GREEN)
#                patch.set_facecolor(BLUE)

        plt.plot(portals[0],portals[1],'go')
#        plt.plot(portals[0],portals[1],'bo')
        for edge in edges:
            plt.plot(edge[0],edge[1],'g-')
#            plt.plot(edge[0],edge[1],'b-')
        for patch in patches:
            ax.add_patch(patch)

        ax.set_title('AP:\n%s'%commaGroup(aptotal),ha='center')
        ax.axis('off')
        plt.savefig(self.outputDir+'frame_%s.png'%self.m)
        ax.cla()

    def split3instruct(self):
        portals = np.array([self.a.node[i]['xy'] for i in self.a.nodes_iter()]).T
        
        gen1 = self.a.triangulation

        oldedges = []

        plt.plot(portals[0],portals[1],'go')

        plt.axis('off')
        plt.savefig(self.outputDir+'depth_-1.png')
        plt.clf()

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
            plt.savefig(self.outputDir+'depth_{0:02d}.png'.format(depth))
            plt.clf()

            depth += 1

        plt.plot(portals[0],portals[1],'go')

        for edge in oldedges:
            plt.plot(edge[0],edge[1],'k-')

        plt.axis('off')
        plt.savefig(self.outputDir+'depth_%s.png'%depth)
        plt.clf()

