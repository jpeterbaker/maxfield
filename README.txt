
    -----Introduction-----

    This is for Ingress. If you don't know what that is, you're lost.

    This code is designed to make a plan for linking a given set of portals in the way (and the order) that creates the most fields. This is harder than it sounds. If you're working on more than a couple dozen portals, trust me, you'll make a mistake.

    -----Prerequisites-----

    You'll need Python (I've got 2.7) as well as networkx and numpy

    -----Example-----

    I'll be distributing this code with a file EXAMPLE.txt. Try running this

        >> python makePlan.py 4 EXAMPLE.txt output.pkl out

    This will put files int the "out/" directory explaining the link plan. I think these are reasonably self-explanatory if you just look at them.

    This will also put a file called "output.pkl" in "out/". This allows you to save the plan you've got and get the printouts for different numbers of agents. If you then run
        
        >> python makePlan.py 3 out/output.pkl

    You'll get files describing the same plan but for a different number of agents. If you run the first command again with 3 instead of 4, the randomness in the code will give you a whole new plan.

    ----Warantee-----

    No promises

    -----Usage-----

    python createplan.py agent_count input_file [output_directory] [output_file]
    
    agent_count: Number of agents for which to make a plan
    
    input_file:  One of two types of files:
                   .csv formatted as portal name,latE6,lngE6,keys
                        
                        portal name should not contain commas
                        latE6 and lngE6 should be the portal's global coordinates
                        E6 means times 10^6 (no decimal)
                            e.g. the Big Ben portal is at 51500775,-124466
                        keys is the number of keys you have for the portal
                   
                   .pkl an output from a previous run of this program
                        this can be used to make the same plan with a different number of agents

    output_directory: directory in which to put all output
                      default is the working directory

    output_file: name for a .pkl file containing information on the plan
                 if you use this for the input file, the same plan will be produced with the number of agents you specify
                 default: "lastPlan.pkl"

    -----Notes-----

    The space of possible max-field plans is large. Rather than trying every possibility, this program randomly tries some plans and presents you with one that doesn't require you to obtain too many more keys.

    If you don't like the plan you got, run it again. You'll probably get a different plan.



