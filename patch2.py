#!/usr/bin/env python3
"""
Stylus Material patch #2 (runs after patch.py; patch.py calls it automatically).

  - Search / replace bar in the editor top panel (new "Search" toolbar button)
  - Gboard / Android text-selection fixes for CodeMirror 5:
      * line numbers no longer end up in selection, Copy, Cut (numbers are drawn by CSS, not text)
      * Gboard Backspace / "Clear" on a selection no longer desyncs the editor display

Standalone: python patch2.py [repo]   (after patch.py)
"""
import re
import sys
from pathlib import Path

GBOARD_JS = r'''import {CodeMirror} from '@/cm';
import './gboard-fix.css';

const strip = el => {
  const t = el.textContent;
  if (t) {
    el.dataset.ln = t;
    el.textContent = '';
  }
};

const scan = node => {
  if (node.nodeType !== 1) return;
  if (node.classList.contains('CodeMirror-linenumber')) {
    strip(node);
  } else {
    for (const el of node.querySelectorAll('.CodeMirror-linenumber')) strip(el);
  }
};

CodeMirror.defineInitHook(cm => {
  const div = cm.display.lineDiv;
  new MutationObserver(list => {
    for (const m of list) {
      const t = m.target;
      if (t.nodeType === 1 && t.classList.contains('CodeMirror-linenumber')) strip(t);
      for (const n of m.addedNodes) scan(n);
    }
  }).observe(div, {childList: true, subtree: true});
  scan(div);
});

const cmOf = t => (t && t.nodeType === 1 ? t : t && t.parentElement)?.closest?.('.CodeMirror')?.CodeMirror;
const norm = s => s.replace(/[\s\u200b]/g, '');
const DELETE = /^delete(Content|Word|SoftLine|HardLine|Entire)/;
const HEAL = /^(delete|insertFromPaste|insertReplacement)/;
const timers = new WeakMap();

addEventListener('beforeinput', e => {
  if (e.isComposing || !e.cancelable || !DELETE.test(e.inputType)) return;
  const cm = cmOf(e.target);
  if (!cm || cm.isReadOnly()) return;
  const sel = getSelection();
  if (!sel || sel.isCollapsed) return;
  try {
    cm.display.input.pollSelection?.();
  } catch {
    // ignore
  }
  if (cm.somethingSelected() && norm(cm.getSelection()) === norm(sel.toString())) {
    e.preventDefault();
    cm.replaceSelection('', null, '+delete');
  }
}, true);

const onClip = e => {
  const cm = cmOf(e.target);
  if (!cm || !e.clipboardData) return;
  try {
    cm.display.input.pollSelection?.();
  } catch {
    // ignore
  }
  if (!cm.somethingSelected()) return;
  e.clipboardData.setData('text/plain', cm.getSelections().join('\n'));
  e.preventDefault();
  if (e.type === 'cut') cm.replaceSelection('', null, 'cut');
};
addEventListener('copy', onClip, true);
addEventListener('cut', onClip, true);

addEventListener('input', e => {
  if (e.isComposing || !HEAL.test(e.inputType || '')) return;
  const cm = cmOf(e.target);
  if (!cm) return;
  clearTimeout(timers.get(cm));
  timers.set(cm, setTimeout(() => cm.refresh(), 150));
}, true);
'''

GBOARD_CSS = r'''.CodeMirror-linenumber[data-ln]::before { content: attr(data-ln); }
.CodeMirror-gutters,
.CodeMirror-gutter-wrapper,
.CodeMirror-linenumber {
  -webkit-user-select: none !important;
  -moz-user-select: none !important;
  user-select: none !important;
}
'''

