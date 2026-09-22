#!/usr/bin/env python3
"""Read-only HTML/Markdown craft checks. No rendering, network or dependencies."""
from __future__ import annotations

import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'param', 'source', 'track', 'wbr'}
PROTECTED = {'script', 'style', 'template', 'noscript', 'pre', 'code',
             'blockquote', 'q', 'math', 'svg'}
CHECKS = ['duplicate-id', 'missing-local-fragment', 'missing-lang',
          'missing-alt', 'heading-level-skip', 'heading-hard-break',
          'unnamed-control', 'repeated-em-dash', 'separator-strip',
          'markdown-hard-breaks']


class Node:
    def __init__(self, tag, attrs, line, parent=None):
        self.tag, self.attrs, self.line, self.parent = tag, dict(attrs), line, parent
        self.children = []

    def text(self):
        return ''.join(c.text() if isinstance(c, Node) else c for c in self.children)

    def excluded(self):
        node = self
        while node:
            if (node.tag in PROTECTED or 'hidden' in node.attrs
                    or node.attrs.get('aria-hidden', '').lower() == 'true'):
                return True
            node = node.parent
        return False

    def ancestors(self):
        node = self.parent
        while node:
            yield node
            node = node.parent

    def descendants(self):
        pending = [c for c in self.children if isinstance(c, Node)]
        while pending:
            child = pending.pop()
            yield child
            pending.extend(c for c in child.children if isinstance(c, Node))


class Tree(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.root = Node('root', {}, 1)
        self.stack = [self.root]
        self.nodes = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.getpos()[0], self.stack[-1])
        self.stack[-1].children.append(node)
        self.nodes.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def finding(rule, severity, line, message):
    return dict(rule=rule, severity=severity, line=line, message=message)


def copy_findings(text, line):
    results = []
    if text.count('—') >= 2:
        results.append(finding('repeated-em-dash', 'review', line,
                               'Repeated em dashes in one text block; review intent, do not rewrite quotations.'))
    if text.count('·') >= 3 or text.count('•') >= 3:
        results.append(finding('separator-strip', 'review', line,
                               'Repeated separators in one text block; check whether a list or plain sentence reads better.'))
    return results


