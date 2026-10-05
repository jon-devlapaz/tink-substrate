# Local CI steps (no --tool-cache), 2026-10-05T04:07:52Z
```
$ python3 -B -m unittest discover -s tests
...........fatal: cannot change to '/var/folders/sk/r2ns7lvn2ygcsj7bhd0mvnyw0000gn/T/tmphrxcqi2_/missing': No such file or directory
......................................
----------------------------------------------------------------------
Ran 49 tests in 11.198s

OK
exit: 0
$ python3 scripts/install_skill.py --destination <tmp>/substrate-skill
Installed: <tmp>/substrate-skill
Open a new agent session and use $tink-substrate.
exit: 0
$ python3 -m tink_substrate --help
options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --config CONFIG
$ python3 .substrate-tools/tink-sdlc/scripts/init.py <tmp>/trial-target --check
Create: .tink/skillsets/build-skillset.json, .tink/skillsets/deployment-skillset.json, .tink/skillsets/design-skillset.json, .tink/skillsets/maintenance-skillset.json, .tink/skillsets/planning-skillset.json, .tink/skillsets/testing-skillset.json, _shared/REVIEW.md, _shared/brief-template.md, _shared/intent-template.md, _shared/plan-template.md, _shared/spec-template.md, _system/SDLC.md, _system/scripts/sdlc.py, _system/verification.json, stages/01-plan/CONTEXT.md, stages/02-design/CONTEXT.md, stages/03-build/CONTEXT.md, stages/04-test/CONTEXT.md, stages/05-deploy/CONTEXT.md, stages/06-maintain/CONTEXT.md
Append SDLC router to AGENTS.md; preserve existing instructions.
Preview only; verification will remain UNCONFIGURED.
exit: 0
$ python3 scripts/check_install.py (installed)
Installation matches source 0642556cbee1864aaf50354b4f3be6da5c8e4e5d
exit: 0
    "tink-sdlc": {
      "url": "https://github.com/jon-devlapaz/tink-sdlc.git",
      "revision": "9172e2dce2fd2c32e69bf9b60e2c03c3bf779ebb"
    }
```
Not run locally: `pip install .` and `tink-substrate --help`. Installed check_install.py reports source 0642556 (HEAD before this commit).
