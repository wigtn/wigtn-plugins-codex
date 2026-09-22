/* Read-only expression for an authorized browser evaluate call. No navigation,
   mutation, fetch, dependency or automatic execution. */
() => {
  const findings = [];
  let total = 0;
  const add = (rule, severity, target, message, measured) => {
    total += 1;
    if (findings.length < 100) findings.push({ rule, severity, target, message, measured });
  };
  const root = document.documentElement;
  const width = root.clientWidth;
  if (width > 0 && root.scrollWidth > width + 2) {
    add('page-horizontal-overflow', 'error', 'document',
      'The page is wider than its viewport; inspect unintended horizontal scrolling.',
      { viewportWidth: width, scrollWidth: root.scrollWidth });
  }
  const nodes = [...document.querySelectorAll('body *')];
  let inspected = 0;
  for (const [index, element] of nodes.entries()) {
    if (element.closest('script,style,template,svg,[hidden],[aria-hidden="true"]')) continue;
    const rect = element.getBoundingClientRect();
    const css = getComputedStyle(element);
    if (!element.getClientRects().length || rect.width <= 0 || rect.height <= 0 ||
        css.visibility === 'hidden' || css.visibility === 'collapse' || css.display === 'none') continue;
    // Check the current viewport. Scroll then rerun to inspect additional areas.
    if (rect.bottom <= 0 || rect.right <= 0 || rect.top >= innerHeight || rect.left >= innerWidth) continue;
    inspected += 1;
    const target = `${element.tagName.toLowerCase()}${element.id ? '#' + element.id : ''} [body index ${index}]`;
    const directText = [...element.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    const overflowX = ['hidden', 'clip'].includes(css.overflowX);
    const overflowY = ['hidden', 'clip'].includes(css.overflowY);
    if (directText && !element.matches('input,textarea,select') &&
        ((overflowX && element.scrollWidth > element.clientWidth + 2) ||
         (overflowY && element.scrollHeight > element.clientHeight + 2))) {
      add('clipped-text', 'review', target,
        'Text extends beyond a clipped box. Check whether truncation is intentional and the full value is accessible.',
        { width: element.clientWidth, scrollWidth: element.scrollWidth,
          height: element.clientHeight, scrollHeight: element.scrollHeight });
    }
    const size = parseFloat(css.fontSize);
    if (directText && Number.isFinite(size) && size < 12) {
      add('small-text', 'review', target, 'Text is smaller than 12 CSS px; check its role and readability.', { fontSize: size });
    }
    if (element.matches('button,input:not([type="hidden"]),select,textarea,[role="button"],a[href]') &&
        !element.disabled && css.pointerEvents !== 'none' &&
        (rect.width < 24 || rect.height < 24)) {
      add('small-target', 'review', target,
        'Target has a dimension below 24 CSS px; inspect spacing, label association and inline-link exceptions.',
        { width: rect.width, height: rect.height });
    }
  }
  return {
    schema_version: 1, mode: 'rendered-viewport', rendered: true,
    status: findings.some(f => f.severity === 'error') ? 'issues' : total ? 'review' : 'no-findings',
    viewport: { width: innerWidth, height: innerHeight }, inspected,
    checks: ['page-horizontal-overflow', 'clipped-text', 'small-text', 'small-target'],
    findings, omitted: Math.max(0, total - findings.length),
    limitations: ['Current viewport only; closed panels, iframe contents and shadow roots are not inspected.',
      'No contrast, accessible-name, keyboard or state-consistency certification.',
      'Thresholds are review heuristics, not a WCAG audit or aesthetic score.']
  };
}
