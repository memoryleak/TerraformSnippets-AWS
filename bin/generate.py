#!/usr/bin/env python3
"""Generate Sublime Text snippets from the AWS provider schema.

The structure (names, types, required/optional, nested blocks) comes from
`terraform providers schema -json`. Human readable descriptions come from the
provider's Markdown docs (website/docs/{r,d}) because the AWS provider leaves
most schema descriptions empty.
"""
import argparse
import json
import re
import shutil
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

PROVIDER = "registry.terraform.io/hashicorp/aws"
INDENT = "  "
DESCRIPTION_LENGTH = 100

# (schema key, output directory, HCL keyword, docs directory, trigger prefix, docs heading)
KINDS = [
    ("resource_schemas", "resources", "resource", "r", "", "Resource"),
    ("data_source_schemas", "data-sources", "data", "d", "data_", "Data Source"),
]

# "tags_all" is reported as optional but is computed from "tags" and the provider default tags.
SKIPPED_ATTRIBUTES = {"id", "tags_all"}

ARGUMENT_LINE = re.compile(r"^[*-] `([a-z0-9_]+)`\s*-\s*(.*)$")
LEADING_FLAGS = re.compile(r"^\((?:Required|Optional)[^)]*\)\s*")
MARKDOWN_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")


class Placeholders:
    """Hands out sequential tab stops, starting after the block label (${1})."""

    def __init__(self):
        self.index = 1

    def next(self, default=None):
        self.index += 1
        return "${%d}" % self.index if default is None else "${%d:%s}" % (self.index, default)


# --- Documentation -----------------------------------------------------------

def clean_text(text):
    text = MARKDOWN_LINK.sub(r"\1", text).replace("`", "").strip()
    sentence = re.split(r"(?<=\.)\s", text, maxsplit=1)[0]
    if len(sentence) > DESCRIPTION_LENGTH:
        sentence = sentence[:DESCRIPTION_LENGTH - 3].rstrip() + "..."
    return sentence


def parse_doc(path):
    """Return (description, {argument: description}) for one docs page."""
    text = path.read_text(encoding="utf-8")
    description = ""
    match = re.search(r"^description:\s*(?:\|-?\s*\n((?:[ \t]+.*\n?)+)|(.+))", text, re.M)
    if match:
        description = " ".join((match.group(1) or match.group(2)).split()).strip("\"'")

    arguments = {}
    section = re.search(r"^## Arguments? Reference\s*$(.*?)(?=^## Attributes? Reference|\Z)", text, re.M | re.S)
    for line in (section.group(1) if section else "").splitlines():
        match = ARGUMENT_LINE.match(line.strip())
        if match and match.group(1) not in arguments:
            arguments[match.group(1)] = clean_text(LEADING_FLAGS.sub("", match.group(2)))
    return clean_text(description), arguments


def load_docs(docs_dir, subdir, heading):
    """Map type name (e.g. aws_instance) to its parsed docs page."""
    docs = {}
    if docs_dir is None:
        return docs
    title = re.compile(r"^# %s: (aws_[a-z0-9_]+)\s*$" % heading, re.M)
    for path in sorted((docs_dir / subdir).glob("*.markdown")):
        match = title.search(path.read_text(encoding="utf-8"))
        name = match.group(1) if match else "aws_" + path.name.split(".")[0]
        docs.setdefault(name, parse_doc(path))
    return docs


# --- Rendering ---------------------------------------------------------------

def snippet_escape(text):
    return text.replace("\\", "\\\\").replace("$", "\\$").replace("]]>", "]] >")


def example_value(attribute_type):
    """A literal of the right type, used for commented optional arguments."""
    kind = attribute_type if isinstance(attribute_type, str) else attribute_type[0]
    return {"string": '""', "number": "0", "bool": "false", "map": "{}", "object": "{}",
            "list": "[]", "set": "[]", "tuple": "[]"}.get(kind, "null")


def placeholder_value(name, attribute_type, placeholders):
    kind = attribute_type if isinstance(attribute_type, str) else attribute_type[0]
    if kind == "string":
        return '"%s"' % placeholders.next(name)
    if kind == "number":
        return placeholders.next("0")
    if kind == "bool":
        return placeholders.next("false")
    if kind in ("list", "set", "tuple"):
        return "[%s]" % placeholders.next()
    if kind in ("map", "object"):
        return "{%s}" % placeholders.next()
    return placeholders.next("null")


