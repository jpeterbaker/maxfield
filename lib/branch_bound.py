
import numpy as np

class CantSplit(Exception):
    pass

# This could be used if more splits are wanted than are possible
class InfState:
    def __init__(self):
        self.value = np.inf
    def split(self,num):
        raise CantSplit()

def branch_bound(root,lo,hi):
    '''
    Uses a branch-and-bound style approach to minimize a function

    hi: maximum number of branches to obtain at each level
    lo: number of branches to explore further

    root: is an instance of a state class with callable nextstate()
        nextstate() should:
            create an iterable "root.children"
            create an iterable of functin values "root.values"
        each member of root.children should also be a state class
        members of root.values correspond to members of root.children

    returns s,v (the state and lowest found value)
    '''
    # number of branches to make from each branch
    # this number could be different for each branch, e.g. proportional to value
    splitSize = hi // lo

    states = np.array([root])

    print 'Planning agent movements:'

    # This is only for the printout
    counter = 0
    while True:
        # The branches of the states
        try:
            for state in states:
                state.split(splitSize)
        except CantSplit:
            # TODO For now, assume all states finish splitting at the same time
            break

        branches = np.array([ state.children for state in states])
        branches.shape = (-1)

        branchvalues = [branch.value for branch in branches]
        bestlo = np.argsort(branchvalues)[:lo]
        states = branches[bestlo]

        print counter
        counter += 1

    return states[0],states[0].value

if __name__=='__main__':
    class TSPstate:
        d = None
        n = -1
        def __init__(self,hist=[0],travel=0.,notHist=None):
            '''
            hist: list of points visited so far
            travel: distance travelled so far
            notHist: set of points NOT visited so far
            '''
            self.hist = hist
            self.value = travel
            if notHist == None:
                self.notHist = set(range(TSPstate.n))-set(hist)
            else:
                self.notHist = notHist

            if len(self.notHist) == 0:
                # Make it a loop
                self.value += TSPstate.d[hist[0],hist[-1]]
                self.hist.append(hist[0])

        def split(self,nchildren):
            if len(self.hist) > TSPstate.n:
                raise CantSplit()

            if nchildren > len(self.notHist):
                candidates = self.notHist
            else:
                nHarray = np.array(list(self.notHist))
                ranking = np.argsort(TSPstate.d[self.hist[-1],nHarray])
                candidates = nHarray[ranking[:nchildren]]

            self.children = []
            for cand in candidates:
                self.children.append(TSPstate(self.hist+[cand],\
                                              self.value+d[self.hist[-1],cand],\
                                              self.notHist-set([cand])))

    pts = np.array([[0,0],\
                    [1,0],\
                    [2,0],\
                    [3,0],\
                    [0,5]])

    dx = pts[:,0] - pts[:,0].reshape([-1,1])
    dy = pts[:,1] - pts[:,1].reshape([-1,1])

    d = np.zeros([6,6])

    d[:5,:5] = np.sqrt(dx**2+dy**2)

    TSPstate.d = d
    TSPstate.n = 6

    root = TSPstate([0])

    state,value = branch_bound(root,512,1024)

    print state.hist
    print value

