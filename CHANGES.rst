Changes
=======

1.2.5 (unreleased)


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