SEARCH_JS = r'''import editor from './editor';
import './search-bar.css';

const ICON = {
  up: 'M7.41 15.41L12 10.83l4.59 4.58L18 14l-6-6-6 6z',
  down: 'M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z',
  swap: 'M6.99 11L3 15l3.99 4v-3H14v-2H6.99v-3zM21 9l-3.99-4v3H10v2h7.01v3L21 9z',
  close: 'M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z',
};
const MAX = 9999;

let header;
let bar;
let findEl;
let replEl;
let repRow;
let countEl;
let toggleEl;
let isOpen = false;
let isRep = false;
let cur = null;
let timer;
const overlays = new Map();

const btn = (a, d, title) =>
  `<span class="md-sb-btn" role="button" tabindex="0" data-a="${a}" title="${title}" aria-label="${title}">` +
  `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${d}"/></svg></span>`;
const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const fold = s => s === s.toLowerCase();
const opts = s => ({caseFold: fold(s)});
const getEds = () => editor.getEditors(true).filter(Boolean);
const startOf = cm => ({line: cm.firstLine(), ch: 0});
const endOf = cm => ({line: cm.lastLine(), ch: cm.getLine(cm.lastLine()).length});

function activeCm(eds = getEds()) {
  return eds.reduce((a, b) => ((b.lastActive || 0) > (a.lastActive || 0) ? b : a), eds[0]);
}

function setOverlay(cm, s) {
  const old = overlays.get(cm);
  if (old) {
    cm.removeOverlay(old);
    overlays.delete(cm);
  }
  if (!s) return;
  const rx = new RegExp(esc(s), fold(s) ? 'gi' : 'g');
  const ov = {
    token(stream) {
      rx.lastIndex = stream.pos;
      const m = rx.exec(stream.string);
      if (m && m.index === stream.pos) {
        stream.pos += m[0].length || 1;
        return 'md-find';
      }
      if (m) stream.pos = m.index;
      else stream.skipToEnd();
    },
  };
  cm.addOverlay(ov);
  overlays.set(cm, ov);
}

function clearCur() {
  if (cur) cur.mark.clear();
  cur = null;
}

function select(cm, from, to) {
  clearCur();
  cm.setSelection(from, to);
  cm.scrollIntoView({from, to}, 120);
  cm.lastActive = Date.now();
  cur = {cm, mark: cm.markText(from, to, {className: 'md-find-cur'})};
}

function step(dir, inclusive) {
  const s = findEl.value;
  const eds = getEds();
  if (!s || !eds.length) return false;
  const n = eds.length;
  const start = Math.max(0, eds.indexOf(activeCm(eds)));
  for (let i = 0; i <= n; i++) {
    const cm = eds[((start + dir * i) % n + n) % n];
    if (!overlays.has(cm)) setOverlay(cm, s);
    let from;
    if (i === 0) from = cm.getCursor(dir > 0 && !inclusive ? 'to' : 'from');
    else from = dir > 0 ? startOf(cm) : endOf(cm);
    const c = cm.getSearchCursor(s, from, opts(s));
    if (c.find(dir < 0)) {
      select(cm, c.from(), c.to());
      return true;
    }
  }
  return false;
}

function tally(replaced) {
  if (replaced != null) {
    countEl.textContent = `${replaced} replaced`;
    countEl.classList.remove('none');
    return;
  }
  const s = findEl.value;
  if (!s) {
    countEl.textContent = '';
    return;
  }
  const f = cur && cur.mark.find();
  let total = 0;
  let idx = 0;
  for (const cm of getEds()) {
    const c = cm.getSearchCursor(s, startOf(cm), opts(s));
    while (total < MAX && c.findNext()) {
      total++;
      if (!idx && f && cm === cur.cm && c.from().line === f.from.line && c.from().ch === f.from.ch) idx = total;
    }
  }
  countEl.textContent = total ? `${idx ? idx + '/' : ''}${total}${total >= MAX ? '+' : ''}` : '0';
  countEl.classList.toggle('none', !total);
}

function refresh() {
  clearTimeout(timer);
  const s = findEl.value;
  for (const cm of getEds()) setOverlay(cm, s);
  clearCur();
  if (s) step(1, true);
  tally();
}

function replaceOne() {
  const s = findEl.value;
  if (!s) return;
  const cm = cur ? cur.cm : activeCm();
  if (!cm) return;
  if (cm.somethingSelected()) {
    const sel = cm.getSelection();
    if (fold(s) ? sel.toLowerCase() === s : sel === s) {
      clearCur();
      cm.replaceSelection(replEl.value, 'end');
    }
  }
  step(1);
  tally();
}

function replaceAll() {
  const s = findEl.value;
  if (!s) return;
  const r = replEl.value;
  let n = 0;
  clearCur();
  for (const cm of getEds()) {
    cm.operation(() => {
      const c = cm.getSearchCursor(s, startOf(cm), opts(s));
      while (n < 1e5 && c.findNext()) {
        c.replace(r);
        n++;
      }
    });
  }
  tally(n);
}

function open() {
  if (!isOpen) {
    isOpen = true;
    bar.hidden = false;
    header.classList.add('md-sb-on');
    const cm = activeCm();
    if (cm && cm.somethingSelected()) {
      const t = cm.getSelection();
      if (t && t.length < 200 && !t.includes('\n')) findEl.value = t;
    }
    if (findEl.value) refresh();
  }
  findEl.focus();
  findEl.select();
}

function close() {
  isOpen = false;
  bar.hidden = true;
  clearTimeout(timer);
  header.classList.remove('md-sb-on');
  for (const cm of getEds()) setOverlay(cm, '');
  clearCur();
}

function clearOrClose() {
  if (findEl.value) {
    findEl.value = '';
    refresh();
    findEl.focus();
  } else {
    close();
  }
}

function toggleReplace() {
  isRep = !isRep;
  repRow.hidden = !isRep;
  toggleEl.classList.toggle('on', isRep);
  if (isRep) replEl.focus();
}

const ACTIONS = {
  prev: () => {
    step(-1);
    tally();
  },
  next: () => {
    step(1);
    tally();
  },
  toggle: toggleReplace,
  x: clearOrClose,
  rep: replaceOne,
  all: replaceAll,
};

function build() {
  bar = document.createElement('div');
  bar.id = 'md-sb';
  bar.hidden = true;
  const field = (id, ph, extra) =>
    `<div class="md-sb-field"><input id="${id}" type="text" placeholder="${ph}" autocomplete="off" ` +
    `autocapitalize="off" autocorrect="off" spellcheck="false" enterkeyhint="${id === 'md-sb-find' ? 'search' : 'done'}">${extra}</div>`;
  bar.innerHTML =
    '<div class="md-sb-row">' +
    field('md-sb-find', 'Search', '<span class="md-sb-count"></span>') +
    btn('prev', ICON.up, 'Previous match') +
    btn('next', ICON.down, 'Next match') +
    btn('toggle', ICON.swap, 'Replace') +
    btn('x', ICON.close, 'Clear / close') +
    '</div>' +
    '<div class="md-sb-row md-sb-rep" hidden>' +
    field('md-sb-repl', 'Replace with', '') +
    '<span class="md-sb-btn md-sb-txt" role="button" tabindex="0" data-a="rep">Replace</span>' +
    '<span class="md-sb-btn md-sb-txt" role="button" tabindex="0" data-a="all">All</span>' +
    '</div>';
  findEl = bar.querySelector('#md-sb-find');
  replEl = bar.querySelector('#md-sb-repl');
  repRow = bar.querySelector('.md-sb-rep');
  countEl = bar.querySelector('.md-sb-count');
  toggleEl = bar.querySelector('[data-a="toggle"]');
  header.append(bar);

  // keep keyboard and focus in the input while tapping bar buttons
  bar.addEventListener('mousedown', e => {
    if (e.target.closest('[data-a]')) e.preventDefault();
  });
  bar.addEventListener('click', e => {
    const el = e.target.closest('[data-a]');
    if (el) ACTIONS[el.dataset.a]();
  });
  bar.addEventListener('keydown', e => {
    const el = e.target.closest('[data-a]');
    if (el && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      ACTIONS[el.dataset.a]();
    }
  });
  findEl.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(refresh, 80);
  });
  findEl.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      e.preventDefault();
      e.stopPropagation();
      clearTimeout(timer);
      ACTIONS[e.shiftKey ? 'prev' : 'next']();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      e.stopPropagation();
      close();
    }
  });
  replEl.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      e.preventDefault();
      e.stopPropagation();
      replaceOne();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      e.stopPropagation();
      close();
    }
  });
}

export default function SearchBar() {
  header = document.getElementById('header');
  const el = document.getElementById('cm-search');
  if (!header || !el) return;
  build();
  el.addEventListener('mousedown', e => e.preventDefault());
  el.addEventListener('click', open);
  el.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      open();
    }
  });
}
'''

