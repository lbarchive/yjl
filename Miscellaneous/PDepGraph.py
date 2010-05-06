#!/usr/bin/python
#
# PDepGraph generates dependency graph data for being processed in Graphviz.
#
# This code is in Publid Domain.
#
# Author:
#  2009, 2010 Yu-Jie Lin
#
# Dependencies:
#  1. gentoolkit
#  2. Graphviz - Optional, but need it to generate real graph.


from optparse import OptionParser
import sys


DEBUG = False
QUIET = False
DEP_TYPE_COLOR = {'ct': 'red', 'pm': 'green', 'rt': 'blue'}


def p(msg, lr=True):

  if QUIET:
    return

  if lr:
    print >> sys.stderr, msg
  else:
    print >> sys.stderr, msg,

def p_dbg(msg):

  if QUIET or not DEBUG:
    return
  p('DEBUG: %s' % msg)


def p_err(msg):
  
  if QUIET:
    return
  p('ERROR: %s' % msg)


sys.path += ['/usr/lib/gentoolkit/pym']


try:
  from gentoolkit.helpers import find_packages as find_pkgs
  from gentoolkit.helpers import find_all_packages as find_all_pkgs
  from gentoolkit.helpers import find_all_installed_packages as find_all_installed_pkgs
  from gentoolkit.helpers import split_package_name
except ImportError:
  p('You do not seem to have package gentoolkit. Run `emerge gentoolkit` first.')
  sys.exit(1)


def split_pkg_name(pkg_name):

  names = split_package_name(pkg_name)
  if names[3] == 'r0':
    names[3] = ''
  return names


def get_ver_rev(pkg_name):

  names = split_package_name(pkg_name)
  if names[3] == 'r0':
    return names[2]
  else:
    return '-'.join(names[2:])


def conflict_pkgs(pkgs):

  cat = pkgs[0].get_category()
  conflicted = filter(lambda pkg: cat != pkg.get_category(), pkgs[1:])
  if conflicted:
    return True
  return False


def find_pkg(pkg_name):

  # Check if slot is in search key
  if ':' not in pkg_name:
    found_pkgs = find_pkgs(pkg_name)
  else:
    new_pkg_name, slot = pkg_name.split(':')
    tmp_found_pkgs = find_pkgs(new_pkg_name)
    # Only keep those in same slot
    found_pkgs = []
    for pkg in tmp_found_pkgs:
      if pkg.get_env_var('SLOT') == slot:
        found_pkgs += [pkg]

  if len(found_pkgs) == 0:
    return
  elif len(found_pkgs) > 1:
    # Checking if conflict
    if conflict_pkgs(found_pkgs):
      p_err('Conflicting package name "%s":' % pkg_name)
      for pkg in found_pkgs:
        p_err(' %s' % pkg.get_cpv())
      return
    else:
      # Choose latest version/revision
      pkg = found_pkgs[0]
      for pkg_next in found_pkgs[1:]:
        if pkg.compare_version(pkg_next) == -1:
          pkg = pkg_next
  else:
    pkg = found_pkgs[0]
  del found_pkgs
  
  return pkg


