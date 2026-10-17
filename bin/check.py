#!/usr/bin/env python3
"""Validate generated snippets.

Checks that every snippet is well-formed XML with a valid, unique tab trigger,
then expands all snippets with their default values and lets `terraform fmt`
parse the result to catch HCL syntax errors.
"""
import re
import subprocess
import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path

TRIGGER = re.compile(r"^(data_)?aws_[a-z0-9_]+$")
TYPE_LABEL = re.compile(r'^(resource|data) "(aws_[a-z0-9_]+)" "')
PLACEHOLDER = re.compile(r"\$\{\d+(?::([^}]*))?\}")


def expand(content):
    """Expand a snippet body the way Sublime would when accepting every default."""
    content = PLACEHOLDER.sub(lambda match: match.group(1) or "", content)
    return content.replace("\\$", "$").replace("\\\\", "\\")


def terraform_fmt(source):
    """Return terraform's parse error for the given HCL, or None if it parses."""
    result = subprocess.run(["terraform", "fmt", "-no-color", "-"], input=source, capture_output=True, text=True)
    return result.stderr.strip() if result.returncode else None


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "Snippets")
    errors, triggers, expanded = [], {}, []

    paths = sorted(root.rglob("*.sublime-snippet"))
    for path in paths:
        try:
            snippet = ElementTree.parse(path).getroot()
        except ElementTree.ParseError as error:
            errors.append("%s: invalid XML: %s" % (path, error))
            continue
        trigger = snippet.findtext("tabTrigger", "")
        content = snippet.findtext("content", "").strip()
        match = TYPE_LABEL.match(content)
        if not TRIGGER.match(trigger):
            errors.append("%s: invalid tab trigger %r" % (path, trigger))
        if not match or match.group(2) != path.stem or not trigger.endswith(match.group(2)):
            errors.append("%s: type, trigger and file name do not match" % path)
        if trigger in triggers:
            errors.append("%s: duplicate tab trigger %r (also in %s)" % (path, trigger, triggers[trigger]))
        triggers[trigger] = path
        expanded.append((path, expand(content)))

    # Parse everything in one go; only on failure look for the offending snippets one by one.
    if terraform_fmt("\n\n".join(content for _, content in expanded)):
        for path, content in expanded:
            error = terraform_fmt(content)
            if error:
                errors.append("%s: invalid HCL:\n%s" % (path, error))

    for error in errors:
        print(error, file=sys.stderr)
    print("%d snippets checked, %d errors" % (len(paths), len(errors)))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
