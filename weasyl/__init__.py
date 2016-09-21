import subprocess

__sha__ = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).strip()