def process_pkg(pkg_name, pkgs, pkg_pool):

  global options

  pkg = find_pkg(pkg_name)
  if not pkg:
    return

  if options.only_installed and not pkg.is_installed():
    return
  if pkg.get_name() == 'portage':
    p_dbg(repr(pkg.get_runtime_deps()))
  cpv = pkg.get_cpv()
  if cpv in pkgs:
    p_dbg('Already processed package %s' % cpv)
    return
  else:
    p_dbg('Processing package %s' % cpv)

  p_pkg = {'cpv': pkg.get_cpv(), 'deps': [], 'installed': pkg.is_installed(), 'found': True}

  # Process dependencies
  for check_dep_type in options.check_dep_types:
    if check_dep_type == 'ct':
      deps = pkg.get_compiletime_deps()
    elif check_dep_type == 'pm':
      deps = pkg.get_postmerge_deps()
    elif check_dep_type == 'rt':
      deps = pkg.get_runtime_deps()

    for dep in deps:
      # dep = (comparator, [use flags], cpv)
      # Find dependency package with criterion, which is the comparator
      if not (options.show_uses or options.only_used_uses) and len(dep[1]) > 0:
        p_dbg('%s: dep %s is optional dependency, dropped' % (cpv, dep[2]))
        continue
      
      dep_pkg = find_pkg(dep[0] + dep[2])
      # Check if this dependency is enabled by USE flag
      used = False
      uses = pkg.get_use_flags().replace('\n', '').split(' ')
      for dep_use in dep[1]:
        neg = False
        if dep_use[0] == '!':
          dep_use = dep_use[1:]
          neg = True
        if not (dep_use in uses) ^ neg:
          break
      else:
        used = True
      if options.only_used_uses and not used:
        p_dbg('%s: dep %s dropped, USEs not satifified' % (cpv, dep[2]))
        continue

      if dep_pkg:
        installed = dep_pkg.is_installed()
        dep_pkg_cpv = dep_pkg.get_cpv()
        if options.only_installed and not installed:
          p_dbg('%s: dep %s dropped, not installed' % (cpv, dep_pkg_cpv))
          if dep_pkg_cpv not in pkgs and not options.only_installed:
            pkgs[dep_pkg_cpv] = {'cpv': dep_pkg_cpv, 'deps': [], 'installed': installed, 'found': True}
          continue
        if dep_pkg.get_name() not in options.stop_deps and \
            dep_pkg.get_category() not in options.stop_cats:
          pkg_pool += [dep_pkg_cpv]
        elif dep_pkg_cpv not in pkgs:
          pkgs[dep_pkg_cpv] = {'cpv': dep_pkg_cpv, 'deps': [], 'installed': installed, 'found': True}
        p_pkg['deps'] += [(dep, dep_pkg_cpv, check_dep_type, used)]
        p_dbg('%s: added dep %s' % (cpv, dep_pkg_cpv))
      else:
        if dep[2] not in pkgs:
          pkgs[dep[2]] = {'cpv': dep[2], 'deps': [], 'installed': False, 'found': False}
        p_pkg['deps'] += [(dep, dep[2], check_dep_type, used)]
        p_err('%s: failed to find dep %s' % (cpv, dep[0] + dep[2]))

  pkgs[cpv] = p_pkg


def generate_DOT(pkgs, out):

  global options
  
  out('''digraph Portage {
rankdir=LR
node [shape=plaintext, fontname=Terminus, fontsize=8.0, fontcolor=black];
''')
  # Print all packages
  for pkg_name in pkgs:
    pkg = pkgs[pkg_name]
    names = split_pkg_name(pkg_name)
    pkg_attrs = {'fontname': 'Terminus', 'fontsize': '8.0', 'fontcolor': 'black', 'label': r'"%s\n%s"' % ('%s/%s' % (names[0], names[1]), get_ver_rev(pkg_name))}
    if pkg['installed']:
      pkg_attrs['shape'] = 'box'
    else:
      pkg_attrs['shape'] = 'plaintext'
    if not pkg['found']:
      pkg_attrs['fillcolor'] = 'red'
      pkg_attrs['fontcolor'] = 'white'
      pkg_attrs['style'] = 'filled'
    if names[1] in options.stop_deps or names[0] in options.stop_cats:
      pkg_attrs['fontcolor'] = 'white'
      pkg_attrs['fillcolor'] = 'blue'
      pkg_attrs['style'] = 'filled'
    out(r'"%s" [%s];' % (pkg_name, ','.join(['%s=%s' % (k, v) for k, v in pkg_attrs.items()])))

  # Print all deps
  for pkg_name in pkgs:
    pkg = pkgs[pkg_name]
    for dep in pkg['deps']:
      if options.revdep:
        dep_info, dep_pkg_cpv, dep_type, used, revdep_pkg_cpv = dep
      else:
        dep_info, dep_pkg_cpv, dep_type, used = dep
      dep_attrs = {'fontname': 'Terminus', 'fontsize': '8.0', 'fontcolor': 'black', 'color': DEP_TYPE_COLOR[dep_type]}
      if dep_info[0]:
        # Has comparator
        dep_attrs['label'] = '"%s"' % (dep_info[0] + get_ver_rev(dep_info[2]))
      elif ':' in dep_info[2]:
        # A SLOT dependency
        dep_attrs['label'] = '":%s"' % dep_info[2].split(':')[1]
      if dep_info[1]:
        dep_attrs['style'] = 'dashed'
        # TODO put USE flags into dep_attrs['label']
      if used:
        # This dependency is enabled by USE flag
        dep_attrs['penwidth'] = '2'
      if options.revdep:
        out('"%s" -> "%s" [%s]' % (revdep_pkg_cpv, pkg_name, ','.join(['%s=%s' % (k, v) for k, v in dep_attrs.items()])))
      else:
        out('"%s" -> "%s" [%s]' % (pkg_name, dep_pkg_cpv, ','.join(['%s=%s' % (k, v) for k, v in dep_attrs.items()])))
  out('}')


