# POPGEN

Methods for deordering and reordering partial order plans.

## Disclaimer

This code is from half-a-decade ago, and is in need of some serious updating. This will likely come in the form of a rewrite using libraries such as [[bauhaus](https://github.com/qumulab/bauhaus)], but until that time please be aware that things may no longer be working with modern libraries.

## Usage

```bash
# Encode a given problem+plan into a MaxSAT instance
$ python popgen/encoder.py --domain d.pddl --problem p.pddl --plan p.plan --output out.wcnf

# Solve the MaxSAT instance
$ rc2.py -vv out.wcnf > out.sol

# Decode the solution back into a plan
$ python popgen/analyzer.py --map out.wcnf.map --rc2out out.sol --print-solution --show-popstats --count-linearizations
```

## Requirements

- [pysat](https://pysathq.github.io/)
- [bauhaus](https://bauhaus.readthedocs.io/)

## Citing This Work

```latex
@article{jair-popgen,
  author    = {Christian Muise and J. Christopher Beck and Sheila A. McIlraith},
  title     = {Optimal Partial-Order Plan Relaxation via MaxSAT},
  journal   = {Journal of Artificial Intelligence Research},
  year      = {2016},
  url       = {http://www.jair.org/media/5128/live-5128-9534-jair.pdf}
}
```