def align(lines, prefix=""):
    """Align `=` and trailing comments of (name, value, comment) lines like `terraform fmt` does."""
    width = max((len(name) for name, _, _ in lines), default=0)
    code = ["%s%s = %s" % (prefix, name.ljust(width), value) for name, value, _ in lines]
    comment_column = max((len(line) for line in code), default=0)
    return [line.ljust(comment_column) + "  # " + snippet_escape(comment) if comment else line
            for line, (_, _, comment) in zip(code, lines)]


def is_input(attribute):
    return attribute.get("required") or attribute.get("optional")


def render_block(block, depth, placeholders, arguments):
    """Render required arguments as tab stops and optional ones as comments."""
    pad = INDENT * depth
    attributes = {name: attribute for name, attribute in block.get("attributes", {}).items()
                  if name not in SKIPPED_ATTRIBUTES and is_input(attribute)}
    block_types = block.get("block_types", {})

    lines = []
    required = [(name, placeholder_value(name, attribute["type"], placeholders),
                 arguments.get(name) if depth == 1 else None)
                for name, attribute in attributes.items() if attribute.get("required")]
    lines.extend(align(required, pad))

    for name, block_type in block_types.items():
        if block_type.get("min_items", 0) > 0:
            lines.append(pad + name + " {")
            lines.extend(render_block(block_type["block"], depth + 1, placeholders, arguments))
            lines.append(pad + "}")

    optional = [name for name, attribute in attributes.items()
                if not attribute.get("required") and not attribute.get("deprecated")]
    optional_blocks = [name for name, block_type in block_types.items()
                       if block_type.get("min_items", 0) == 0 and not block_type["block"].get("deprecated")]
    if depth == 1 and (optional or optional_blocks):
        if lines:
            lines.append("")
        lines.extend(align([(name, example_value(attributes[name]["type"]), arguments.get(name))
                            for name in optional], pad + "# "))
        for name in optional_blocks:
            comment = arguments.get(name)
            lines.append(pad + "# %s {}" % name + ("  # " + snippet_escape(comment) if comment else ""))
    return lines


def render_snippet(keyword, type_name, trigger, schema, doc):
    description, arguments = doc
    body = render_block(schema["block"], 1, Placeholders(), arguments)
    content = '%s "%s" "${1:name}" {\n%s\n}' % (keyword, type_name, "\n".join(body)) if body \
        else '%s "%s" "${1:name}" {\n}' % (keyword, type_name)
    label = ("Data source: " if keyword == "data" else "") + (description or type_name)
    return (
        "<snippet>\n"
        "<content><![CDATA[\n%s\n]]></content>\n"
        "<tabTrigger>%s</tabTrigger>\n"
        "<scope>source.terraform</scope>\n"
        "<description>%s</description>\n"
        "</snippet>\n"
    ) % (content, trigger, xml_escape(label))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--schema", required=True, type=Path, help="output of `terraform providers schema -json`")
    parser.add_argument("--docs", type=Path, help="provider docs directory (website/docs)")
    parser.add_argument("--out", required=True, type=Path, help="snippet output directory")
    args = parser.parse_args()

    provider = json.loads(args.schema.read_text())["provider_schemas"][PROVIDER]

    # Regenerate from scratch so snippets for removed resources disappear.
    for path in args.out.rglob("*.sublime-snippet"):
        path.unlink()
    for _, directory, *_ in KINDS:
        shutil.rmtree(args.out / directory, ignore_errors=True)

    for schema_key, directory, keyword, docs_subdir, prefix, heading in KINDS:
        docs = load_docs(args.docs, docs_subdir, heading)
        target = args.out / directory
        target.mkdir(parents=True)
        schemas = provider.get(schema_key, {})
        for type_name in sorted(schemas):
            snippet = render_snippet(keyword, type_name, prefix + type_name, schemas[type_name],
                                     docs.get(type_name, ("", {})))
            (target / (type_name + ".sublime-snippet")).write_text(snippet, encoding="utf-8")
        documented = sum(1 for name in schemas if name in docs)
        print("%s: %d snippets (%d with docs)" % (directory, len(schemas), documented))


if __name__ == "__main__":
    main()
