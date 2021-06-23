Changelog
=========

0.1.2
------------------
- update versionning scheme to remove letters
- set django2.2 as required
- use only python3 as programming language
- force fpm to use python3
  [nhislaire]

0.1.1m
------------------
- always use last item of list instead of using index to validate user's choice
  [nhislaire]

0.1.1l
------------------
- manage multi-select choice
  [nhislaire]


0.1.1k
------------------
- Add docstrings
- Add descriptions to endpoints, or translate them to french
  [nhislaire]


0.1.1j
------------------
- Refactor and simplify get method and submethods
- Add docstrings to refactored methods
  [nhislaire]


0.1.1i
------------------
- Hardcode dialect_options value as it should not changes
  [nhislaire]


0.1.1h
------------------
- Do not recalculate meal's date before returning the json as they are correct
  in the imported csv file.
  [nhislaire]


0.1.1g
------------------
- init buster branch that will become master later and adapt Jenkinsfile
  to allow the iMio Nexus Debian Buster package build
  [dmuyshond]


0.1.1f
------------------
- Fix user's choice checking method if prod
  [nhi]

0.1.1e
------------------

- Manage "nothing" items in test method.
  [boulch]

0.1.1d
------------------

- update get endpoint. Use a paremeter to choice if form is in test mode or not.
  [boulch]

0.1.1c
------------------

- Added test endpoint and refactored code.
  [boulch]

0.1.1a
------------------

- Adapt Jenkinsfile to install package python3/dist-package instead of python2