SEARCH_CSS = r'''/* toolbar: Styles, Search, Beautify ... Docs, Select all, Copy, Paste (end of row 1); Homepage on row 2 */
.compact-layout #stylus-edit #header #cm-search { order: 11; }
.compact-layout #stylus-edit #header #beautify { order: 12; }
.compact-layout #stylus-edit #header #testRE { order: 13; }
.compact-layout #stylus-edit #header #from-mozilla { order: 14; }
.compact-layout #stylus-edit #header #to-mozilla { order: 15; }
.compact-layout #stylus-edit #header #basic-info a[href*="Writing-styles"] { order: 16; }
.compact-layout #stylus-edit #header #usercss-docs { order: 17; }
.compact-layout #stylus-edit #header #cm-select-all { order: 30; margin-left: auto !important; }
.compact-layout #stylus-edit #header #cm-copy { order: 31; }
.compact-layout #stylus-edit #header #cm-paste { order: 32; }
.compact-layout #stylus-edit #header #url {
  order: 34;
  margin: 0 !important;
  flex: 0 0 clamp(56px, calc((100% - 28px) / 8), 96px);
  width: auto;
  max-width: none;
}
.compact-layout #stylus-edit #header #preview-error { order: 34; }
.compact-layout #stylus-edit #header #new-as { order: 34; }
.compact-layout #stylus-edit #header #preview-error[hidden],
.compact-layout #stylus-edit #header #url:not([href^="http"]) { display: none !important; }

/* search bar: replaces the toolbar rows while open (normal flow, no fixed heights) */
.compact-layout #stylus-edit #header.md-sb-on :is([data-label], .md-break, details, #new-as) { display: none !important; }
#header > #md-sb {
  order: 4;
  flex: 1 1 100%;
  box-sizing: border-box;
  margin: 0 !important;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
#md-sb[hidden], #md-sb .md-sb-row[hidden] { display: none !important; }
#md-sb .md-sb-row { display: flex; align-items: center; gap: 2px; }
#md-sb .md-sb-field { position: relative; flex: 1 1 auto; min-width: 0; margin-right: 2px; }
#md-sb input {
  display: block;
  width: 100%;
  height: 40px;
  min-height: 0;
  box-sizing: border-box;
  margin: 0;
  padding: 0 56px 0 14px;
  border: 0 !important;
  border-radius: 20px !important;
  outline: none !important;
  background: var(--md-surface-v, #e3e7f2) !important;
  color: var(--md-text, inherit) !important;
  font: 14px/1.2 var(--family, system-ui, sans-serif);
  box-shadow: none;
}
#md-sb .md-sb-rep input { padding-right: 14px; }
#md-sb input:focus { box-shadow: 0 0 0 2px var(--md-primary, #0b57d0) !important; }
#md-sb .md-sb-count {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--md-text-2, #555);
  font: 500 12px/1 var(--family, system-ui, sans-serif);
  pointer-events: none;
}
#md-sb .md-sb-count.none { color: var(--md-danger, #b3261e); }
#md-sb .md-sb-btn {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  width: 38px;
  height: 38px;
  border-radius: 19px;
  color: var(--md-text-2, #555);
  cursor: pointer;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}
#md-sb .md-sb-btn:active { background: var(--md-primary-c, #d3e3fd); }
#md-sb .md-sb-btn.on { background: var(--md-primary-c, #d3e3fd); color: var(--md-on-primary-c, #041e49); }
#md-sb .md-sb-btn svg { width: 22px; height: 22px; fill: currentColor; }
#md-sb .md-sb-txt {
  width: auto;
  padding: 0 12px;
  color: var(--md-primary, #0b57d0);
  font: 500 13px/1 var(--family, system-ui, sans-serif);
}
.cm-md-find { background: rgba(255, 193, 7, .38); border-radius: 2px; }
.md-find-cur { background: rgba(255, 140, 0, .62) !important; outline: 1px solid #f57c00; border-radius: 2px; }
'''

