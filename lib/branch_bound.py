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
import numpy as np

class CantSplit(Exception):
    pass

# This could be used if more splits are wanted than are possible
class InfState:
    def __init__(self):
        self.value = np.inf
    def split(self,num):
        raise CantSplit()

def branch_bound(root,lo,hi,callback=None):
    '''
    Uses a branch-and-bound style approach to minimize a function

    hi: maximum number of branches to obtain at each level
    lo: number of branches to explore further
    callback: function called at the beginning of every iteration

    The tree will grow up to 'hi' branches and then be trimmed down to 'lo'

    root: is an instance of a state class with callable split(num)
            create an iterable of functin values "root.values"
        each member of root.children should also be a state class
        members of root.values correspond to members of root.children

    returns s,v (the state and lowest found value)
    '''
    if callback == None:
        def callback():
            pass

    # number of branches to make from each branch
    # this number could be different for each branch, e.g. proportional to value
    splitSize = hi // lo

    states = [root]
    finals = [] # Terminating states

    while len(states) > 0:
        callback()

        # The branches of the states
        branches = []
        for state in states:
            try:
                branches.extend(state.split(splitSize))
#                print len(branches),'branches'
            except CantSplit:
                finals.append(state)
                break

        branchvalues = [branch.value for branch in branches]
        bestlo = np.argsort(branchvalues)[:lo]
        states = [branches[i] for i in bestlo]


    best = np.argmin([s.value for s in finals])
#    print finals[0].value
#    print finals[-1].value
    return finals[best],finals[best].value

