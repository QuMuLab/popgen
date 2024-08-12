
# Depots
depots = []
for i in range(1,23):
    depots.append(('domains/depots/domain.pddl', "domains/depots/pfile%d" % i))

# Driverlog
# Domains above 15 cannot be solved by ff
driverlog = []
#for i in range(1,21):
for i in range(1,16):
    driverlog.append(('domains/driverlog/domain.pddl', "domains/driverlog/pfile%d" % i))

# Logistics
logistics = []
for i in range(1,10):
    logistics.append(('domains/logistics/domain.pddl', "domains/logistics/prob0%d.pddl" % i))
for i in range(10, 36):
    logistics.append(('domains/logistics/domain.pddl', "domains/logistics/prob%d.pddl" % i))

# Openstacks -- Note: problems above p07 are too large for FF
openstacks = []
for i in range(1,8):
#for i in range(1,10):
    openstacks.append(("domains/openstacks/domain_p0%d.pddl" % i, "domains/openstacks/p0%d.pddl" % i))
#for i in range(10, 31):
#    openstacks.append(("domains/openstacks/domain_p%d.pddl" % i, "domains/openstacks/p%d.pddl" % i))

# Rovers
# Domains above 34 cannot be encoded (memory or time)
rovers = []
for i in range(1,10):
    rovers.append(('domains/rovers/domain.pddl', "domains/rovers/p0%d.pddl" % i))
for i in range(10, 35):
    rovers.append(('domains/rovers/domain.pddl', "domains/rovers/p%d.pddl" % i))

# Storage
# Domains above 17 cannot be solved by ff
storage = []
for i in range(1,10):
    storage.append(('domains/storage/domain.pddl', "domains/storage/p0%d.pddl" % i))
for i in range(10, 18):
#for i in range(10, 31):
    storage.append(('domains/storage/domain.pddl', "domains/storage/p%d.pddl" % i))

# TPP
tpp = []
for i in range(1,10):
    #tpp.append(("domains/tpp/domain_p0%d.pddl" % i, "domains/tpp/p0%d.pddl" % i))
    tpp.append(("domains/tpp/domain.pddl", "domains/tpp/p0%d.pddl" % i))
for i in range(10, 31):
    #tpp.append(("domains/tpp/domain_p%d.pddl" % i, "domains/tpp/p%d.pddl" % i))
    tpp.append(("domains/tpp/domain.pddl", "domains/tpp/p%d.pddl" % i))

# Trucks
trucks = []
for i in range(1,10):
    trucks.append(("domains/trucks/domain_p0%d.pddl" % i, "domains/trucks/p0%d.pddl" % i))
for i in range(10, 31):
    trucks.append(("domains/trucks/domain_p%d.pddl" % i, "domains/trucks/p%d.pddl" % i))

# Zenotravel
zenotravel = []
for i in range(1,21):
    zenotravel.append(('domains/zenotravel/domain.pddl', "domains/zenotravel/pfile%d" % i))

# Manufactured dependent
dependent = []
for i in range(2,9):
    dependent.append(("domains/manufactured/dependent/domain%d.pddl" % i, "domains/manufactured/dependent/prob%d.pddl" % i))

# Manufactured dependent2
dependent2 = []
for i in range(2,11):
    dependent2.append(("domains/manufactured/dependent2/domain%d.pddl" % i, "domains/manufactured/dependent2/prob%d.pddl" % i))

# Manufactured pairs
pairs = []
for i in range(2,11):
    pairs.append(("domains/manufactured/pairs/domain%d.pddl" % i, "domains/manufactured/pairs/prob%d.pddl" % i))

# Manufactured parallel
parallel = []
for i in range(2,11):
    parallel.append(("domains/manufactured/parallel/domain%d.pddl" % i, "domains/manufactured/parallel/prob%d.pddl" % i))

# Manufactured tail
tail = []
for i in range(1,9):
    tail.append(("domains/manufactured/tail/domain%d0.pddl" % i, "domains/manufactured/tail/prob%d0.pddl" % i))

# FINAL
DOMAINS = {
    'depots': depots,
    'driverlog': driverlog,
    'logistics': logistics,
    'openstacks': openstacks,
    'rovers': rovers,
    'storage': storage,
    'tpp': tpp,
    'trucks': trucks,
    'zenotravel': zenotravel,
    'test-depots': depots[:3],
    'test-driverlog': driverlog[:3],
    'test-logistics': logistics[:3],
    'test-openstacks': openstacks[:3],
    'test-rovers': rovers[:3],
    'test-storage': storage[:3],
    'test-tpp': tpp[:3],
    'test-trucks': trucks[:3],
    'test-zenotravel': zenotravel[:3],
    'dependent': dependent,
    'dependent2': dependent2,
    'parallel': parallel,
    'tail': tail,
    'pairs': pairs
}

GOOD_DOMAINS = ['depots', 'driverlog', 'logistics', 'tpp', 'zenotravel', 'rovers', 'storage']




#########################################
##                                     ##
##  NEW: Use the planning.domains api  ##
##                                     ##
#########################################

import sys

print("Loading domains...", end=' ')
sys.stdout.flush()

import planning_domains_api as api

GOOD_DOMAINS = []
for dom in api.get_domains(12): # 12 is the collection for all STRIPS IPC domains
    probs = api.get_problems(dom['domain_id'])
    DOMAINS[str(dom['domain_name'])] = [(str(p['domain_path']), str(p['problem_path'])) for p in probs]
    GOOD_DOMAINS.append(str(dom['domain_name']))
GOOD_DOMAINS = sorted(GOOD_DOMAINS)

# Negative preconditions, numerics, or lack of solutions
FORBIDDEN_DOMAINS = ['childsnack', 'openstacks', 'settlers', 'tidybot']

# Low flex
FORBIDDEN_DOMAINS.extend([
    'visitall',
    'blocks-reduced',
    'sokoban',
    'pegsol',
    'ged',
    'parking',
    'barman',
    'gripper',
    'cybersec',
    'psr-small',
    'storage',
    'nomystery',
    'mystery',
    'mprime',
    'freecell',
    'hiking',
    'floortile',
    'thoughtful'
])

# Every plan is the same!!
FORBIDDEN_DOMAINS.append('movie')

print("done!")
#print GOOD_DOMAINS

