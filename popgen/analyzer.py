
import argparse, json

from linearizer import count_linearizations
from pop import POP


def get_mapping(map_file):
    with open(map_file) as f:
        mapping = json.load(f)
    return mapping

def print_solution(mapping, output):

    with open(output) as f:
        output = f.readlines()

    varline = [x for x in output if x.startswith('v ')][0]
    values = varline.strip().split(' ')[1:]

    print("\nSolution:")
    for v in values:
        if '-' not in v:
            print("  " + mapping[v])


def do_popstats(mapping, output, show_linears = False):

    with open(output) as f:
        output = f.readlines()

    varline = [x for x in output if x.startswith('v ')][0]
    solline = [x for x in output if x.startswith('s ')][0]

    optiml = ('OPTIMUM FOUND' in solline)
    values = varline.strip().split(' ')[1:]




    # TODO: Continue from here...




    actions = set()
    act_mapping = {}
    orderings = []
    supports = []

    for v in [x for x in values if '-' not in x]:
        if 'in plan' in mapping[v]:
            act = Action(None, None, None, mapping[v].split(' in plan')[0][1:-1])
            act_mapping[mapping[v].split(' in plan')[0]] = act
            actions.add(act)
        elif 'is ordered before' in mapping[v]:
            orderings.append((act_mapping[mapping[v].split(' is ordered before ')[0]], act_mapping[mapping[v].split(' is ordered before ')[1]]))
        elif 'supports' in mapping[v]:
            supports.append((act_mapping[mapping[v].split(' supports ')[0]],
                             act_mapping[mapping[v].split(' supports ')[1].split(' with ')[0]],
                             mapping[v].split(' supports ')[1].split(' with ')[1]))
        else:
            print("Error: Unrecognized mapping line: %s" % mapping[v])

    pop = POP()

    for a in actions:
        pop.add_action(a)
        if a.operator == 'init':
            pop.init = a
        if a.operator == 'goal':
            pop.goal = a

    for (u,v) in orderings:
        pop.link_actions(u,v,'')

    for (a1, a2, p) in supports:
        pop.link_actions(a1,a2,p)

    #for a1 in actions:
    #    for a2 in actions:
    #        if (a1,a2) not in orderings and (a2,a1) not in orderings:
    #            print a1
    #            print a2

    if show_linears:
        print("\nLinearizations: %d\n" % count_linearizations(pop))

    print("\n%s\n" % str(pop))
    print("Optimal: %s" % str(optimal))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Analyze the output of the solved encoding')

    parser.add_argument('--map', help='The mapping file', required=True)
    parser.add_argument('--rc2out', help='The output from RC2', required=True)

    parser.add_argument('--print-solution', help='Print the solution', action='store_true')
    parser.add_argument('--show-popstats', help='Show the POP stats', action='store_true')
    parser.add_argument('--count-linearizations', help='Show the number of linearizations', action='store_true')

    args = parser.parse_args()

    if args.print_solution:
        print_solution(get_mapping(args.map), args.rc2out)

    if args.show_popstats:
        do_popstats(get_mapping(args.map), args.rc2out, args.count_linearizations)

