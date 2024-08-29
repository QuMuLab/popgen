
import random
from decimal import *

getcontext().prec = 30

from krrt.utils import write_file, append_file
from krrt.planning.strips.representation import Action

from popgen.pop import POP
from popgen.linearizer import compute_linflex

def doit(nActs, nFlex, nTrials):

    step = 1.0 / float(nFlex+1)
    acts = [Action(line=str(i)) for i in range(nActs)]
    all_edges = set([(u,v) for u in acts for v in acts])

    fn = "flex-vs-lins_%d-acts_%d-flexes_%d-trials.csv" % (nActs, nFlex, nTrials)
    write_file(fn, 'Flex,LinFlex\n')

    for flex in [step * i for i in range(1,nFlex+1)]:
        print("\nWorking on flex %f" % flex)
        for _ in range(nTrials):
            p = POP()
            for a in acts:
                p.add_action(a)
                p.link_actions(a, a, 'self-loop')

            while p.flex > flex:
                edges = all_edges - (set(p.network.edges()) | set([(v,u) for (u,v) in p.network.edges()]))
                (a1, a2) = random.choice(list(edges))
                p.link_actions(a1, a2, 'random')
                p.transativly_close()

            # Compute the stats
            f = p.flex
            lf = compute_linflex(p)
            print("%f / %f" % (f, lf))
            append_file(fn, "%.20f,%.20f\n" % (f, lf))
        print()


if __name__ == '__main__':
    import sys

    if len(sys.argv) != 4:
        print()
        print("Usage: python rand-grapher.py <num actions> <num flex amounts> <num trials>")
        print()
    else:
        doit(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