def html_findings(source):
    tree = Tree(source)
    nodes = tree.nodes
    results = []
    ids = {}
    for n in nodes:
        if any(a.tag == 'template' for a in n.ancestors()):
            continue
        identifier = n.attrs.get('id')
        if identifier:
            if identifier in ids:
                results.append(finding('duplicate-id', 'error', n.line,
                                       'Duplicate HTML id; anchors and labels may resolve to the wrong element.'))
            ids[identifier] = n
    has_base = any(n.tag == 'base' and n.attrs.get('href') for n in nodes)
    for n in nodes:
        if n.tag == 'html' and not n.attrs.get('lang', '').strip():
            results.append(finding('missing-lang', 'error', n.line,
                                   'Full HTML document has no language declaration.'))
        if n.tag == 'a' and not has_base and not any(a.tag == 'template' for a in n.ancestors()):
            href = n.attrs.get('href', '')
            if href.startswith('#'):
                fragment = unquote(urlsplit(href).fragment)
                # Empty #, the reserved top fragment and text directives are valid.
                if fragment and fragment.lower() != 'top' and ':~:text=' not in fragment and fragment not in ids:
                    results.append(finding('missing-local-fragment', 'review', n.line,
                                           'No matching id in source; check runtime-generated targets or hash routing.'))
        if n.excluded():
            continue
        if n.tag == 'img' and 'alt' not in n.attrs and n.attrs.get('role') not in {'presentation', 'none'}:
            results.append(finding('missing-alt', 'review', n.line,
                                   'Image has no alt attribute; describe it or mark it decorative.'))
        if n.tag == 'br' and any(re.fullmatch('h[1-6]', a.tag) for a in n.ancestors()):
            results.append(finding('heading-hard-break', 'review', n.line,
                                   'Heading contains a hard break; verify the intended wrap at narrow widths.'))
        if n.tag in {'button', 'input', 'select', 'textarea'}:
            kind = n.attrs.get('type', '').lower()
            if kind == 'hidden':
                continue
            name = n.attrs.get('aria-label', '').strip()
            labelled = n.attrs.get('aria-labelledby', '').split()
            name = name or ' '.join(ids[x].text().strip() for x in labelled if x in ids)
            if n.tag == 'button':
                name = name or n.text().strip()
                # Icon accessible names need a browser check, not a source-level verdict.
                name = name or any(c.tag in {'svg', 'img'} and (c.attrs.get('alt') or c.attrs.get('aria-label') or c.text().strip())
                                   for c in n.descendants())
            if n.tag == 'input' and kind in {'submit', 'reset'}:
                name = True  # Native default label exists even without value.
            if n.tag == 'input' and kind == 'button':
                name = name or n.attrs.get('value')
            if n.tag == 'input' and kind == 'image':
                name = name or n.attrs.get('alt')
            if n.tag != 'button':
                name = name or any(a.tag == 'label' and a.text().strip() for a in n.ancestors())
                name = name or any(a.tag == 'label' and a.attrs.get('for') == n.attrs.get('id')
                                   and a.attrs.get('for') and a.text().strip() for a in nodes)
            if not name:
                results.append(finding('unnamed-control', 'review', n.line,
                                       'No source-level control label found; check the rendered accessible name.'))
        # Leaf blocks avoid counting nested list/paragraph text several times.
        if n.tag in {'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'figcaption'}:
            protected_child = any(c.excluded() for c in n.descendants())
            nested_block = any(c.tag in {'p', 'li'} for c in n.descendants())
            if not protected_child and not nested_block:
                results.extend(copy_findings(n.text(), n.line))
    previous = 0
    for n in nodes:
        if re.fullmatch('h[1-6]', n.tag) and not n.excluded():
            level = int(n.tag[1])
            if previous and level > previous + 1:
                results.append(finding('heading-level-skip', 'review', n.line,
                                       f'Heading level jumps from h{previous} to h{level}.'))
            previous = level
    return results


def markdown_findings(source):
    results, paragraph = [], []
    fence, frontmatter, raw_protected, previous = None, False, None, 0

    def flush():
        if paragraph:
            results.extend(copy_findings(' '.join(x[1] for x in paragraph), paragraph[0][0]))
            count = sum(bool(re.search(r'( {2,}|\\)$', text)) for _, text in paragraph)
            if count >= 3:
                results.append(finding('markdown-hard-breaks', 'review', paragraph[0][0],
                                       'Three or more forced line breaks in one paragraph; review reading flow.'))
            paragraph.clear()

    for number, line in enumerate(source.splitlines(), 1):
        if number == 1 and line.strip() == '---':
            frontmatter = True
            continue
        if frontmatter:
            if line.strip() in {'---', '...'}:
                frontmatter = False
            continue
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= fence[1] and not marker[2].strip():
                fence = None
            continue
        if marker:
            flush()
            fence = (marker[1][0], len(marker[1]))
            continue
        # Raw HTML quotations/code and indented Markdown code are protected too.
        if raw_protected:
            if re.search(rf'</{raw_protected}\s*>', line, re.I):
                raw_protected = None
            continue
        raw = re.search(r'<(blockquote|pre|script|style)\b', line, re.I)
        if raw:
            flush()
            if not re.search(rf'</{raw[1]}\s*>', line, re.I):
                raw_protected = raw[1]
            continue
        if not line.strip() or re.match(r'^\s*>|^( {4}|\t)', line):
            flush()
            continue
        cleaned = re.sub(r'(`+).*?\1', '', line)
        heading = re.match(r'^ {0,3}(#{1,6})\s+(.+)', cleaned)
        if heading:
            flush()
            level = len(heading[1])
            if previous and level > previous + 1:
                results.append(finding('heading-level-skip', 'review', number,
                                       f'Heading level jumps from {previous} to {level}.'))
            previous = level
            results.extend(copy_findings(heading[2], number))
            if re.search(r'<br\s*/?>', heading[2], re.I):
                results.append(finding('heading-hard-break', 'review', number,
                                       'Heading contains an HTML hard break.'))
        elif '|' not in cleaned and not re.match(r'^\s*(?:[-+*]|\d+[.)])\s', cleaned):
            paragraph.append((number, cleaned))
        else:
            flush()
    flush()
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='+', type=Path, help='Explicit HTML or Markdown files; no recursive scan')
    args = parser.parse_args()
    reports = []
    input_errors = []
    for path in args.files:
        suffix = path.suffix.lower()
        if suffix not in {'.html', '.htm', '.md', '.markdown'}:
            input_errors.append({'file': str(path), 'error': 'Unsupported format; use rendered inspection for JSX, PDF, DOCX or PPTX.'})
            continue
        try:
            source = path.read_text(encoding='utf-8-sig')
            findings = html_findings(source) if suffix in {'.html', '.htm'} else markdown_findings(source)
        except (OSError, UnicodeError, ValueError) as exc:
            input_errors.append({'file': str(path), 'error': str(exc)})
            continue
        counts = dict(Counter(f['severity'] for f in findings))
        reports.append({'file': str(path), 'counts': counts, 'findings': findings[:100],
                        'omitted': max(0, len(findings)-100)})
    has_errors = any(r['counts'].get('error') for r in reports)
    print(json.dumps({'schema_version': 1, 'mode': 'source', 'rendered': False,
                      'status': 'input-error' if input_errors else 'issues' if has_errors else 'review' if any(r['findings'] for r in reports) else 'no-findings',
                      'checks': CHECKS, 'files': reports, 'input_errors': input_errors,
                      'limitations': ['Source heuristics only; not browser visibility or full Markdown parsing.',
                                      'No layout, contrast, interaction or overall accessibility certification.',
                                      'Review findings are contextual, not defects or quality scores.']},
                     ensure_ascii=False, indent=2))
    return 2 if input_errors else 1 if has_errors else 0


if __name__ == '__main__':
    sys.exit(main())