def generate_revdeps(pkg_name=None):
  '''Generates reverse dependencies package database with critera in options'''

  global options

  if not options.find_orphaned:
    pkg = find_pkg(pkg_name)
    if not pkg:
      return {}
      
    if options.stop_deps and pkg_name in options.stop_deps:
      options.stop_deps.remove(pkg_name)

  if options.only_installed:
    p('Retrieving all installed packages information...', False)
    found_pkgs = find_all_installed_pkgs()
  else:
    p('Retrieving all packages information, should take a quite long time...', False)
    found_pkgs = find_all_pkgs()
  p('%d packages' % len(found_pkgs))

  p('Calculating reverse dependencies...')
  all_pkgs = {}
  for pkg in found_pkgs:
    cpv = pkg.get_cpv()
    all_pkgs[cpv] = {'cpv': cpv, 'deps': [], 'installed': pkg.is_installed(), 'found': True}

  for pkg in found_pkgs:
    cpv = pkg.get_cpv()
    # Process dependencies
    for check_dep_type in options.check_dep_types:
      if check_dep_type == 'ct':
        deps = pkg.get_compiletime_deps()
      elif check_dep_type == 'pm':
        deps = pkg.get_postmerge_deps()
      elif check_dep_type == 'rt':
        deps = pkg.get_runtime_deps()

      for dep in deps:
        # dep = (comparator, [use flags], cpv)
        # Find dependency package with criterion, which is the comparator
        if not (options.show_uses or options.only_used_uses) and len(dep[1]) > 0:
          p_dbg('%s: dep %s is optional dependency, dropped' % (cpv, dep[2]))
          continue
        
        dep_pkg = find_pkg(dep[0] + dep[2])
        if dep_pkg and dep_pkg.get_cpv() in all_pkgs:
          installed = dep_pkg.is_installed()
          dep_pkg_cpv = dep_pkg.get_cpv()
          if not options.find_orphaned:
            if dep_pkg.get_name() in options.stop_deps or \
                dep_pkg.get_category() in options.stop_cats:
              p_dbg('%s: dep %s dropped, no follow' % (cpv, dep_pkg_cpv))
              continue

          # Check if this dependency is enabled by USE flag
          used = False
          uses = pkg.get_use_flags().replace('\n', '').split(' ')
          for dep_use in dep[1]:
            neg = False
            if dep_use[0] == '!':
              dep_use = dep_use[1:]
              neg = True
            if not (dep_use in uses) ^ neg:
              break
          else:
            used = True
          if options.only_used_uses and not used:
            p_dbg('%s: dep %s dropped, USEs not satifified' % (cpv, dep_pkg_cpv))
            continue

          all_pkgs[dep_pkg_cpv]['deps'] += [(dep, dep_pkg_cpv, check_dep_type, used, cpv)]
          p_dbg('%s: added as revdep to %s' % (cpv, dep_pkg_cpv))
        else:
          # In revdeps, unfound dep package is no way to show up in graph. So just drop it.
          p_dbg('%s: dep %s not existed, dropped' % (cpv, dep[2]))
  p('Finished calculating reverse dependencies')

  if options.find_orphaned:
    pkgs = {}
    for cpv in all_pkgs:
      if not all_pkgs[cpv]['deps']:
        pkgs[cpv] = all_pkgs[cpv]
    return pkgs

  p('Starting to walk for reverse dependencies of %s' % pkg_name)
  pkg = find_pkg(pkg_name)
  if not pkg or pkg.get_cpv() not in all_pkgs:
    return {}
  cpv = pkg.get_cpv()

  # Store used packages
  pkgs = {}

  def walker(cpv, pkgs, all_pkgs):
    
    if cpv in pkgs:
      return

    pkgs[cpv] = all_pkgs[cpv]
    
    pkg = pkgs[cpv]
    for dep in pkg['deps']:
      walker(dep[4], pkgs, all_pkgs)

  walker(cpv, pkgs, all_pkgs)

  return pkgs


