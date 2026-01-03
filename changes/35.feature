Handle unbound XML prefixes when strict=False

Allow for unbound XML prefixes when parsing with strict=False.
This is useful for handling XML documents that may have missing
namespace declarations.
