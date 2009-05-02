#!/usr/bin/python
#
# PDepGraph generates dependency graph data for being processed in Graphviz.
#
# This code is in Publid Domain.
#
# Author:
#  2009 Yu-Jie Lin
#
# Dependencies:
#  1. gentoolkit
#  2. Graphviz - Optional, but need it to generate real graph.
#
# Usages:
#  Generate whole world
#   ./PDepGraph.py
#  Pipe result to Graphviz
#   ./PDepGraph.py | neato -T svg -o world.svg
#  Generate output of whole world to file world.DOT, then use Graphviz
#   ./PDepGraph.py -o world.DOT
#   neato -T svg -o world.svg world.DOT
#  Highlight package portage
#   ./PDepGraph.py -l portage
#  Generate dependency graph of package python
#   ./PDepGraph.py -p python


from optparse import OptionParser
from sets import Set
import sys

sys.path += ['/usr/lib/gentoolkit/pym']

try:
  import gentoolkit.helpers
except ImportError:
  print >> sys.stderr, 'You do not seem to have package gentoolkit. Run `emerge gentoolkit` first.'
  sys.exit(1)


def get_packages():

  packages = {}
  
  print >> sys.stderr, 'Retrieving packages information...',
  for package in gentoolkit.helpers.find_all_installed_packages():
    uses = package.get_use_flags().replace('\n', '').split(' ')
    uses += ['']

    # Find out which dependency is enabled by USE flag at the time of emerging.
    deps = []
    for dep in package.get_runtime_deps():
      # dep = (comparator, [use flags], cpv)
      for sub_dep in dep[1]:
        if sub_dep not in uses:
          break
      else:
        dep_name = dep[2].split('/')[1]
        # Remove version number if any
        if dep[0]:
          deps += [dep_name.rsplit('-', 1)[0]]
        else:
          deps += [dep_name]

    packages[package.get_name()] = {'revdeps': [], 'deps': deps}

  # Remove deps are not installed
  for name, value in packages.iteritems():
    new_deps = value['deps'][:]
    for dep in value['deps']:
      if dep not in packages:
        new_deps.remove(dep)
    if new_deps != value['deps']:
      packages[name]['deps'] = new_deps
  print >> sys.stderr, 'done.'

  print >> sys.stderr, 'Calculating reverse dependencies...',
  for name, value in packages.iteritems():
    for dep in value['deps']:
      packages[dep]['revdeps'] += [name]

  print >> sys.stderr, 'done.'
  
  print >> sys.stderr, 'Got %d packages.\n' % len(packages)
  return packages


def generate_DOT(packages, out, hl_pkg_name=''):

  max_revdeps = 0
  for name, value in packages.iteritems():
    if len(value['revdeps']) > max_revdeps:
      max_revdeps = len(value['revdeps'])
  max_revdeps = float(max_revdeps)

  print >> out, '''digraph Portage {
overlap=portho
splines=true
node [shape=plaintext, fontname=Terminus, fontsize=8.0, fontcolor=red];
'''
  for name, value in packages.iteritems():
    if max_revdeps > 0.0:
      r_revdeps = len(value['revdeps']) / max_revdeps
    else:
      r_revdeps = 0

    if hl_pkg_name and hl_pkg_name == name:
      print >> out, '"%s" [shape=ellipse, fontname=Terminus, fontsize=8.0, fontcolor=white, color=red, style=filled];' % name
    else:
      print >> out, '"%s" [shape=plaintext, fontname=Terminus, fontsize=8.0, fontcolor="#0000%2x"];' % (name, r_revdeps * 255)
  print >> out

  color_names = ['black', 'blue', 'blueviolet', 'brown', 'burlywood', 'cadetblue', 'chartreuse', 'chocolate', 'coral', 'cornflowerblue', 'crimson', 'darkgreen', 'deeppink', 'dimgray', 'dodgerblue', 'firebrick', 'forestgreen', 'gold', 'green', 'hotpink', 'indigo', 'limegreen', 'magenta', 'navy', 'orange', 'red', 'yellow']
  #color_names = ['lightblue', 'lightcoral', 'lightcyan', 'lightgoldenrod', 'lightgoldenrodyellow', 'lightgray', 'lightpink', 'lightsalmon', 'lightseagreen', 'lightskyblue', 'lightslateblue', 'lightslategray', 'lightyellow']
  i = 0
  for name, value in packages.iteritems():
    for revdep in value['revdeps']:
      print >> out, '"%s" -> "%s" [arrowhead=vee, arrowsize=0.5, color=%s];' % (name, revdep, color_names[i % len(color_names)])
    i += 1
  print >> out, '}'


def generate_dep_pkgs(packages, name):

  pkg_names = [name]

  def walker(packages, name, walked_pkgs):

    for pkg in packages[name]['deps']:
      if pkg in walked_pkgs:
        continue
      else:
        walked_pkgs += [pkg]
        walker(packages, pkg, walked_pkgs)

  walker(packages, name, pkg_names)

  # Clean up unwanted trails
  set_pkg_names = Set(pkg_names)
  pkgs = {}
  for pkg_name in pkg_names:
    pkg = packages[pkg_name]
    pkg['deps'] = list(Set(pkg['deps']) & set_pkg_names)
    pkg['revdeps'] = list(Set(pkg['revdeps']) & set_pkg_names)
    pkgs[pkg_name] = pkg

  print >> sys.stderr, 'Found %d packages for package %s.\n' % (len(pkgs), name)
  return pkgs


if __name__ == '__main__':
  parser = OptionParser()
  parser.add_option('-p', '--package', dest='package',
                    help='find dependencies of package, also set highlight.')
  parser.add_option('-l', '--highlight', dest='highlight',
                    help='highlight package.')
  parser.add_option('-o', '--out', dest='out',
                    help='write Graphviz DOT to FILE. Using standard output if not specifed.', metavar='FILE')
  (options, args) = parser.parse_args()

  packages = get_packages()

  package = options.package
  highlight = options.highlight
  out =  options.out
  if out:
    f_out = open(out, 'w')
  else:
    f_out = sys.stdout

  if package and package in packages:
    pkgs = generate_dep_pkgs(packages, package)
    highlight = package
  else:
    pkgs = packages

  if out:
    print >> sys.stderr, 'Writing to %s...' % out,
  
  generate_DOT(pkgs, f_out, highlight)
  
  if out:
    print >> sys.stderr, 'done.\n'
    print >> sys.stderr, 'Generate graph using `neato -T [svg|png|...] -o OUTPUT %s`' % out
