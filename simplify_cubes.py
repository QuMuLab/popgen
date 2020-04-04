
import sys

with open(sys.argv[1]) as f:
    content = f.readlines()

content = [line.split('Hitting set:')[1].strip() for line in content]

HS = [set(map(int, line.split(' '))) for line in content]

print "\nOriginal cubes: %d" % len(HS)

changed = True
while changed:
    changed = False
    for i in range(len(HS)-1):
        for j in range(i+1, len(HS)):
            hs1, hs2 = HS[i], HS[j]
            sym_diff = hs1 ^ hs2
            if 2 == len(sym_diff) and 0 == sum(sym_diff):
                HS.append(hs1 - sym_diff)
                changed = True
            if changed:
                break
        if changed:
            break
    if changed:
        HS = HS[:i] + HS[i+1:j] + HS[j+1:]

print "Combined cubes: %d" % len(HS)

new = []
for hs1 in HS:
    subsumed = False
    for hs2 in HS:
        if hs2 < hs1:
            subsumed = True
            break
    if not subsumed:
        new.append(hs1)

HS = new
print "Non-subsumed cubes: %d" % len(HS)

print
print "\n".join([str(sorted(list(hs))) for hs in HS])

