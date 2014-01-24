AS OF 23 JAN. 2014, THIS CODE IS IRRELEVANT. LINKS CANNOT BE MADE TO PORTALS INSIDE FIELDS. THIS WAS THE FOUNDING PRINCIPLE OF THIS STRATEGY.

    -----Introduction-----

    This is for Ingress. If you don't know what that is, you're lost.

    This code is designed to make a plan for linking a given set of portals in the way (and the order) that creates the most fields. This is harder than it sounds. If you're working on more than a dozen portals, learning to use this code will be faster than planning by hand.

    -----Prerequisites-----

    You'll need Python (I've got 2.7) as well as networkx and numpy

    You can get these setup easily with the Enthought Python Distribution:
        https://www.enthought.com/downloads/

    -----Example-----

    I'll be distributing this code with a file EXAMPLE.csv. Try running
        >> python makePlan.py 4 EXAMPLE.csv output output.pkl
    This will put a bunch of files into the "output/" directory (see OUTPUT FILE LIST)
    
    Now try running
        >> python makePlan.py 3 out/output.pkl
    This uses the plan stored in output.pkl instead of calculating a new one. It will create files for 3 agents instead of 4.

    ----OUTPUT FILE LIST----

                keyPrep.txt
                    List of portals, their numbers on the map, and how many keys are needed

                keys_for_agent_M_of_N.txt
                    List of keys agent number M will need (if N agents are participating)

                links_for_agent_M_of_N.txt
                    List of ALL the links
                    Total distance traveled and AP earned by agent number M
                    * Except for the links marked with a star (*), the links should be made IN THE ORDER LISTED
                    * Links with a star can be made out of order, but only EARLY i.e. BEFORE their position in the list (this can save you time)
                    * The links that agent number M makes are marked with underscores__
                    * The first portal listed is the origin portal (where the agent must be)
                    * The second portal listed is the destination portal (for which the agent must have a key)

                portalMap.png
                    A map showing the locations of the portals
                    * Up is north
                    * Numbers correspond to keyPrep and the numbers preceeding portal names in linkes_for_agent_M_of_N.txt

                ownershipPrep.txt
                    List of portals whose first link is incoming
                    * You may be able to save time by capturing and fully powering some of the portals after linking has begun
                    * Portals whose first link is outgoing can be captured and powered by the first agent who needs to make a link from that portal

                lastPlan.pkl
                    A Python pickel file containing all portal and plan information
                    * The default name is "lastPlan.pkl"
                    * In the examples above, this is called "output.pkl"
    ----Warantee-----

    No promises

    -----Usage-----

    python createplan.py agent_count input_file [output_directory] [output_file]
    
    agent_count: Number of agents for which to make a plan
    
    input_file:  One of two types of files:
                   .csv   format:
                              portal name,latE6,lngE6[,keys]
                        
                          portal name should not contain commas
                          latE6 and lngE6 should be the portal's global coordinates
                          E6 means times 10^6 (no decimal)
                              e.g. the Big Ben portal is at 51500775,-124466
                          keys (optional parameter) is the number of keys you have for the portal
                              If you leave this blank, the program assumes you have no keys
                   
                   .pkl   an output from a previous run of this program
                          this can be used to make the same plan with a different number of agents

    output_directory: directory in which to put all output
                      default is the working directory

    output_file: name for a .pkl file containing information on the plan
                 if you use this for the input file, the same plan will be produced with the number of agents you specify
                 default: "lastPlan.pkl"

    -----Notes-----

    The space of possible max-field plans is large. Rather than trying every possibility, this program randomly tries some plans and presents you with one that doesn't require you to obtain too many more keys.

    If you don't like the plan you got, run it again. You'll probably get a different plan.



