Changes
=======

1.4.1

- Cater for malformed XML from WiiM pro in non-strict mode (#14, @pp81381)


1.4.0 (2023-12-16)

- Treat upnp:class as case-insensitive when in non-strict mode (@chishm)
- Raise a `DidlLiteException` when upnp:class is invalid when in strict mode (@chishm)
- Drop Python3.6 and Python3.7 support, add Python3.10, Python3.11, Python3.12 support
- Bump development dependencies


1.3.2 (2021-11-29)

- Annotate DidlObject properties that mypy doesn't see in __init__ (@chishm)


1.3.1 (2021-10-25)

- Class properties from ContentDirectory:4 (@chishm)


1.3.0 (2021-10-07)

- `DidlObject.resources` is now deprecated, use `DidlObject.res` instead
- Rename `utils.ns_tag` to `utils.expand_namespace_tag`
- Rename `utils.namespace_tag` to `utils.split_namespace_tag`
- Add `__repr__` methods to DIDL classes for easier debugging
- Allow camelCase to get and set DIDL object properties (@chishm)


1.2.6 (2021-03-04)

- Add non-strict option misbehaving devices


1.2.5 (2020-09-12)

- Save xml element for addition information


1.2.4 (2019-03-20)

- Better namespace naming


1.2.3 (2019-01-27)

- Fix infinite recursion error in DidlObject.__getattr__/Resource.__getattr__


1.2.2 (2019-01-26)

- Add `py.typed` to support PEP 561
- MyPy understands DidlObject/Descriptor have dynamic properties
- Move utility methods to utils


1.2.1 (2019-01-20)

- Typing fixes (@scop)
- Skip unknown object types on parse (@scop)
- Use defusedxml to parse XML (@scop)


1.2.0 (2018-11-03)

- Typing fixes (@scop)
- Allow unknown properties to be parsed and stored, such as albumArtURI on Items, as used by Kodi


1.1.0 (2018-08-17)

- Always set properties, even if no value was given


1.0.1 (2018-06-29)

- Use default ("") for id and parent_id


1.0.0 (2018-06-29)

- Initial release
