"""Check relative file targets in Markdown links, using only the standard library."""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

LINK_PATTERN = re.compile(r'!?\[[^\]\n]*\]\(([^\)\n]+)\)')
SKIP_SCHEMES = {'http', 'https', 'mailto', 'tel', 'data'}


def check_links(root):
    problems = []
    files = sorted(root.rglob('*.md'))
    for document in files:
        if any(part.startswith('.') and part not in ('.github',) for part in document.relative_to(root).parts):
            continue
        for number, line in enumerate(document.read_text(encoding='utf-8').splitlines(), 1):
            for match in LINK_PATTERN.finditer(line):
                link = match.group(1).strip().strip('<>')
                # Local paths in this repository do not contain whitespace; ignore optional titles.
                link = link.split(' "', 1)[0]
                parts = urlsplit(link)
                if not parts.path or parts.scheme in SKIP_SCHEMES or link.startswith('//'):
                    continue
                if parts.scheme or parts.path.startswith('/'):
                    problems.append(f'{document.relative_to(root)}:{number}: invalid local link {link}')
                    continue
                target = (document.parent / unquote(parts.path)).resolve()
                if not target.is_relative_to(root) or not target.exists():
                    problems.append(f'{document.relative_to(root)}:{number}: missing target {link}')
    return files, problems


def main():
    parser = argparse.ArgumentParser(description='Verify local Markdown links.')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    root = args.root.resolve()
    if not (root / 'README.md').is_file():
        parser.error(f'Not a repository root: {root}')
    docs, errors = check_links(root)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        print(f'FAIL: {len(errors)} invalid links in {len(docs)} Markdown files.', file=sys.stderr)
        return 1
    print(f'OK: checked local links in {len(docs)} Markdown files.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
