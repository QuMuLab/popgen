
import os
from domains import DOMAINS

os.system('mkdir benchmarks-allact-serial')

for dom in ['depots', 'driverlog', 'logistics', 'rovers', 'storage']:
    os.system('mkdir ' + dom + '-allact')
    os.system('mkdir ' + dom + '-allact-allgoal')
    for i in range(10):
        ffpath = 'RESULTS/plans/' + dom + '/' + DOMAINS[dom][i][1].split('/')[-1].split('.')[0] + '.ff'
        os.system("python encoder.py -domain %s -prob %s -ffout %s -output p%d ALLACT SERIAL" % (DOMAINS[dom][i][0],
                                                                                   DOMAINS[dom][i][1],
                                                                                   ffpath, i+1))
        os.system("mv p%d* %s" % (i+1, dom + '-allact'))

        os.system("python encoder.py -domain %s -prob %s -ffout %s -output p%d ALLACT SERIAL RELAXGOAL" % (DOMAINS[dom][i][0],
                                                                                             DOMAINS[dom][i][1],
                                                                                             ffpath, i+1))
        os.system("mv p%d* %s" % (i+1, dom + '-allact-allgoal'))

    os.system('mv ' + dom + '* benchmarks/')
