DIDL-Lite (Digital Item Declaration Language) tools for Python
==============================================================

DIDL-Lite tools for Python to read and write DIDL-Lite-xml.

Usage
-----

See ``tests/`` for examples on how to use this.

Note that this package does **NOT** do any type checking. Coercion of data types from and to strings must be done by the user of this library.


Resources / documents
---------------------

DIDL-Lite resources and documents:

* `UPnP-av-ContentDirectory-v1-Service <http://upnp.org/specs/av/UPnP-av-ContentDirectory-v1-Service.pdf>`_
* `UPnP-av-ContentDirectory-v2-Service <http://upnp.org/specs/av/UPnP-av-ContentDirectory-v2-Service.pdf>`_
* `didl-lite-v2.xsd <http://www.upnp.org/schemas/av/didl-lite-v2.xsd>`_
* `mpeg21-didl <http://xml.coverpages.org/mpeg21-didl.html>`_


Releasing
---------

Steps for releasing:

- Switch to development: ``git checkout master``
- Do a pull: ``git pull``
- Run towncrier: ``towncrier build --version <version>``
- Commit towncrier results: ``git commit -m "Towncrier"``
- Run bump2version (note that this creates a new commit + tag): ``bump2version --tag major/minor/patch``
- Push to github: ``git push && git push --tags``