def parse_args():

  global options, args
  
  parser = OptionParser(usage='%prog [options] package', )
  parser.add_option('-n', '--rev-deps', dest='revdep', action='store_true',
      default=False, help='Reverse dependencies mode, better to use with -i or may result with thousands of packags and could take really long time to process')
  parser.add_option('-c', '--ctdeps', dest='ctdeps', action='store_true',
      default=False, help='Show compile time dependencies')
  parser.add_option('-p', '--pmdeps', dest='pmdeps', action='store_true',
      default=False, help='Show post merge dependencies')
  parser.add_option('-r', '--rtdeps', dest='rtdeps', action='store_true',
      default=True, help='Show run time dependencies (default)')
  parser.add_option('-R', '--no-rtdeps', dest='rtdeps', action='store_false',
      default=True, help='Do not show run time dependencies')
  parser.add_option('-i', '--only-installed', dest='only_installed', action='store_true',
      default=False, help='Show only installed package')
  parser.add_option('-u', '--show-uses', dest='show_uses', action='store_true',
      default=False, help='Show dependencies with USE flag attached')
  parser.add_option('-U', '--only-used-uses', dest='only_used_uses', action='store_true',
      default=False, help='Show dependencies with USE flag attached and acutally used in installing time. This implies -u.')
  parser.add_option('-C', '--stop-cats', dest='stop_cats',
      default='virtual', help='Do follow dependencies in these categories, currently no use with -n (default: %default)')
  parser.add_option('-D', '--stop-deps', dest='stop_deps',
      default='alsa-lib,cairo,curl,db,eselect,fontconfig,glib,glibc,gnome-vfs,gtk+,hal,java-config,libglade,libgnome,libgnomeui,libtool,libXft,libxml2,libxslt,openldap,pam,pango,perl,python,qt-gui,udev,vim,XML-Parser,xorg-server', help='Do follow these dependencies, currently no use with -n (default: %default)')
  parser.add_option('-O', '--find-orphaned', dest='find_orphaned', action='store_true',
      default=False, help='Find orphaned packages, which are not required by others. Should run with -iU')
  parser.add_option('-H', '--more-help', dest='help', action='store_true',
      default=False, help='Show more help')
  parser.add_option('-d', '--debug', dest='debug', action='store_true',
      default=False, help='Show debug messages')
  parser.add_option('-q', '--quiet', dest='quiet', action='store_true',
      default=False, help='Quiet mode')
  parser.add_option('-o', '--out', dest='out',
                    help='write Graphviz DOT to FILE. Using standard output if not specifed.', metavar='FILE')
  options, args = parser.parse_args()

  if options.help:
    print '''Legend:
 Package Shape:
  None   = The package is not installed
  Box    = The package is installed
 Package Color:
  Red    = The package could not be found
  Blue   = The package is stopped being followd
 Arrow Color:
  Red    = Compile time dependency
  Green  = Post merge dependency
  Blue   = Run time dependency
 Arrow Thickness:
  Thick  = The dependency is enabled by USE flags at installing time
  Thin   = The dependency is not enabled by USE flags at installing time
 Arrow Style:
  Solid  = Required dependency
  Dashed = Optional by USE flags
'''
    sys.exit(0)

  options.stop_cats = options.stop_cats.split(',')
  options.stop_deps = options.stop_deps.split(',')

  DEBUG = options.debug
  QUIET = options.quiet

  check_dep_types = []
  if options.ctdeps:
    check_dep_types += ['ct']
  if options.pmdeps:
    check_dep_types += ['pm']
  if options.rtdeps:
    check_dep_types += ['rt']
  options.check_dep_types = check_dep_types


if __name__ == '__main__':

  global options, args

  parse_args()

  out = options.out
  if out:
    f_out = open(out, 'w')
  else:
    f_out = sys.stdout

  if options.find_orphaned:
    pkgs = generate_revdeps()
  elif options.revdep:
    pkgs = generate_revdeps(args[0])
  else:
    # Store all packages are needed
    pkgs = {}
    # A queue of packages waiting to process
    pkg_pool = [args[0]]

    while pkg_pool:
      pkg_name = pkg_pool.pop()
      process_pkg(pkg_name, pkgs, pkg_pool) 

  p('Result %d packages' % len(pkgs))

  def print_out(msg):
    print >> f_out, msg

  if options.find_orphaned:
    cpvs = pkgs.keys()
    cpvs.sort()
    print_out('\n'.join(cpvs))
  else:
    generate_DOT(pkgs, print_out)

  if out:
    f_out.close()
    if not options.find_orphaned:
      p('\nGenerate graph using `dot -T [svg|png|...] -o OUTPUT %s`')
