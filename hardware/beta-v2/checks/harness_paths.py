# -*- coding: utf-8 -*-
"""Cross-platform path resolution for the Full Beta v2 check/routing harness.

FBV2-CLOUD-001.  Until this task the harness carried three workstation-specific
assumptions baked in as string literals:

    KC       = r"P:/New folder (2)/bin/kicad-cli.exe"
    AUTH_DIR = r"P:/Vaults/ClaudeVault/AQROOT/hardware/beta-v2/kicad/aqroot-beta-v2"
    usage    = "P:/New folder (2)/bin/python.exe" ...

Every one of those is true only on the original Windows development machine.
None of them is a property of the PROJECT, and none of them can be true on the
Ubuntu cloud worker -- yet the scripts that carry them are the ones that decide
whether copper is allowed onto the authoritative board.  A harness that cannot
run on a second machine cannot be independently re-verified, so the literals had
to go somewhere they could be resolved instead of assumed.

The three policies live here, once, so a future portability defect has one place
to be fixed rather than four:

  * kicad_cli()   -- KICAD_CLI env var, then PATH, then documented Windows
                     fallbacks, then a LOUD failure.  Never a silent default.
  * project_dir() -- derived from THIS file's location by walking
                     checks/ -> beta-v2/ -> hardware/ -> repository root.
                     Nothing about the username, the mount point, the home
                     directory or the Obsidian vault path enters into it.
  * python_exe()  -- sys.executable, always.  Whichever interpreter can import
                     pcbnew is by definition the one a child process needs.

Environment overrides exist for both, so a Windows machine with KiCad somewhere
unusual, or a checkout mounted somewhere unusual, stays fully supported by
SUPPLYING a path rather than by the harness guessing one.
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# checks/ -> beta-v2/ -> hardware/ -> repository root.  os.pardir rather than
# '..' so the walk is spelled the same way on both platforms.
REPO_ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, os.pardir))

PROJECT_NAME = 'aqroot-Beta-v2'
PCBNAME = PROJECT_NAME + '.kicad_pcb'
DRUNAME = PROJECT_NAME + '.kicad_dru'
PRONAME = PROJECT_NAME + '.kicad_pro'

# Files/directories that must sit beside a .kicad_pcb for DRC to measure against
# the PROJECT's rules instead of KiCad's defaults.  This is the G1 guard of
# router_regression.py, stated once.
PROJECT_CONTEXT = (DRUNAME, PRONAME, 'fp-lib-table', 'sym-lib-table', 'libraries')

# Consulted on Windows ONLY, and only after KICAD_CLI and PATH have both come up
# empty.  The first entry is the historical development machine; the second is
# the KiCad 10 default installer location.  A Linux worker never reaches here.
_WINDOWS_KICAD_CLI_FALLBACKS = (
    r'P:/New folder (2)/bin/kicad-cli.exe',
    r'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe',
)

_kicad_cli_cache = []


def project_dir():
    """Absolute path to the authoritative Full Beta v2 KiCad project."""
    override = os.environ.get('AQROOT_BETA_V2_PROJECT')
    if override:
        d = os.path.abspath(override)
        if not os.path.isdir(d):
            raise SystemExit(
                'AQROOT_BETA_V2_PROJECT is set to %r, which is not a directory.' % override)
        return d
    return os.path.join(REPO_ROOT, 'hardware', 'beta-v2', 'kicad', 'aqroot-beta-v2')


def project_file(name):
    return os.path.join(project_dir(), name)


def missing_project_context(pcb_dir):
    """Names from PROJECT_CONTEXT absent beside `pcb_dir`.  Empty list = complete."""
    d = os.path.dirname(os.path.abspath(pcb_dir)) if os.path.isfile(pcb_dir) else pcb_dir
    return [n for n in PROJECT_CONTEXT if not os.path.exists(os.path.join(d, n))]


def kicad_cli():
    """Resolve the kicad-cli executable, or fail loudly saying how to fix it.

    Order: KICAD_CLI, then PATH, then -- on Windows only -- the documented
    installer locations.  There is deliberately no silent default: a DRC run
    against a kicad-cli that is not there must not look like a DRC run that
    found nothing wrong.
    """
    if _kicad_cli_cache:
        return _kicad_cli_cache[0]

    tried = []
    env = os.environ.get('KICAD_CLI')
    if env:
        tried.append('KICAD_CLI=%s' % env)
        cand = env if os.path.isfile(env) else shutil.which(env)
        if cand:
            _kicad_cli_cache.append(cand)
            return cand

    tried.append('shutil.which("kicad-cli")')
    cand = shutil.which('kicad-cli')
    if cand:
        _kicad_cli_cache.append(cand)
        return cand

    if os.name == 'nt':
        for p in _WINDOWS_KICAD_CLI_FALLBACKS:
            tried.append(p)
            if os.path.isfile(p):
                _kicad_cli_cache.append(p)
                return p

    raise SystemExit(
        'kicad-cli could not be resolved on this machine (%s).\n'
        'Tried, in order:\n  %s\n'
        'Fix it by putting kicad-cli on PATH, or by setting KICAD_CLI to its '
        'full path, e.g.\n'
        '  Linux:   export KICAD_CLI=/usr/bin/kicad-cli\n'
        '  Windows: set KICAD_CLI=C:\\Program Files\\KiCad\\10.0\\bin\\kicad-cli.exe'
        % (sys.platform, '\n  '.join(tried)))


def python_exe():
    """The interpreter a child process should be launched with.

    Always sys.executable.  The harness needs pcbnew, and the only interpreter
    known to have it is the one already running -- on Windows that is KiCad's
    bundled python.exe, on the Ubuntu worker it is the venv python that has the
    distribution pcbnew on its path.  Hard-coding either is what broke.
    """
    return sys.executable
