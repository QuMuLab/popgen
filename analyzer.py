from krrt.utils import get_opts, write_file, read_file, get_lines, match_value
from krrt.planning.strips.representation import parse_problem, generate_action, Action
from krrt.planning import parse_output_FF, parse_output_popf
from krrt.sat.CNF import Formula

from linearizer import count_linearizations
from pop import POP

import networkx as nx

USAGE_STRING = """
Usage: python analyzer.py -<option> <argument> -<option> <argument> ... <FLAG> <FLAG> ...

        Where options are:
          -map <map file>
          -minimaxout <minimaxsat output>
          -wcnf <wcnf file>
          -popstats <minimaxsat output>

        And the flags include:
          NOCOUNT: When doing -popstats, don't enumerate/count the linearizations
        """

def get_mapping(map_file):
    mapping = {}
    lines = read_file(map_file)
    for line in lines:
        mapping[line.split(' ')[0]] = ' '.join(line.split(' ')[1:])
        mapping['-'+line.split(' ')[0]] = 'NULL'
        #mapping['-'+line.split(' ')[0]] = 'Not ' + ' '.join(line.split(' ')[1:])
    return mapping

def do_minimaxout(mapping, output):

    # sat4j
    if match_value(output, 's OPTIMUM FOUND'):
        data = get_lines(output, 's OPTIMUM FOUND', 'c objective.*')
    else:
        data = get_lines(output, 's UPPER BOUND', 'c objective.*')

    values = data[1].strip().split(' ')[1:-1]

    # MaxHS
    #data = get_lines(output, 's OPTIMUM FOUND', 'c Optimum.*')
    #values = data[0].strip().split(' ')[1:]


    for v in values:
        if mapping[v] != 'NULL':
            print mapping[v]

def do_wcnf(mapping, output):
    data = get_lines(output, lower_bound='p .*')
    for line in data:
        print "Clause (%s):" % line.split(' ')[0]
        for lit in line.strip().split(' ')[1:-1]:
            if lit[0] == '-':
                print "  Not (%s)" % mapping[lit[1:]]
            else:
                print "  %s" % mapping[lit]

def do_popstats(mapping, output, disable_linears = False):

    # sat4j
    if match_value(output, 's OPTIMUM FOUND'):
        data = get_lines(output, 's OPTIMUM FOUND', 'c objective.*')
        optimal = True
    else:
        data = get_lines(output, 's UPPER BOUND', 'c objective.*')
        optimal = False

    # MaxHS
    #data = get_lines(output, 's OPTIMUM FOUND', 'c Optimum.*')
    #values = data[0].strip().split(' ')[1:]

    try:
        values = data[1].strip().split(' ')[1:-1]
        #values = data[0].strip().split(' ')[1:]
    except IndexError:
        print data
        print data[1]
        raise IndexError

    actions = set()
    act_mapping = {}
    orderings = []
    supports = []

    for v in filter(lambda x: '-' not in x, values):
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
            print "Error: Unrecognized mapping line: %s" % mapping[v]

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

    if not disable_linears:
        print "\nLinearizations: %d\n" % count_linearizations(pop)

    print "\n%s\n" % str(pop)
    print "Optimal: %s" % str(optimal)


if __name__ == '__main__':
    import os
    myargs, flags = get_opts()

    if not myargs.has_key('-map'):
        print "Must include the map file:"
        print USAGE_STRING
        os._exit(1)

    map_file = myargs['-map']

    if '-minimaxout' in myargs:
        do_minimaxout(get_mapping(map_file), myargs['-minimaxout'])

    if '-wcnf' in myargs:
        do_wcnf(get_mapping(map_file), myargs['-wcnf'])

    if '-popstats' in myargs:
        do_popstats(get_mapping(map_file), myargs['-popstats'], ('NOCOUNT' in flags))