EDIT_HTML_BTN = (
    '\n        <a tabindex="0" id="cm-search" data-label="Search" title="Search and replace">'
    '<i class="i-search"></i></a>'
)


def apply(root, P, log, warn):
    print('== patch2: search bar + Gboard fixes')
    P.put('src/edit/gboard-fix.js', GBOARD_JS)
    P.put('src/edit/gboard-fix.css', GBOARD_CSS)
    P.put('src/edit/search-bar.js', SEARCH_JS)
    P.put('src/edit/search-bar.css', SEARCH_CSS)

    P.edit('src/edit.html',
           r'(id="cm-paste"[^>]*>\s*<i class="i-paste"></i>\s*</a>)',
           r'\1' + EDIT_HTML_BTN, marker='id="cm-search"', regex=True)

    IDX = 'src/edit/index.js'
    P.add_import(IDX, "import './gboard-fix';\n", "'./gboard-fix'")
    P.add_import(IDX, "import SearchBar from './search-bar';\n", 'SearchBar from',
                 after="import PanelPos from './panel-pos';\n")
    P.edit(IDX, '  PanelPos();\n', '  PanelPos();\n  SearchBar();\n', marker='SearchBar();')


if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import patch
    r = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
    apply(r, patch.Patcher(r), patch.log, patch.warn)
    print(f'\nDone. {len(patch.warnings)} warning(s).')
    for w in patch.warnings:
        print('  -', w)
