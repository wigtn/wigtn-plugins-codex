#!/usr/bin/env python3
"""Detector regression tests. DOM fixtures are not real-browser visual QA."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT/'plugins/wigtn-plugins-with-codex/skills/visual-craft'
if not SKILL.exists():
    SKILL = Path(__file__).parent  # Staging execution before installation.
SOURCE = SKILL/'scripts/audit-source.py'
spec = importlib.util.spec_from_file_location('craft_audit', SOURCE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def rules(findings):
    return {f['rule'] for f in findings}


class SourceTests(unittest.TestCase):
    def test_html_defects_and_source_locations(self):
        findings = audit.html_findings('<html>\n<h1 id="a">Title</h1>\n<p id="a">Body</p>\n<a href="#missing">Go</a>')
        self.assertEqual(rules(findings), {'missing-lang', 'duplicate-id', 'missing-local-fragment'})
        self.assertEqual(next(f['line'] for f in findings if f['rule'] == 'duplicate-id'), 3)
        self.assertEqual(next(f['severity'] for f in findings if f['rule'] == 'missing-local-fragment'), 'review')

    def test_fragment_decoding_and_reserved_targets(self):
        findings = audit.html_findings('<h1 id="한글">제목</h1><a href="#%ED%95%9C%EA%B8%80">이동</a><a href="#">상단</a><a href="#top">top</a><a href="#:~:text=abc">text</a><a href="other.html#x">다른 문서</a>')
        self.assertNotIn('missing-local-fragment', rules(findings))

    def test_base_url_does_not_make_external_fragment_a_local_error(self):
        self.assertEqual(audit.html_findings('<base href="https://example.org/"><a href="#outside">Go</a>'), [])

    def test_preserved_copy_is_not_flagged(self):
        source = '<html lang="ko"><h1>WIGTN.</h1><blockquote>원문 — 인용 — 그대로 · 유지 · 필요 · 함</blockquote><p><q>원문 — 인용 — 유지</q></p><pre>코드 — 코드 — 코드</pre><svg><text>브랜드 — 원본 — 보존</text></svg><p hidden>숨김 — 내용 — 보존</p><p aria-hidden="true">장식 — 장식 — 장식</p></html>'
        self.assertEqual(audit.html_findings(source), [])

    def test_review_patterns_are_not_hard_errors(self):
        findings = audit.html_findings('<h1>좋은<br>제목</h1><h3>건너뛴 제목</h3><p>문장 — 문장 — 문장</p><p>가 · 나 · 다 · 라</p>')
        self.assertEqual(rules(findings), {'heading-hard-break', 'heading-level-skip', 'repeated-em-dash', 'separator-strip'})
        self.assertTrue(all(f['severity'] == 'review' for f in findings))

    def test_native_and_associated_control_names(self):
        source = '<label for="a">이름</label><input id="a"><label>옵션<select><option>1</option></select></label><span id="name">설명</span><textarea aria-labelledby="name"></textarea><button aria-label="닫기"></button><button><svg><title>메뉴</title></svg></button><input type="submit"><input type="hidden"><img alt="">'
        self.assertEqual(audit.html_findings(source), [])

    def test_unlabelled_controls_and_images(self):
        findings = audit.html_findings('<input placeholder="이름"><button></button><img src="x.png">')
        self.assertEqual(rules(findings), {'unnamed-control', 'missing-alt'})
        self.assertEqual(len(findings), 3)

    def test_submit_button_has_no_native_default_name(self):
        findings = audit.html_findings('<button type="submit"></button><input type="submit">')
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['rule'], 'unnamed-control')

    def test_inert_template_does_not_collide_with_live_ids(self):
        self.assertEqual(audit.html_findings('<div id="a"></div><template><div id="a"></div><a href="#x">template</a></template>'), [])

    def test_markdown_protected_content(self):
        source = '---\ntitle: a — b — c\n---\n# 제목\n> 인용 — 그대로 — 유지\n\n```text\na — b — c\n```\n\n    code — code — code\n\n`a — b — c`\n\n<blockquote>\na — b — c\n</blockquote>\n'
        self.assertEqual(audit.markdown_findings(source), [])

    def test_fence_only_closes_with_matching_marker(self):
        source = '````\n```\na — b — c\n````\n\n일반 — 문장 — 검토\n'
        findings = audit.markdown_findings(source)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['line'], 6)

    def test_markdown_heading_break_and_paragraph_breaks(self):
        source = '# 시작\n\n### 제목<br>줄\n\n하나  \n둘  \n셋  \n넷\n'
        self.assertEqual(rules(audit.markdown_findings(source)), {'heading-level-skip', 'heading-hard-break', 'markdown-hard-breaks'})

    def test_dense_tables_and_ordered_lists_are_not_decoration(self):
        self.assertEqual(audit.markdown_findings('# 결과\n\n| 열 | 값 |\n|---|---|\n| x | 20 |\n\n1. 설치\n2. 실행\n'), [])

    def test_cli_does_not_mutate_or_execute_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'test.html'
            marker = Path(tmp)/'marker'
            path.write_text(f'<html lang="ko"><script>require("fs").writeFileSync({json.dumps(str(marker))},"bad")</script><h1>제목</h1><p>문장 — 문장 — 문장</p></html>')
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            result = subprocess.run([sys.executable, str(SOURCE), str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)['status'], 'review')
            self.assertFalse(marker.exists())
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)

    def test_cli_error_codes_and_unsupported_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'test.html'
            path.write_text('<html><h1 id="a">a</h1><p id="a">b</p>')
            result = subprocess.run([sys.executable, str(SOURCE), str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            result = subprocess.run([sys.executable, str(SOURCE), str(Path(tmp)/'missing.md'), 'component.tsx'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(len(json.loads(result.stdout)['input_errors']), 2)

    def test_report_is_bounded_without_hiding_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'test.html'
            path.write_text('<button></button>'*120)
            result = subprocess.run([sys.executable, str(SOURCE), str(path)], capture_output=True, text=True)
            report = json.loads(result.stdout)['files'][0]
            self.assertEqual(len(report['findings']), 100)
            self.assertEqual(report['counts']['review'], 120)
            self.assertEqual(report['omitted'], 20)


class GeometryFixtureTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node unavailable; DOM geometry fixture not run')
    def test_readonly_detector_geometry(self):
        runner = r'''
const fs = require('node:fs'); const vm = require('node:vm'); const assert = require('node:assert/strict');
const source = fs.readFileSync(process.argv[1], 'utf8');
function node(p = {}) {
  const style = Object.assign({visibility:'visible',display:'block',overflowX:'visible',overflowY:'visible',fontSize:'16px',pointerEvents:'auto'}, p.style);
  const rect = Object.assign({width:100,height:44,top:0,left:0,bottom:44,right:100}, p.rect);
  return {tagName:'P',id:'',disabled:false,style,childNodes:[{nodeType:3,textContent:'Text'}],
    clientWidth:100,scrollWidth:100,clientHeight:44,scrollHeight:44,
    closest:()=>null,getClientRects:()=>[rect],getBoundingClientRect:()=>rect,
    matches:(selector)=>selector.startsWith('button') && !!p.interactive,
    ...p, style, getBoundingClientRect:()=>rect};
}
function run(nodes, scrollWidth=390) {
  const context = {document:{documentElement:{clientWidth:390,scrollWidth},querySelectorAll:()=>nodes},
    getComputedStyle:n=>n.style,innerWidth:390,innerHeight:844};
  return vm.runInNewContext('('+source+')()', context);
}
assert.equal(run([]).status,'no-findings');
assert.equal(run([],500).findings[0].rule,'page-horizontal-overflow');
assert.equal(run([node({style:{overflowX:'auto'},scrollWidth:730})]).findings.length,0);
assert.equal(run([node({style:{overflowX:'hidden'},scrollWidth:300})]).findings[0].rule,'clipped-text');
assert.equal(run([node({style:{fontSize:'11px'}})]).findings[0].severity,'review');
assert.equal(run([node({interactive:true,rect:{height:20}})]).findings[0].rule,'small-target');
assert.equal(run([node({closest:()=>({})})]).inspected,0);
assert.equal(run([node({rect:{top:900,bottom:944},style:{fontSize:'8px'}})]).inspected,0);
assert.equal(run([node({style:{display:'none'}})]).inspected,0);
const bounded=run(Array.from({length:120},()=>node({style:{fontSize:'8px'}})));
assert.equal(bounded.findings.length,100);assert.equal(bounded.omitted,20);
console.log('10 synthetic DOM geometry assertions passed; no real browser was run.');
'''
        result = subprocess.run(['node', '-e', runner, str(SKILL/'scripts/audit-rendered.js')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        print(result.stdout.strip())


if __name__ == '__main__':
    unittest.main(verbosity=2)
