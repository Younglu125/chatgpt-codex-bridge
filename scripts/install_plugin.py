"""Stage and validate a plugin before replacing a managed personal installation."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid

from package_plugin import build

NAME = 'chatgpt-codex-bridge'
HELPERS = ('create_basic_plugin.py', 'read_marketplace_name.py', 'update_plugin_cachebuster.py')


def replace_bytes(path, content):
    """Replace one manifest atomically, preserving its previous bytes for rollback."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='.ccb-manifest-', dir=path.parent, delete=False) as file:
        temp = Path(file.name)
        file.write(content)
    try:
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def install(mode):
    codex_home = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
    helper = codex_home / 'skills/.system/plugin-creator/scripts'
    market = Path.home() / '.agents/plugins/marketplace.json'
    dest = Path.home() / 'plugins' / NAME
    codex = shutil.which('codex')
    if not codex:
        raise RuntimeError('Codex CLI is required; use the supported release marketplace UI instead.')
    missing = [name for name in HELPERS if not (helper / name).is_file()]
    if missing:
        raise RuntimeError('Official plugin-creator helpers unavailable: ' + ', '.join(missing)
                           + '. Use the release marketplace following README.')
    subprocess.run([codex, 'plugin', 'add', '--help'], check=True, capture_output=True)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with (dest.parent / '.ccb-install.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if dest.is_symlink() or market.is_symlink():
            raise RuntimeError('Refusing to replace a symlink installation or marketplace.')
        previous_market = market.read_bytes() if market.exists() else None
        entries = json.loads(previous_market)['plugins'] if previous_market is not None else []
        existing = next((x for x in entries if x['name'] == NAME), None)
        if existing and existing.get('source', {}).get('path') != './plugins/' + NAME:
            raise RuntimeError('Existing marketplace entry points elsewhere; resolve it before installing.')
        if dest.exists() and (not existing or not (dest / 'GENERATED.txt').is_file()):
            raise RuntimeError('Refusing to replace an unmanaged installation directory.')

        # Older installations have no mode record. Preserve those with a built backend.
        saved_mode = dest / 'INSTALLATION.json'
        old_mode = json.loads(saved_mode.read_text())['mode'] if saved_mode.exists() else None
        if old_mode not in {None, 'lite', 'full'}:
            raise RuntimeError('Unknown saved installation mode; inspect it before updating.')
        had_full = old_mode == 'full' or (dest / 'vendor/codex-with-chatgpt/dist/cli/index.js').is_file()
        selected = 'full' if mode == 'full' or (mode == 'auto' and had_full) else 'lite'

        with tempfile.TemporaryDirectory(prefix='.ccb-install-', dir=dest.parent) as temporary:
            stage = Path(temporary)
            candidate = stage / NAME
            built = build(candidate)
            subprocess.run([sys.executable, str(candidate / 'scripts/setup.py'), '--mode', selected], check=True)
            subprocess.run([sys.executable, str(helper / 'update_plugin_cachebuster.py'), str(candidate)], check=True)
            (candidate / 'INSTALLATION.json').write_text(json.dumps({'mode': selected}) + '\n')
            # Cachebuster and mode metadata change only this installed copy, not the source.
            manifest = candidate / 'CONTENTS.sha256.json'
            hashes = json.loads(manifest.read_text())
            for name in [*hashes, 'INSTALLATION.json']:
                hashes[name] = hashlib.sha256((candidate / name).read_bytes()).hexdigest()
            manifest.write_text(json.dumps(hashes, indent=2) + '\n')

            staged_market = stage / 'marketplace.json'
            if previous_market is not None:
                staged_market.write_bytes(previous_market)
            if not existing:
                # Scaffold and marketplace changes stay in staging until all builds succeed.
                subprocess.run([
                    sys.executable, str(helper / 'create_basic_plugin.py'), NAME,
                    '--path', str(stage / 'scaffold'), '--with-marketplace',
                    '--marketplace-path', str(staged_market),
                ], check=True)
            market_name = subprocess.check_output([
                sys.executable, str(helper / 'read_marketplace_name.py'),
                '--marketplace-path', str(staged_market),
            ], text=True).strip()
            new_market = staged_market.read_bytes()
            if (market.read_bytes() if market.exists() else None) != previous_market:
                raise RuntimeError('Marketplace changed during preparation; retry without overwriting it.')

            backups = dest.parent / '.ccb-install-backups'
            backups.mkdir(exist_ok=True)
            backup = backups / (uuid.uuid4().hex + '-previous') if dest.exists() else None
            switched = False
            market_written = False
            registering = False
            try:
                if backup is not None:
                    dest.rename(backup)
                candidate.rename(dest)
                switched = True
                if not existing:
                    replace_bytes(market, new_market)
                    market_written = True
                registering = True
                subprocess.run([codex, 'plugin', 'add', NAME + '@' + market_name], check=True)
            except (Exception, KeyboardInterrupt) as error:
                recovery = []
                try:
                    if switched:
                        failed = backups / (uuid.uuid4().hex + '-failed')
                        dest.rename(failed)
                        recovery.append('failed candidate retained at ' + str(failed))
                    if backup is not None and backup.exists():
                        backup.rename(dest)
                        recovery.append('previous package files restored')
                    if market_written:
                        if not market.exists() or market.read_bytes() != new_market:
                            raise RuntimeError('Marketplace changed after switch; reconcile it manually.')
                        if previous_market is None:
                            market.unlink()
                        else:
                            replace_bytes(market, previous_market)
                    if registering and backup is not None:
                        subprocess.run([codex, 'plugin', 'add', NAME + '@' + market_name], check=True)
                        recovery.append('previous package re-registered; verify in a new task')
                    elif registering:
                        recovery.append('no previous package; check any partial host registration before retrying')
                except (Exception, KeyboardInterrupt) as rollback_error:
                    recovery.append('recovery incomplete: ' + str(rollback_error)
                                    + '; previous backup: ' + str(backup))
                raise RuntimeError('Installation failed: ' + str(error) + '. ' + '; '.join(recovery)) from error

            print(json.dumps({**built, 'package': str(dest), 'mode': selected,
                              'backup': str(backup) if backup else None}, indent=2))
            print('Installed ' + selected + ' package. Open a new task to verify loading; ChatGPT access is not tested here.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['auto', 'lite', 'full'], default='auto',
                        help='auto preserves Full; explicit lite requests a downgrade')
    install(parser.parse_args().mode)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        raise SystemExit(str(error)) from error
