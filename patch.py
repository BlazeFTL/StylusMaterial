#!/usr/bin/env python3
"""
Stylus "Material Mobile" patch.

Run in the root of your Stylus fork checkout:

    python patch.py                 # apply patch (+ rebuild icon font if deps installed)
    python patch.py --build         # apply, pnpm install, build Firefox MV2, pack .xpi
    python patch.py --no-bump       # keep version as is
    python patch.py --id "{uuid}" --name "Stylus Material"   # fork identity (optional)
    python patch.py --update-url URL --build-number N         # auto-update (CI)

Safe to re-run: every edit is skipped when already applied.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import zipfile
from pathlib import Path

MATERIAL_CSS = r'''/* Material light theme + mobile layout (added by patch.py) */

/* ===== tokens (peach & purple) ===== */
:root {
  --md-primary: #8400ff;
  --md-on-primary: #fff;
  --md-primary-c: #f1e4ff;
  --md-on-primary-c: #3a0873;
  --md-accent: #ff645e;
  --md-on-accent: #2a0300;
  --md-accent-c: #ffd6c4;
  --md-on-accent-c: #3d1306;
  --md-lav: #9191ff;
  --md-grad: linear-gradient(120deg, #910fff 0%, #ff645e 100%);
  --md-cta: var(--md-grad);
  --md-on-cta: #fff;
  --md-surface: #fff;
  --md-bg: #fff8f4;
  --md-surface-v: #ffeee6;
  --md-outline: #85798f;
  --md-outline-v: #f1e2ea;
  --md-text: #000004;
  --md-text-2: #41364d;
  --md-danger: #d93636;
  --md-hover: rgba(132, 0, 255, .06);
  --md-press: rgba(132, 0, 255, .12);
  --md-elev1: 0 1px 2px rgba(80, 20, 120, .14), 0 1px 4px 1px rgba(80, 20, 120, .06);
  --md-elev2: 0 2px 6px rgba(80, 20, 120, .18), 0 6px 16px 2px rgba(80, 20, 120, .1);
  --family: Inter, Roboto, "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif;
  --font-size: 13px;
  --input-height: 32px;
  --icon-font-size: 20px;
}
:root.touch {
  --font-size: 14px;
  --input-height: 40px;
  --icon-font-size: 22px;
}
:root:not([data-ui-theme="dark"]) {
  --bg: var(--md-surface);
  --fg: var(--md-text);
  --accent-1: var(--md-primary);
  --accent-2: var(--md-lav);
  --accent-3: var(--md-surface-v);
  --accent-4: #fff0e8;
  --accent-5: #fffaf7;
  --header-bg: var(--md-surface);
  --zebra: rgba(132, 0, 255, .04);
  --red1: var(--md-danger);
  --focus-color1: var(--md-primary);
  --focus-color2: transparent;
}
:root[data-ui-theme="dark"] {
  --md-primary: #d0b3ff;
  --md-on-primary: #2d0060;
  --md-primary-c: #45217f;
  --md-on-primary-c: #eaddff;
  --md-accent: #ff8a84;
  --md-on-accent: #3d0a07;
  --md-accent-c: #6b2a28;
  --md-on-accent-c: #ffdad4;
  --md-lav: #b4b4ff;
  --md-grad: linear-gradient(120deg, #b98cff 0%, #ff8a84 100%);
  --md-on-cta: #1e0036;
  --md-surface: var(--c100);
  --md-bg: var(--c99);
  --md-surface-v: var(--c90);
  --md-outline: var(--c45);
  --md-outline-v: var(--c75);
  --md-text: var(--fg);
  --md-text-2: var(--c30);
  --md-danger: var(--red1);
  --md-hover: rgba(255, 255, 255, .07);
  --md-press: rgba(255, 255, 255, .13);
  --md-elev1: 0 1px 3px rgba(0, 0, 0, .6);
  --md-elev2: 0 4px 16px rgba(0, 0, 0, .7);
  --focus-color1: var(--md-primary);
  --focus-color2: transparent;
}

/* ===== base ===== */
body[id^="stylus-"] [hidden] { display: none !important; }
html, body { -webkit-tap-highlight-color: transparent; }
body { font-family: var(--family); }
:focus, .CodeMirror-focused { --focus-shadow: 0 0 0 1px var(--md-primary); }
code { border-radius: 6px; border-color: var(--md-outline-v); }
summary:hover { color: var(--md-primary); }
a { color: var(--md-primary); }
a:hover { color: var(--md-primary); }

/* ===== buttons ===== */
html button {
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: var(--input-height);
  min-height: var(--input-height);
  padding: 0 16px !important;
  border: 0 !important;
  border-radius: calc(var(--input-height) / 2) !important;
  background: var(--md-primary-c) !important;
  background-image: none !important;
  color: var(--md-on-primary-c) !important;
  font: 500 13.5px/1 var(--family) !important;
  letter-spacing: .01em;
  box-shadow: none;
  cursor: pointer;
  transition: box-shadow .15s, background-color .15s;
}
html button i { color: inherit !important; }
html button:not(:disabled):hover { box-shadow: inset 0 0 0 999px var(--md-hover); }
html button:not(:disabled):active { box-shadow: inset 0 0 0 999px var(--md-press); }
html button:disabled {
  background: var(--md-surface-v) !important;
  color: var(--md-outline) !important;
  opacity: .7;
  cursor: default;
}
html button.icon {
  width: 40px;
  min-width: 40px;
  padding: 0 !important;
  background: transparent !important;
  color: var(--md-text-2) !important;
  border-radius: 50% !important;
}
html #save-button:not(:disabled),
html .dirty #save-button + button,
html #apply-all-updates,
html #message-box-buttons button:first-child {
  background: var(--md-cta) !important;
  color: var(--md-on-cta) !important;
}
html .split-btn { display: inline-flex; gap: 2px; }
.compact-layout #stylus-edit #header #save-button { min-width: 64px; }
html .split-btn > button:first-child { border-radius: 20px 4px 4px 20px !important; padding-right: 14px !important; }
html .split-btn > .split-btn-pedal {
  margin-left: 0 !important;
  padding: 0 10px !important;
  border-radius: 4px 20px 20px 4px !important;
}
.split-btn-menu {
  border: 0 !important;
  border-radius: 12px;
  box-shadow: var(--md-elev2) !important;
  padding: 6px 0 !important;
  background: var(--md-surface);
}
.split-btn-menu > * { padding: 12px 20px !important; }
.split-btn-menu > :hover { background: var(--md-hover) !important; }

/* ===== inputs ===== */
html :is(input:not([type]), input[type=text], input[type=number], input[type=search],
         input[type=url], input[type=password], input[type=time], input[type=email]),
html textarea,
html select {
  box-sizing: border-box;
  background: var(--md-surface);
  color: var(--md-text);
  border: 1px solid var(--md-outline) !important;
  border-radius: 8px !important;
  font: inherit;
}
html :is(input:not([type]), input[type=text], input[type=number], input[type=search],
         input[type=url], input[type=password], input[type=time], input[type=email]) {
  height: var(--input-height);
  min-height: var(--input-height) !important;
  padding: 0 12px !important;
}
html textarea { padding: 8px 12px; min-height: var(--input-height); }
html select {
  height: var(--input-height);
  padding: 0 30px 0 12px !important;
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
}
html :is(input, textarea, select):hover:not(:disabled):not(:focus) { border-color: var(--md-text-2) !important; }
html :is(input, textarea, select):focus {
  border-color: var(--md-primary) !important;
  box-shadow: 0 0 0 1px var(--md-primary) !important;
  outline: none;
}
html .select-wrapper > select { padding-right: 30px !important; }
html .select-wrapper::after {
  content: '▼';
  font: 22px/1 icons;
  top: 50%;
  right: 6px;
  transform: translateY(-50%);
  color: var(--md-text-2);
  margin: 0;
}
html input[type=search]::-webkit-search-cancel-button { cursor: pointer; }
html input[type=color] { border-radius: 8px !important; }

/* ===== checkbox ===== */
html input[type=checkbox]:not(.slider) {
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  box-sizing: border-box;
  position: relative;
  display: inline-flex;
  flex: 0 0 20px;
  width: 20px;
  height: 20px;
  margin: 0 10px 0 0;
  vertical-align: middle;
  border: 2px solid var(--md-outline) !important;
  border-radius: 4px !important;
  background: transparent !important;
  cursor: pointer;
  transition: background-color .12s, border-color .12s;
}
html input[type=checkbox]:not(.slider)::after,
html input[type=checkbox]:not(.slider):checked::after {
  content: "";
  position: absolute;
  left: 4px;
  top: 0;
  width: 5px !important;
  height: 10px !important;
  box-sizing: content-box;
  border: solid var(--md-on-primary);
  border-width: 0 2px 2px 0;
  background: none;
  font: inherit;
  transform: rotate(45deg) scale(0);
  transition: transform .12s;
}
html input[type=checkbox]:not(.slider):checked {
  background: var(--md-primary) !important;
  border-color: var(--md-primary) !important;
}
html input[type=checkbox]:not(.slider):checked::after { transform: rotate(45deg) scale(1); }
html input[type=checkbox]:not(.slider):hover:not(:disabled) { border-color: var(--md-primary) !important; }
html input[type=checkbox]:not(.slider):disabled { opacity: .45; cursor: default; }
html input[type=checkbox]:not(.slider) + span { color: inherit; }

/* ===== switch ===== */
html input.slider {
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  box-sizing: border-box;
  position: relative;
  display: inline-block;
  flex: 0 0 44px;
  width: 44px !important;
  height: 24px !important;
  margin: 0 !important;
  vertical-align: middle;
  border: 2px solid var(--md-outline) !important;
  border-radius: 12px !important;
  background: var(--md-surface-v) !important;
  box-shadow: none !important;
  cursor: pointer;
  transition: background-color .2s, border-color .2s;
}
html input.slider::after {
  content: "";
  position: absolute;
  top: 50%;
  left: 4px;
  width: 10px;
  height: 10px;
  margin: 0;
  border: 0;
  border-radius: 50%;
  background: var(--md-outline);
  box-shadow: none;
  transform: translateY(-50%);
  transition: left .2s, width .2s, height .2s, background-color .2s;
}
html input.slider:checked {
  background: var(--md-primary) !important;
  border-color: var(--md-primary) !important;
}
html input.slider:checked::after {
  left: 20px;
  width: 16px;
  height: 16px;
  background: var(--md-on-primary);
  border: 0;
}
html input.slider:focus-visible { outline: 2px solid var(--md-primary); outline-offset: 2px; }
html input.slider:disabled { opacity: .45; cursor: default; }

/* ===== radio ===== */
html input[type=radio] {
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  box-sizing: border-box;
  position: relative;
  flex: 0 0 20px;
  width: 20px;
  height: 20px;
  margin: 0 10px 0 0;
  border: 2px solid var(--md-outline);
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
  transition: border-color .12s;
}
html input[type=radio]::after {
  left: 3px;
  top: 3px;
  width: 10px;
  height: 10px;
  background-color: var(--md-primary);
  transform: scale(0);
  transition: transform .12s;
}
html input[type=radio]:checked { border-color: var(--md-primary); }
html input[type=radio]:checked::after { background-color: var(--md-primary); transform: scale(1); }
html .radio-wrapper { min-height: var(--input-height); }

/* ===== misc controls ===== */
input[type=range] { accent-color: var(--md-primary); }
.i-documentation, .i-export, .i-import, .i-info, .i-caution, .i-config { font-size: 20px; }
a.icon > i { color: var(--md-text-2); }
a.icon:hover > i, a:hover > i { color: var(--md-primary); }
[data-cmd="note"] i { color: var(--md-outline); }
::selection { background: var(--md-primary-c); color: var(--md-on-primary-c); }

/* ===== dialogs ===== */
#message-box { background: rgba(0, 0, 0, .4); }
#message-box > div {
  border-radius: 24px;
  overflow: hidden;
  box-shadow: var(--md-elev2);
  background: var(--md-surface);
}
#message-box-title:not(:empty) {
  background: var(--md-surface) !important;
  color: var(--md-text) !important;
  font-size: 1.15rem;
  font-weight: 500;
  padding: 20px 56px 8px 24px;
  min-height: 0;
}
#message-box-title::before { display: none !important; }
#message-box.danger #message-box-title { color: var(--md-danger) !important; }
#message-box-close-icon i { color: var(--md-text-2) !important; padding: 14px; }
#message-box-contents { padding: 8px 24px 16px; }
#message-box-buttons {
  background: transparent !important;
  padding: 8px 16px 16px !important;
  gap: 8px;
  justify-content: flex-start;
}
#message-box-buttons > button { margin: 0 !important; }
html #message-box-buttons button:not(:first-child) {
  background: transparent !important;
  color: var(--md-primary) !important;
}

/* ===== toast (copy / paste) ===== */
#md-snack {
  position: fixed;
  left: 50%;
  bottom: 24px;
  z-index: 99999999;
  max-width: calc(100vw - 32px);
  padding: 12px 20px;
  border-radius: 8px;
  background: #322f35;
  color: #fff;
  font: 14px/1.3 var(--family);
  box-shadow: var(--md-elev2);
  transform: translate(-50%, 24px);
  opacity: 0;
  pointer-events: none;
  transition: opacity .2s, transform .2s;
}
#md-snack.on { opacity: 1; transform: translate(-50%, 0); }

/* ===== editor: toolbar items ===== */
.md-break { display: none; }
#stylus-edit #header [data-label]:not(#cancel-button)::after,
#stylus-edit #header [data-label]#cancel-button::before { white-space: nowrap; }
#stylus-edit #header { background: var(--md-surface); box-shadow: var(--md-elev1); }
#stylus-edit #header a[data-label] { cursor: pointer; }
#stylus-edit #name { border-radius: 10px !important; }
#stylus-edit #reset-name { cursor: pointer; }
#stylus-edit .dirty #save-button { box-shadow: none; }

/* ===== editor: compact (mobile) layout ===== */
.compact-layout #stylus-edit #header {
  padding: 8px 12px 10px !important;
  gap: 6px 4px !important;
  border-bottom: 0 !important;
  align-items: center;
  align-content: flex-start;
}
.compact-layout #stylus-edit #header.sticky { box-shadow: var(--md-elev2); }
.compact-layout #stylus-edit :is(#basic-info, #actions, #details-wrapper) { display: contents; }
.compact-layout #stylus-edit #enabled-label { order: 1; margin: 0 4px 0 0; }
.compact-layout #stylus-edit #enabled-label input { margin: 0 !important; }
.compact-layout #stylus-edit #basic-info-name {
  order: 2;
  flex: 1 1 0 !important;
  min-width: 0 !important;
  max-width: none !important;
  padding: 0 !important;
  overflow: visible;
  position: relative;
}
.compact-layout #stylus-edit #name {
  field-sizing: fixed !important;
  width: 100%;
  max-width: none;
  padding-right: 40px !important;
}
.compact-layout #stylus-edit #reset-name {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
}
.compact-layout #stylus-edit #save { order: 3; margin-left: 4px; flex: 0 0 auto; }
.compact-layout #stylus-edit .md-break { display: block; flex: 0 0 100%; height: 0; }
.compact-layout #stylus-edit .md-break-1 { order: 5; }
.compact-layout #stylus-edit .md-break-2 { order: 35; }

.compact-layout #stylus-edit #header [data-label] {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  gap: 2px;
  box-sizing: border-box;
  width: 56px;
  height: auto !important;
  min-height: 50px;
  margin: 0;
  padding: 4px 2px 3px !important;
  border: 0 !important;
  border-radius: 14px !important;
  background: transparent !important;
  color: var(--md-text-2) !important;
  font: 500 10.5px/1.15 var(--family) !important;
  letter-spacing: 0;
  text-align: center;
  text-decoration: none;
  user-select: none;
}
.compact-layout #stylus-edit #header [data-label]:active { background: var(--md-primary-c) !important; }
.compact-layout #stylus-edit #header [data-label] > i { font-size: 22px; color: var(--md-primary); }
.compact-layout #stylus-edit #header a[data-label]::after { content: attr(data-label); }
.compact-layout #stylus-edit #header #cancel-button { font-size: 0 !important; }
.compact-layout #stylus-edit #header #cancel-button::before {
  content: attr(data-label);
  order: 2;
  font: 500 10.5px/1.15 var(--family);
}
.compact-layout #stylus-edit #header #cancel-button::after { order: 1; font-size: 22px; color: var(--md-primary); }
.compact-layout #stylus-edit #header #usercss-docs {
  mask: none;
  background: transparent;
  width: 58px;
  height: auto;
}
.compact-layout #stylus-edit #header #usercss-docs::before {
  content: "";
  width: 22px;
  height: 22px;
  background: var(--md-primary);
  mask: url("@@USERCSS_ICON@@") no-repeat center / contain;
  -webkit-mask: url("@@USERCSS_ICON@@") no-repeat center / contain;
}
.compact-layout #stylus-edit #header #usercss-docs::after { content: attr(data-label); }
.compact-layout #stylus-edit #cancel-button { order: 10; }
.compact-layout #stylus-edit #cm-copy { order: 11; }
.compact-layout #stylus-edit #cm-paste { order: 12; }
.compact-layout #stylus-edit #cm-select-all { order: 13; }
.compact-layout #stylus-edit #beautify { order: 14; }
.compact-layout #stylus-edit #testRE { order: 15; }
.compact-layout #stylus-edit #from-mozilla { order: 16; }
.compact-layout #stylus-edit #to-mozilla { order: 17; }
.compact-layout #stylus-edit #basic-info a[href*="Writing-styles"] { order: 18; }
.compact-layout #stylus-edit #usercss-docs { order: 19; }
.compact-layout #stylus-edit #url { order: 20; margin: 0; }
.compact-layout #stylus-edit #preview-error { order: 21; }
.compact-layout:not(.is-new-style) #stylus-edit #new-as { display: none; }
.compact-layout #stylus-edit #new-as {
  order: 22;
  flex: 1 1 100%;
  align-items: center;
  gap: 0;
  font-size: 13px;
}
.compact-layout #stylus-edit #new-as > span { font-size: 13px; }
.compact-layout #stylus-edit #new-as input { margin-right: 10px; }
.compact-layout #stylus-edit #details-wrapper > details { order: 40; }

/* section chips */
.compact-layout #stylus-edit #header details {
  border: 0 !important;
  background: transparent !important;
}
.compact-layout #stylus-edit #header summary { list-style: none; }
.compact-layout #stylus-edit #header summary h2 {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 30px;
  margin: 0;
  padding: 0 12px;
  border-radius: 15px;
  background: var(--md-surface-v);
  color: var(--md-text);
  font: 500 12.5px/1 var(--family);
  white-space: nowrap;
}
.compact-layout #stylus-edit #header summary h2.i { font-size: 12.5px; padding-left: 8px; }
.compact-layout #stylus-edit #header summary h2 { font-size: 12px; }
.compact-layout #stylus-edit #header summary h2.i::after {
  order: -1;
  font-size: 18px;
  color: var(--md-primary);
}
.compact-layout #stylus-edit #header details[open] > summary h2 {
  background: var(--md-primary-c);
  color: var(--md-on-primary-c);
}
.compact-layout #stylus-edit #header details[open] > summary + * {
  border-radius: 16px;
  box-shadow: var(--md-elev2);
  background: var(--md-surface);
  padding: 16px;
}
.compact-layout #stylus-edit #lint:not([open]) { padding: 0; }
.compact-layout #stylus-edit #toc, .compact-layout #stylus-edit .lint-report-container { max-width: 80vw; }

/* ===== options page ===== */
#stylus-options { background: var(--md-bg); color: var(--md-text); padding-bottom: calc(var(--input-height) + 28px + env(safe-area-inset-bottom, 0px)); }
#stylus-options header {
  background: var(--md-grad) !important;
  color: var(--md-on-cta);
  padding: 12px 16px;
  min-height: 56px;
  box-sizing: border-box;
  border: 0;
  box-shadow: var(--md-elev1);
  position: relative;
  z-index: 2;
}
#stylus-options header h1 { font-size: 20px; font-weight: 500; }
#stylus-options header i {
  color: var(--md-on-cta) !important;
  font-size: 24px;
  padding: 8px;
  border-radius: 50%;
  cursor: pointer;
}
#stylus-options header i:hover, #stylus-options header i:active { background: rgba(255, 255, 255, .2); }
#stylus-options main { background: var(--md-bg); padding: 8px; box-sizing: border-box; }
#stylus-options .block {
  flex-direction: column;
  align-items: stretch;
  margin: 8px;
  padding: 12px 16px 8px;
  border: 0 !important;
  border-radius: 16px;
  background: var(--md-surface);
  box-shadow: var(--md-elev1);
}
#stylus-options h2 {
  flex: 0 0 auto;
  width: auto;
  margin: 0 0 4px;
  padding: 0;
  background: none;
  color: var(--md-primary);
  font-size: 13px;
  font-weight: 500;
  letter-spacing: .06em;
  text-transform: uppercase;
}
#stylus-options .block > * { padding-left: 0; padding-right: 0; }
#stylus-options .items { width: 100%; }
#stylus-options .items > label,
#stylus-options .items .radio-wrapper { min-height: 48px; }
#stylus-options .items.swap > label {
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}
#stylus-options .items.swap > label > p:first-child {
  order: 0 !important;
  flex: 1 1 auto;
  margin: 0;
}
#stylus-options .items.swap > label > input,
#stylus-options .items.swap > label > input[type=number] {
  order: 1;
  flex: 0 0 auto;
  margin: 0 !important;
}
#stylus-options .items.swap > label > input[type=number] {
  width: 84px;
  text-align: center;
}
#stylus-options .items.swap > label > input[type=color] {
  width: 56px;
  height: 36px;
  padding: 2px !important;
}
#stylus-options input[type=number] { border: 1px solid var(--md-outline) !important; padding: 0 8px !important; }
#stylus-options label.radio-wrapper { justify-content: flex-start; flex-wrap: wrap; row-gap: 2px; }
#stylus-options .items > label + label { border-top: 1px solid var(--md-outline-v); }
#stylus-options .radio-wrapper { align-items: center; }
#stylus-options input[type=time] { margin: 0 6px 0 0; width: 9.2em; min-width: 0; padding: 0 8px !important; }
#stylus-options .radio-wrapper + span { margin-left: 8px; }
#stylus-options .sync-options > div { gap: 12px !important; }
#stylus-options .sync-options[data-enabled] .actions { display: flex; flex-wrap: wrap; gap: 8px; }
#stylus-options .drive-options input { height: var(--input-height); }
#stylus-options textarea { border-color: var(--md-outline) !important; }
#stylus-options footer {
  display: flex;
  gap: 8px;
  height: auto;
  padding: 10px 16px calc(10px + env(safe-area-inset-bottom, 0px));
  background: var(--md-surface) !important;
  border: 0 !important;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, .12);
}
#stylus-options footer button { flex: 1 1 0; margin: 0 !important; padding: 0 8px !important; min-width: 0; }
#stylus-options footer #manage { background: var(--md-cta) !important; color: var(--md-on-cta) !important; }
#stylus-options footer #reset { background: transparent !important; color: var(--md-danger) !important; box-shadow: inset 0 0 0 1px var(--md-outline-v); }
#stylus-options #FOUC h2 { color: var(--md-danger); }
@media (max-width: 549px) {
  #stylus-options { width: 100%; border: 0; box-shadow: none; }
}

/* ===== manage page ===== */
#stylus-manage { background: var(--md-bg); color: var(--md-text); }
#stylus-manage #header {
  background: var(--md-surface) !important;
  box-shadow: var(--md-elev1);
  border-right: 0;
}
#stylus-manage #header h1 { font-size: 22px; font-weight: 500; }
#stylus-manage #stats { background: var(--md-primary); border-radius: 12px; padding: 2px 4px 2px 10px; }
#stylus-manage #installed { background: transparent; }
#stylus-manage .entry { background: var(--md-surface); }
#stylus-manage .entry.odd { background: var(--md-surface); }
#stylus-manage .style-info[data-type=version] { color: var(--md-text-2); }
#stylus-manage .entry.usercss .style-name-link::after {
  background: var(--md-primary-c);
  color: var(--md-on-primary-c);
  border-radius: 6px;
  padding: 2px 6px;
  font-weight: 500;
}
#stylus-manage .entry i { color: var(--md-text-2); }
#stylus-manage .entry .actions a { border-radius: 50%; }
#stylus-manage #search { height: var(--input-height); }
#stylus-manage #wide-inputs .select-wrapper select { max-width: 100%; }
#stylus-manage .select-wrapper { margin-left: 0; }
#stylus-manage .select-wrapper::after { top: 50%; right: 6px; margin: 0; }
#stylus-manage #header select { height: var(--input-height); padding: 0 30px 0 12px !important; }

/* compact: header becomes a card, entries become cards */
.compact-layout #stylus-manage #header {
  position: relative;
  width: 100% !important;
  height: auto;
  padding: 12px 16px 16px;
  overflow: visible;
  z-index: 5;
}
.compact-layout #stylus-manage #manage-settings { flex-flow: column; align-items: stretch; padding: 0; }
.compact-layout #stylus-manage #installed { padding: 8px 12px 24px; flex-direction: column; flex-wrap: nowrap; gap: 10px; }
.compact-layout #stylus-manage #manage-settings { gap: 12px; }
.compact-layout #stylus-manage #filters { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.compact-layout #stylus-manage #filters > #stats { grid-column: 1 / -1; }
.compact-layout #stylus-manage .filter-selection { left: 0; display: flex; align-items: center; gap: 8px; min-width: 0; min-height: 0; }
.compact-layout #stylus-manage #header .filter-selection > label { margin: 0; padding: 0; }
.compact-layout #stylus-manage .filter-selection > label > input { margin-right: 0; }
.compact-layout #stylus-manage #filters > .filter-selection:last-child { grid-column: 1 / -1; }
.compact-layout #stylus-manage .filter-selection > #only-updates > input { margin-right: 10px; }
.compact-layout #stylus-manage .filter-selection .select-wrapper { flex: 1 1 auto; min-width: 0; }
.compact-layout #stylus-manage .filter-selection select { width: 100%; min-width: 0; font-size: 13px; }
.compact-layout #stylus-manage #wide-inputs { gap: 10px; }
.compact-layout #stylus-manage #wide-inputs > * { gap: 8px; }
.compact-layout #stylus-manage #search-wrapper > input { flex: 1 1 auto; width: auto; }
.compact-layout #stylus-manage #actions { display: block; }
.compact-layout #stylus-manage #actions main {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  width: 100%;
  box-sizing: border-box;
  min-width: 0;
  margin: 0;
}
.compact-layout #stylus-manage #actions main > * { margin: 0; min-width: 0; }
.compact-layout #stylus-manage #actions > details { display: none; }
.compact-layout #stylus-manage #actions main button.icon,
.compact-layout #stylus-manage #actions details + main button.icon {
  position: relative;
  width: 100%;
  height: auto;
  min-height: 44px;
  padding: 6px 12px !important;
  justify-content: flex-start;
  gap: 10px;
  border-radius: 14px !important;
  background: var(--md-surface-v) !important;
  color: var(--md-text) !important;
  border: 0 !important;
}
.compact-layout #stylus-manage #actions main button.icon::before {
  content: attr(title);
  order: 2;
  min-width: 0;
  text-align: left;
  white-space: normal;
  font: 500 13px/1.15 var(--family);
}
.compact-layout #stylus-manage #actions main button.icon > :is(i, svg) {
  position: static;
  margin: 0;
  order: 1;
  flex: 0 0 auto;
  font-size: 22px;
  color: var(--md-primary) !important;
}
.compact-layout #stylus-manage #update-history-button::before { content: attr(title) !important; }
.compact-layout #stylus-manage #actions a#add-style { display: block; }
.compact-layout #stylus-manage #actions a#add-style > button { background: var(--md-cta) !important; color: var(--md-on-cta) !important; }
.compact-layout #stylus-manage #actions a#add-style > button i { color: var(--md-on-cta) !important; }
.compact-layout #stylus-manage #backup { display: contents; }
.compact-layout #stylus-manage #backup > button:not(.icon) { width: 100%; height: 44px; border-radius: 14px !important; }
.compact-layout #stylus-manage #backup > .split-btn { display: flex; width: 100%; }
.compact-layout #stylus-manage #backup > .split-btn > button:first-child { flex: 1 1 auto; height: 44px; }
.compact-layout #stylus-manage #backup > .split-btn > button + button { height: 44px; }
.compact-layout #stylus-manage #backup > p { grid-column: 1 / -1; }
.compact-layout #stylus-manage #links main { gap: 4px 16px; }
.compact-layout:not(.empty) #stylus-manage #links summary::after { content: "Links"; }
.compact-layout #stylus-manage #backup-hint summary::after { content: "Backup reminder"; }
.compact-layout:not(.empty) #stylus-manage #links summary::after,
.compact-layout #stylus-manage #backup-hint summary::after {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 14px;
  background: var(--md-surface-v);
  color: var(--md-text-2);
  font: 500 12px/1 var(--family);
}
.compact-layout #stylus-manage #links summary h2::after { content: none; }
.compact-layout #stylus-manage :is(#links, #backup-hint) details { gap: 8px; }
.compact-layout #stylus-manage #disableAll-label { margin: 0 0 4px; display: flex; align-items: center; gap: 4px; }

.compact-layout #stylus-manage .entry {
  display: grid !important;
  grid-template-columns: auto auto minmax(0, 1fr) auto;
  align-items: center;
  padding: 12px 8px 10px 14px !important;
  border: 0 !important;
  border-radius: 16px;
  box-shadow: var(--md-elev1);
  width: 100%;
  contain-intrinsic-block-size: auto 7em;
}
.compact-layout #stylus-manage .entry > * { margin: 0; padding: 0; min-width: 0; max-width: none; flex: none; }
.compact-layout #stylus-manage .entry > .style-name {
  grid-area: 1 / 1 / 2 / 4;
  min-width: 0;
  max-width: none;
  padding: 4px 0 4px 0;
  font-size: 15px;
  font-weight: 500;
}
.compact-layout #stylus-manage .entry > .actions { grid-area: 1 / 4 / 2 / 5; justify-self: end; display: flex; align-items: center; }
.compact-layout #stylus-manage .entry > .style-info[data-type=size] {
  grid-area: 2 / 1;
  justify-self: start;
  padding: 0 10px 0 var(--name-padding-left, 14px);
  font-size: 12px;
  color: var(--md-text-2);
  flex: none;
}
.compact-layout #stylus-manage .entry > .style-info[data-type=age] {
  grid-area: 2 / 2;
  justify-self: start;
  font-size: 12px;
  color: var(--md-text-2);
  flex: none;
}
.compact-layout #stylus-manage .entry > .applies-to {
  grid-area: 3 / 1 / 4 / 5;
  position: relative;
  padding: 8px 32px 0 0 !important;
  flex: none;
}
.compact-layout #stylus-manage .entry .style-name-link { width: auto; flex: 1 1 auto; }
.compact-layout #stylus-manage .entry .targets {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  max-height: calc(var(--num-targets, 3) * 30px);
  width: 100%;
}
.compact-layout #stylus-manage .entry .target {
  position: relative;
  display: inline-flex;
  align-items: center;
  width: auto;
  min-width: 0;
  max-width: 100%;
  height: 26px;
  line-height: 26px;
  padding: 0 10px !important;
  border-radius: 8px;
  background: var(--md-surface-v);
  color: var(--md-text);
  font-size: 12px;
}
.compact-layout.has-favicons #stylus-manage .entry .target { padding-left: 28px !important; }
.compact-layout #stylus-manage .entry.disabled .target { background: var(--md-surface); }
.compact-layout #stylus-manage .entry .target img {
  position: absolute;
  left: 7px;
  top: 5px;
  width: 16px;
  height: 16px;
  margin: 0;
}
.compact-layout #stylus-manage .entry .expander { right: 0; top: 4px; bottom: auto; width: 32px; height: 32px; justify-content: center; border-radius: 50%; }
.compact-layout #stylus-manage .entry .actions > a, .compact-layout #stylus-manage .entry .actions > span {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.compact-layout #stylus-manage .entry .actions a:active { background: var(--md-press); }
.compact-layout #stylus-manage .entry .updater-icons { display: contents; }
.compact-layout #stylus-manage .entry .updater-icons > * { display: none; width: 36px; height: 36px; align-items: center; justify-content: center; }
.compact-layout #stylus-manage .entry .can-update .update,
.compact-layout #stylus-manage .entry.can-update .updater-icons .update,
.compact-layout #stylus-manage .entry.no-update:not(.update-problem):not(.update-done) .up-to-date,
.compact-layout #stylus-manage .entry.update-done .updated,
.compact-layout #stylus-manage .entry.updatable:not(.checking-update) .updater-icons .check-update { display: inline-flex; }
.compact-layout #stylus-manage .entry.disabled { box-shadow: none; background: var(--md-surface-v); }
.compact-layout #stylus-manage .entry.disabled .style-name-link { color: var(--md-text-2); font-weight: 400; }
.compact-layout #stylus-manage .entry .style-name input { margin: 0 12px 0 0; }
.compact-layout #stylus-manage .entry .homepage { margin-left: 2px; }
.compact-layout #stylus-manage .entry .updater-icons .update-note { display: none; }
.compact-layout #stylus-manage .updater-icons > :not(.check-update)::after { max-width: 60vw; }

/* ===== popup ===== */
#stylus-popup { background: var(--md-surface); }
html.mobile:not(.sidebar) { width: 100% !important; }
html.mobile #stylus-popup { min-width: 100% !important; max-width: none !important; width: 100%; }
:root.touch { --entry-h: 48px; --outer-padding: 16px; --inner-padding: 28px; }
#stylus-popup #installed .entry { border-radius: 0; }
#stylus-popup .entry .actions > :not([hidden]) { border-radius: 50%; }
#stylus-popup .entry .actions > :hover,
#stylus-popup .entry .actions > :active { background: var(--md-hover); }
#stylus-popup .entry .actions i { color: var(--md-text-2); }
#stylus-popup .style-name { font-size: 14px; }
.touch #stylus-popup .style-name { font-size: 15px; }
#stylus-popup #toggler { background: var(--md-surface-v); border-bottom: 0; }
#stylus-popup #main-actions { background: var(--md-accent-c); border-bottom: 0; }
#stylus-popup #main-actions a, #stylus-popup #main-actions i { color: var(--md-on-accent-c); }
#stylus-popup #write-style { font-weight: 500; }
#stylus-popup #disableAll-label {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 16px;
  border-left: 0;
}
#stylus-popup #disableAll-label img {
  position: static;
  order: -1;
  width: 20px;
  height: 20px;
  margin: 0;
  filter: none;
}
#stylus-popup #disableAll { color: var(--md-outline); }
html #stylus-popup #disableAll::after { content: ""; }
#stylus-popup #menu { border-radius: 12px; box-shadow: var(--md-elev2); }

/* ===== install-usercss ===== */
#stylus-install-usercss { background: var(--md-bg); }
#stylus-install-usercss #header { background: var(--md-surface) !important; box-shadow: var(--md-elev1); }

/* ===== embedded dialogs / config ===== */
.config-dialog #message-box-contents { padding-top: 4px; }

/* ============================================================
   v2: peach & purple refresh + mobile fixes
   ============================================================ */

/* ----- popup: page ----- */
html.mobile body#stylus-popup {
  min-height: var(--100dvh, 100dvh);
  background: var(--md-bg);
}
#stylus-popup { --border: 1px solid var(--md-outline-v); }
#stylus-popup #unstylable {
  margin: 16px 16px 8px;
  padding: 16px;
  border-radius: 20px;
  background: var(--md-surface);
  box-shadow: var(--md-elev1);
}
#stylus-popup #no-styles {
  margin: 16px 16px 8px;
  padding: 24px 20px;
  border-radius: 24px;
  background: var(--md-surface);
  box-shadow: var(--md-elev1);
  text-align: center;
  line-height: 1.4;
  color: var(--md-text-2);
  cursor: pointer;
}
#stylus-popup #no-styles:hover { color: var(--md-text-2); }
#stylus-popup #no-styles b { display: block; margin-top: 6px; color: var(--md-primary); font-weight: 600; }
#stylus-popup #installed {
  margin: 8px 16px;
  border: 0 !important;
  border-radius: 20px;
  background: var(--md-surface);
  box-shadow: var(--md-elev1);
}
#stylus-popup #installed:empty { display: none; }
#stylus-popup #toggler {
  margin: 8px 16px;
  border: 0;
  border-radius: 16px;
  background: var(--md-surface);
  box-shadow: var(--md-elev1);
}
#stylus-popup #main-actions {
  margin: 8px 16px;
  border: 0 !important;
  border-radius: 16px;
  background: var(--md-accent-c);
  align-items: center;
}
#stylus-popup #disableAll-label { border-radius: 16px; }
#stylus-popup .write-style-link:last-child { color: var(--md-on-accent-c); }

/* ----- popup: bottom action bar with labels ----- */
html body#stylus-popup #popup-options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  flex: 0 0 auto;
  margin-top: auto;
  padding: 12px 16px calc(12px + env(safe-area-inset-bottom, 0px));
  border: 0;
  background: transparent;
}
#stylus-popup #popup-options > a,
#stylus-popup #popup-options .split-btn {
  min-width: 0;
  height: 48px;
  border-radius: 16px;
  background: var(--md-surface);
  box-shadow: var(--md-elev1);
}
#stylus-popup #popup-options a:not(.split-btn-menu > *) {
  color: var(--md-text);
  font: 500 14px/1 var(--family);
  text-decoration: none;
}
#stylus-popup #popup-options > a,
#stylus-popup #popup-options .split-btn > a:first-child {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 14px;
  padding: 0 12px 0 20px;
  border-radius: 16px;
}
#stylus-popup #popup-options .split-btn { display: flex; align-items: stretch; position: relative; gap: 0; }
#stylus-popup #popup-options .split-btn > a:first-child { flex: 1 1 auto; min-width: 0; border-radius: 16px 0 0 16px; }
#stylus-popup #popup-options a.dropdown {
  flex: 0 0 40px;
  min-width: 0;
  height: auto;
  margin: 0;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-left: 1px solid var(--md-outline-v);
  border-radius: 0 16px 16px 0;
}
#stylus-popup #popup-options a:not(.split-btn-menu > *):active { background: var(--md-press); }
#stylus-popup #popup-options a[data-label]::after { content: attr(data-label); }
#stylus-popup #popup-options a:not(.split-btn-menu > *) i { flex: 0 0 auto; min-width: 24px; text-align: center; color: var(--md-primary); font-size: 22px; }
#stylus-popup #popup-options a.dropdown i { font-size: 20px; color: var(--md-text-2); }

/* ----- popup: dropdown menus (vertical sheet) ----- */
html body#stylus-popup #popup-options .split-btn-menu {
  position: absolute;
  top: auto;
  bottom: calc(100% + 8px);
  left: 0;
  right: auto;
  width: max-content;
  min-width: 100%;
  max-width: calc(100vw - 32px);
  padding: 6px;
  border: 0;
  border-radius: 20px;
  background: var(--md-surface);
  box-shadow: var(--md-elev2);
  transform: none;
  z-index: 1000;
}
html.styles-last body#stylus-popup #popup-options .split-btn-menu { top: calc(100% + 8px); bottom: auto; }
html body#stylus-popup #popup-options .split-btn:nth-child(2) .split-btn-menu { left: auto; right: 0; }
#stylus-popup #popup-options .split-btn-menu::before {
  display: block;
  padding: 8px 14px 6px;
  color: var(--md-primary);
  font: 600 11px/1 var(--family);
  letter-spacing: .08em;
  text-transform: uppercase;
}
#stylus-popup #popup-options #popup-manage-button ~ .split-btn-menu::before { content: "Manage"; }
#stylus-popup #popup-options #find-styles-btn ~ .split-btn-menu::before { content: "Search styles on"; }
#stylus-popup #popup-options .split-btn-menu > * {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  width: auto;
  min-width: 0;
  height: 48px;
  padding: 0 14px !important;
  border-radius: 12px;
  background: none;
  box-shadow: none;
  color: var(--md-text);
  font: 500 14px/1 var(--family);
  text-decoration: none;
  white-space: nowrap;
}
#stylus-popup #popup-options .split-btn-menu > :is(:hover, :focus, :active) {
  background: var(--md-primary-c) !important;
  color: var(--md-on-primary-c);
}


/* ----- popup: per-style menu (3 dots) ----- */
#stylus-popup #menu {
  box-sizing: border-box;
  padding-left: 16px;
  padding-right: 16px;
  background: rgba(40, 10, 70, .45);
}
#stylus-popup #menu > div {
  width: 100%;
  max-width: 440px;
  box-sizing: border-box;
  border: 0;
  border-radius: 28px;
  overflow: hidden;
  background: var(--md-surface);
  box-shadow: var(--md-elev2);
}
#stylus-popup #menu > div > * { padding: 12px 20px; }
#stylus-popup #menu header {
  gap: 12px;
  padding: 14px 20px !important;
  border-bottom: 0;
  background: var(--md-surface-v);
  color: var(--md-text);
  font-size: 15px;
  font-weight: 600;
}
#stylus-popup #menu.enabled header { background: var(--md-primary-c); color: var(--md-on-primary-c); }
#stylus-popup #menu.delete header { background: var(--md-danger); color: #fff; }
#stylus-popup #menu.delete header i { color: #fff; }
#stylus-popup #menu header label { display: flex; align-items: center; flex: 1 1 auto; min-width: 0; }
#stylus-popup #menu header a { margin-left: 0; }
#stylus-popup #menu header i { color: var(--md-primary); font-size: 22px; }
#stylus-popup #menu [data-ovr]:not([hidden]) { min-height: 52px; font-size: 14px; }
#stylus-popup #menu [data-ovr] label {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 40px;
  width: 40px;
  height: 40px;
  margin-left: 6px;
  line-height: 40px;
}
html #stylus-popup #menu [data-ovr] label input {
  position: absolute;
  left: 0;
  top: 0;
  width: 40px;
  height: 40px;
  margin: 0;
  border: 0 !important;
  border-radius: 50% !important;
  background: var(--md-surface-v) !important;
}
html #stylus-popup #menu [data-ovr] label input::after { display: none !important; }
html #stylus-popup #menu [data-ovr] label input:checked {
  background: color-mix(in srgb, var(--c, var(--md-primary)) 18%, transparent) !important;
}
#stylus-popup #menu [data-ovr] i { top: 0; font-size: 22px; color: var(--md-outline); }
#stylus-popup #menu main > p:not(#matchedOvr) {
  margin: 4px -20px;
  padding: 10px 20px;
  background: var(--md-surface-v);
  color: var(--md-text-2);
  font-size: 13px;
  line-height: 1.4;
}
#stylus-popup #menu #matchedOvr {
  margin: 8px -20px 0;
  padding: 10px 20px 0;
  border-top: 1px solid var(--md-outline-v);
  color: var(--md-text-2);
  font-size: 12px;
}
#stylus-popup #menu footer {
  direction: ltr !important;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 16px 16px;
  border-top: 0;
  background: transparent;
}
html #stylus-popup #menu footer button { margin: 0; flex: 0 0 auto; padding: 0 18px !important; }
html #stylus-popup #menu footer [data-cmd=cancel] { order: 1; background: var(--md-surface-v) !important; color: var(--md-text) !important; }
html #stylus-popup #menu footer [data-cmd=edit] { order: 2; background: var(--md-cta) !important; color: var(--md-on-cta) !important; }
html #stylus-popup #menu footer [data-cmd=delete] {
  order: 0;
  margin-right: auto;
  background: transparent !important;
  color: var(--md-danger) !important;
  box-shadow: inset 0 0 0 1px var(--md-outline-v);
}
html #stylus-popup #menu.delete footer [data-cmd=delete] { background: var(--md-danger) !important; color: #fff !important; box-shadow: none; }

/* ----- manage: header, empty state, links ----- */
#stylus-manage #header {
  border: 0 !important;
  border-radius: 0 0 24px 24px;
  background: var(--md-surface) !important;
}
.compact-layout #stylus-manage #header { border-bottom: 0 !important; }
.compact-layout #stylus-manage #header h1 {
  display: flex;
  visibility: visible;
  align-items: center;
  gap: 12px;
  margin: -12px -16px 4px;
  padding: 14px 16px;
  background: var(--md-grad);
  color: var(--md-on-cta);
  font: 500 20px/1.2 var(--family);
}
.compact-layout #stylus-manage #header h1::before {
  content: "S";
  display: grid;
  place-items: center;
  flex: 0 0 32px;
  height: 32px;
  box-sizing: border-box;
  border: 2px solid #000;
  border-radius: 9px;
  background: #35f0d8;
  color: #000;
  font: 800 18px/1 var(--family);
}
.compact-layout #stylus-manage #header .filter-selection,
.compact-layout #stylus-manage #header label { background: none; }
.compact-layout.empty #stylus-manage #links { padding: 20px 16px 28px; font-size: 14px; line-height: 1.3; }
.compact-layout.empty #stylus-manage #links::before {
  content: "Get styles";
  display: block;
  margin: 0 4px 12px;
  color: var(--md-primary);
  font: 600 12px/1 var(--family);
  letter-spacing: .08em;
  text-transform: uppercase;
}
.compact-layout #stylus-manage #links main { display: flex; flex-flow: column; gap: 8px; }
.compact-layout #stylus-manage #links main a {
  display: flex;
  align-items: center;
  gap: 12px;
  box-sizing: border-box;
  width: 100%;
  min-height: 52px;
  padding: 8px 8px 8px 8px;
  border-radius: 16px;
  background: var(--md-surface);
  box-shadow: var(--md-elev1);
  color: var(--md-text);
  font-weight: 500;
  text-decoration: none;
}
.compact-layout #stylus-manage #links main a:active { background: var(--md-primary-c); }
.compact-layout #stylus-manage #links main a::before {
  content: "";
  flex: 0 0 36px;
  height: 36px;
  border-radius: 12px;
  background: url("@@EXT_P@@") center / 20px no-repeat, var(--md-primary-c);
}
.compact-layout #stylus-manage #links main a::after {
  content: "";
  flex: 0 0 24px;
  height: 24px;
  margin-left: auto;
  background: url("@@CHEV@@") center / 24px no-repeat;
}
.compact-layout #stylus-manage #links main a:has(> img)::before { display: none; }
.compact-layout #stylus-manage #links main a.target { padding: 8px; line-height: 1.3; overflow: visible; }
.compact-layout #stylus-manage #links main a.target > img {
  position: static;
  flex: 0 0 20px;
  width: 20px;
  height: 20px;
  margin: 0;
  padding: 8px;
  border-radius: 12px;
  background: var(--md-primary-c);
}
[data-ui-theme="dark"].compact-layout #stylus-manage #links main a::before {
  background: url("@@EXT_D@@") center / 20px no-repeat, var(--md-primary-c);
}
.compact-layout #stylus-manage #backup-hint main {
  padding: 12px 14px;
  border-radius: 16px;
  background: var(--md-surface-v);
  color: var(--md-text-2);
  font-size: 13px;
}

/* ----- editor: toolbar fills the row, header accent ----- */
#stylus-edit #header {
  border-radius: 0 0 20px 20px;
  background: var(--md-surface);
}
.compact-layout #stylus-edit #header [data-label],
.compact-layout #stylus-edit #header #usercss-docs {
  flex: 1 1 56px;
  width: auto;
  max-width: 96px;
}

/* ----- editor: code area ----- */
html:not([data-ui-theme="dark"]) .CodeMirror.cm-s-default { background: var(--md-surface); }
html:not([data-ui-theme="dark"]) .cm-s-default .CodeMirror-gutters {
  background: var(--md-bg);
  border-right: 1px solid var(--md-outline-v);
}
html:not([data-ui-theme="dark"]) .cm-s-default .CodeMirror-linenumber { color: var(--md-outline); }
html:not([data-ui-theme="dark"]) .cm-s-default .CodeMirror-activeline-background { background: var(--md-hover); }
html:not([data-ui-theme="dark"]) .cm-s-default .CodeMirror-selected { background: var(--md-accent-c); }
html:not([data-ui-theme="dark"]) .cm-s-default .CodeMirror-cursor { border-left-color: var(--md-primary); }

/* ----- editor: @-moz-document rows must not run under the gutter ----- */
.usercss .applies-to {
  box-sizing: border-box;
  margin: 0;
  padding: 12px calc(12px + var(--cm-bar-width, 0px)) 8px calc(var(--cm-gutter-w, 0px) + 12px);
}
.usercss .applies-to ul { min-width: 0; --input-height: 34px; }
.usercss .applies-to li { flex-wrap: nowrap; gap: 6px; margin-bottom: 6px; }
.usercss .applies-to li .select-wrapper { flex: 0 1 auto; min-width: 0; max-width: 46%; margin-right: 0; }
.usercss .applies-to li select { max-width: 100%; text-overflow: ellipsis; }
.usercss .applies-to li .applies-value-wrapper { flex: 1 1 0; min-width: 0; gap: 6px; }
.usercss .applies-to li .applies-value { flex: 1 1 0; min-width: 0; width: 100%; }
.usercss .applies-to li img { margin: 0; }
.usercss .applies-to .add-applies-to,
.usercss .applies-to .remove-applies-to {
  flex: 0 0 34px;
  width: 34px;
  height: 34px;
  margin: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}
.usercss .applies-to .add-applies-to:active,
.usercss .applies-to .remove-applies-to:active { background: var(--md-press); }
.usercss .applies-to li .add-applies-to:first-child { margin-left: 0; }

/* ----- options: full screen on phones, tidy time row ----- */
html.mobile:has(> body#stylus-options) { padding: 0 !important; }
html.mobile #stylus-options {
  width: 100% !important;
  max-width: none;
  height: var(--100dvh, 100dvh);
  max-height: var(--100dvh, 100dvh);
  margin: 0 !important;
  border: 0 !important;
  border-radius: 0;
  box-shadow: none !important;
}
html.mobile #stylus-options main { flex: 1 1 auto; min-height: 0; }
#stylus-options label:has(> #manage\.newUI) { display: none; }
#stylus-options main { padding: 14px 14px 24px; }
#stylus-options .block {
  margin: 0 0 14px;
  padding: 0 16px 8px;
  overflow: hidden;
  border: 1px solid var(--md-outline-v) !important;
  box-shadow: var(--md-elev1);
}
#stylus-options .block > h2 {
  position: relative;
  margin: 0 -16px 6px;
  padding: 14px 16px 12px 30px;
  border-bottom: 1px solid var(--md-outline-v);
  background: var(--md-surface-v);
  color: var(--md-text);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
}
#stylus-options .block > h2::before {
  content: "";
  position: absolute;
  left: 14px;
  top: 50%;
  width: 4px;
  height: 16px;
  margin-top: -8px;
  border-radius: 2px;
  background: var(--md-grad);
}
#stylus-options label.radio-wrapper:has(.md-time-range) { flex-wrap: wrap; }
#stylus-options .md-time-range {
  display: flex;
  flex: 1 0 100%;
  align-items: center;
  gap: 10px;
  box-sizing: border-box;
  margin: 2px 0 10px 30px;
}
#stylus-options .md-time-range input[type=time] { flex: 1 1 0; width: auto; min-width: 0; margin: 0; }
#stylus-options .md-time-range .md-to { flex: 0 0 auto; color: var(--md-text-2); font-size: 13px; }
'''

CLIPBOARD_JS = r'''import editor from './editor';

let snackEl;
let snackTimer;

function snack(msg) {
  if (!snackEl) {
    snackEl = document.createElement('div');
    snackEl.id = 'md-snack';
    document.body.append(snackEl);
  }
  snackEl.textContent = msg;
  snackEl.classList.add('on');
  clearTimeout(snackTimer);
  snackTimer = setTimeout(() => snackEl.classList.remove('on'), 1800);
}

function activeCm() {
  const live = editor.getEditors(true).filter(Boolean);
  if (live.length) {
    return live.reduce((a, b) => ((b.lastActive || 0) > (a.lastActive || 0) ? b : a));
  }
  return editor.getEditors()[0];
}

async function writeClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // fall through to execCommand
  }
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.cssText = 'position:fixed;top:0;left:0;opacity:0';
  document.body.append(ta);
  ta.select();
  let ok = false;
  try {
    ok = document.execCommand('copy');
  } catch {
    // ignore
  }
  ta.remove();
  return ok;
}

async function copy() {
  const cm = activeCm();
  if (!cm) return;
  const hasSel = cm.somethingSelected();
  const text = hasSel ? cm.getSelection() : cm.getValue();
  snack(await writeClipboard(text)
    ? (hasSel ? 'Copied selection' : `Copied all (${text.length} chars)`)
    : 'Copy failed');
}

async function paste() {
  const cm = activeCm();
  if (!cm) return;
  let text;
  try {
    text = await navigator.clipboard.readText();
  } catch {
    // fall through to execCommand
  }
  if (text == null) {
    cm.focus();
    cm.execCommand('selectAll');
    let ok = false;
    try {
      ok = document.execCommand('paste');
    } catch {
      // ignore
    }
    if (!ok) snack('Paste blocked: long-press the editor and tap Paste');
    return;
  }
  if (!text) {
    snack('Clipboard is empty');
    return;
  }
  cm.operation(() => {
    const last = cm.lastLine();
    cm.replaceRange(text, {line: cm.firstLine(), ch: 0}, {line: last, ch: cm.getLine(last).length}, 'paste');
    const end = cm.lastLine();
    cm.setCursor({line: end, ch: cm.getLine(end).length});
  });
  cm.focus();
  snack(`Pasted ${text.length} chars`);
}

function selectAll() {
  const cm = activeCm();
  if (!cm) return;
  cm.execCommand('selectAll');
  cm.focus();
}

export default function ClipboardBar() {
  for (const [id, fn] of [['cm-copy', copy], ['cm-paste', paste], ['cm-select-all', selectAll]]) {
    const el = document.getElementById(id);
    if (!el) continue;
    // keep focus (and the on-screen keyboard) in the editor
    el.addEventListener('mousedown', e => e.preventDefault());
    el.addEventListener('click', fn);
    el.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        fn();
      }
    });
  }
}
'''

# Material Design icons (Apache-2.0), 24x24. Existing glyph ids (the unicode char
# in <svg id="">) are preserved so global.css and every .i-* class keep working.
ICONS = {
    'attention': 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z',
    'beautify': 'M7.5 5.6L10 7 8.6 4.5 10 2 7.5 3.4 5 2l1.4 2.5L5 7zm12 9.8L17 14l1.4 2.5L17 19l2.5-1.4L22 19l-1.4-2.5L22 14zM22 2l-2.5 1.4L17 2l1.4 2.5L17 7l2.5-1.4L22 7l-1.4-2.5zm-7.63 5.29c-.39-.39-1.02-.39-1.41 0L1.29 18.96c-.39.39-.39 1.02 0 1.41l2.34 2.34c.39.39 1.02.39 1.41 0L16.7 11.05c.39-.39.39-1.02 0-1.41l-2.33-2.35zm-1.03 5.49l-2.12-2.12 2.44-2.44 2.12 2.12-2.44 2.44z',
    'caution': 'M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z',
    'check1': 'M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z',
    'check2': 'M18 7l-1.41-1.41-6.34 6.34 1.41 1.41L18 7zm4.24-1.41L11.66 16.17 7.48 12l-1.41 1.41L11.66 19l12-12-1.42-1.41zM.41 13.41L6 19l1.41-1.41L1.83 12 .41 13.41z',
    'checked': 'M19 3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-9 14l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z',
    'close-thin': 'M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z',
    'close': 'M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z',
    'cloud': 'M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z',
    'config-aux': 'M3 17v2h6v-2H3zM3 5v2h10V5H3zm10 16v-2h8v-2h-8v-2h-2v6h2zM7 9v2H3v2h4v2h2V9H7zm14 4v-2H11v2h10zm-6-4h2V7h4V5h-4V3h-2v6z',
    'config-doc': 'M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z',
    'config-editor': 'M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z',
    'config-lite': 'M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z',
    'config': 'M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z',
    'copy': 'M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z',
    'documentation': 'M21 5c-1.11-.35-2.33-.5-3.5-.5-1.95 0-4.05.4-5.5 1.5-1.45-1.1-3.55-1.5-5.5-1.5S2.45 4.9 1 6v14.65c0 .25.25.5.5.5.1 0 .15-.05.25-.05C3.1 20.45 5.05 20 6.5 20c1.95 0 4.05.4 5.5 1.5 1.35-.85 3.8-1.5 5.5-1.5 1.65 0 3.35.3 4.75 1.05.1.05.15.05.25.05.25 0 .5-.25.5-.5V6c-.6-.45-1.25-.75-2-1zm0 13.5c-1.1-.35-2.3-.5-3.5-.5-1.7 0-4.15.65-5.5 1.5V8c1.35-.85 3.8-1.5 5.5-1.5 1.2 0 2.4.15 3.5.5v11.5z',
    'edit': 'M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z',
    'empty': 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zM4 12c0-4.42 3.58-8 8-8 1.85 0 3.55.63 4.9 1.69L5.69 16.9C4.63 15.55 4 13.85 4 12zm8 8c-1.85 0-3.55-.63-4.9-1.69L18.31 7.1C19.37 8.45 20 10.15 20 12c0 4.42-3.58 8-8 8z',
    'export': 'M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z',
    'external': 'M19 19H5V5h7V3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z',
    'import': 'M9 16h6v-6h4l-7-7-7 7h4zm-4 2h14v2H5z',
    'info': 'M11 7h2v2h-2zm0 4h2v6h-2zm1-9C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z',
    'install': 'M12 16.5l4-4h-3v-9h-2v9H8l4 4zm9-13h-6v1.99h6v14.03H3V5.49h6V3.5H3c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2v-14c0-1.1-.9-2-2-2z',
    'log': 'M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z',
    'manage': 'M3 14h4v-4H3v4zm0 5h4v-4H3v4zM3 9h4V5H3v4zm5 5h13v-4H8v4zm0 5h13v-4H8v4zM8 5v4h13V5H8z',
    'menu': 'M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z',
    'minus': 'M19 13H5v-2h14v2z',
    'pin': 'M14 4v5c0 1.12.37 2.16 1 3H9c.65-.86 1-1.9 1-3V4h4m3-2H7c-.55 0-1 .45-1 1s.45 1 1 1h1v5c0 1.66-1.34 3-3 3v2h5.97v7l1 1 1-1v-7H19v-2c-1.66 0-3-1.34-3-3V4h1c.55 0 1-.45 1-1s-.45-1-1-1z',
    'pinned': 'M16 9V4h1c.55 0 1-.45 1-1s-.45-1-1-1H7c-.55 0-1 .45-1 1s.45 1 1 1h1v5c0 1.66-1.34 3-3 3v2h5.97v7l1 1 1-1v-7H19v-2c-1.66 0-3-1.34-3-3z',
    'plus': 'M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z',
    'regex': 'M7 9H2V7h5v2zm0 3H2v2h5v-2zm13.59 7l-3.83-3.83c-.8.52-1.74.83-2.76.83-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5c0 1.02-.31 1.96-.83 2.75L22 17.59 20.59 19zM17 11c0-1.65-1.35-3-3-3s-3 1.35-3 3 1.35 3 3 3 3-1.35 3-3zM2 19h10v-2H2v2z',
    'reorder': 'M9 3L5 6.99h3V14h2V6.99h3L9 3zm7 14.01V10h-2v7.01h-3L15 21l4-3.99h-3z',
    'search': 'M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z',
    'select-arrow': 'M7 10l5 5 5-5z',
    'share': 'M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92 1.61 0 2.92-1.31 2.92-2.92s-1.31-2.92-2.92-2.92z',
    'sort-down': 'M20 12l-1.41-1.41L13 16.17V4h-2v12.17l-5.58-5.59L4 12l8 8 8-8z',
    'undo': 'M12.5 8c-2.65 0-5.05.99-6.9 2.6L2 7v9h9l-3.62-3.62c1.39-1.16 3.16-1.88 5.12-1.88 3.54 0 6.55 2.31 7.6 5.5l2.37-.78C21.08 11.03 17.15 8 12.5 8z',
    'update-check': 'M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z',
    'v': 'M16.59 8.59L12 13.17 7.41 8.59 6 10l6 6 6-6z',
    # new icons (id char, path)
    'paste': ('\u2397', 'M19 2h-4.18C14.4.84 13.3 0 12 0c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm7 18H5V4h2v3h10V4h2v16z'),
    'select-all': ('\u26f6', 'M3 5h2V3c-1.1 0-2 .9-2 2zm0 8h2v-2H3v2zm4 8h2v-2H7v2zM3 9h2V7H3v2zm10-6h-2v2h2V3zm6 0v2h2c0-1.1-.9-2-2-2zM5 21v-2H3c0 1.1.9 2 2 2zm-2-4h2v-2H3v2zM9 3H7v2h2V3zm2 18h2v-2h-2v2zm8-8h2v-2h-2v2zm0 8c1.1 0 2-.9 2-2h-2v2zm0-12h2V7h-2v2zm0 8h2v-2h-2v2zm-4 4h2v-2h-2v2zm0-16h2V3h-2v2zM7 17h10V7H7v10zm2-8h6v6H9V9z'),
}

SVG_TPL = ('<svg id="{id}" version="1.1" xmlns="http://www.w3.org/2000/svg" '
           'viewBox="0 0 24 24"><path d="{d}"/></svg>\n')

# (label, element-id) -> inserted as data-label so mobile layout can show captions
TOOLBAR_NEW = (
    '        <a tabindex="0" id="cm-select-all" data-label="Select all" title="Select all">'
    '<i class="i-select-all"></i></a>\n'
    '        <a tabindex="0" id="cm-copy" data-label="Copy" title="Copy selection (or everything)">'
    '<i class="i-copy"></i></a>\n'
    '        <a tabindex="0" id="cm-paste" data-label="Paste" title="Paste">'
    '<i class="i-paste"></i></a>\n'
)

PAGES = ('edit', 'manage', 'options', 'popup', 'install-usercss', 'sidepanel')

warnings = []


def log(tag, msg):
    print(f'  [{tag}] {msg}')


def warn(msg):
    warnings.append(msg)
    log('WARN', msg)


def read(p):
    return p.read_text(encoding='utf-8')


def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)


class Patcher:
    def __init__(self, root):
        self.root = root

    def path(self, rel):
        return self.root / rel

    def put(self, rel, text):
        p = self.path(rel)
        if p.exists() and read(p) == text:
            log('same', rel)
            return
        write(p, text)
        log('write', rel)

    def edit(self, rel, old, new, marker=None, regex=False, count=1, optional=False):
        p = self.path(rel)
        if not p.exists():
            warn(f'missing file {rel}')
            return False
        s = read(p)
        if marker and marker in s:
            log('skip', f'{rel}: {marker[:40]}')
            return True
        if regex:
            s2, n = re.subn(old, (lambda m: m.expand(new)) if '\\' in new else new, s,
                            count=0 if count == 0 else count, flags=re.S)
        else:
            n = s.count(old)
            if n:
                s2 = s.replace(old, new) if count == 0 else s.replace(old, new, count)
        if not n:
            if optional:
                log('skip', f'{rel}: nothing to change')
            else:
                warn(f'anchor not found in {rel}: {old[:60]!r}')
            return False
        write(p, s2)
        log('edit', f'{rel}: {(marker or old)[:40]}')
        return True

    def add_import(self, rel, line, marker, after=None):
        p = self.path(rel)
        if not p.exists():
            warn(f'missing file {rel}')
            return
        s = read(p)
        if marker in s:
            log('skip', f'{rel}: {marker}')
            return
        if after and after in s:
            i = s.index(after) + len(after)
        else:
            ms = list(re.finditer(r"^import\s+[^;(][^;]*;[ \t]*\n", s, re.M))
            if not ms:
                warn(f'no import found in {rel}')
                return
            i = ms[-1].end() - 0
            if after:
                warn(f'{rel}: anchor {after!r} missing, appended to imports')
        write(p, s[:i] + (line if s[i - 1] == '\n' else '\n' + line) + s[i:])
        log('edit', f'{rel}: {marker}')


EXTRA_PATHS = {
    'chev': 'M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z',
}


def svg_uri(d, fill):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
           '<path fill="%s" d="%s"/></svg>' % (fill, d))
    return 'data:image/svg+xml,' + urllib.parse.quote(svg, safe="/:=,;()' ").replace('"', '%22')


def material_css(P):
    icon = P.path('src/icon/usercss.svg')
    svg = read(icon) if icon.exists() else (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="%s"/></svg>' % ICONS['config-editor'])
    svg = re.sub(r'\s+', ' ', svg.replace('<!-- pixel-aligned -->', '')).strip()
    uri = 'data:image/svg+xml,' + urllib.parse.quote(svg, safe="/:=,;()' ")
    css = MATERIAL_CSS.replace('@@USERCSS_ICON@@', uri.replace('"', '%22'))
    return (css
            .replace('@@EXT_P@@', svg_uri(ICONS['external'], '#8400ff'))
            .replace('@@EXT_D@@', svg_uri(ICONS['external'], '#d0b3ff'))
            .replace('@@CHEV@@', svg_uri(EXTRA_PATHS['chev'], '#85798f')))


def bump_minor(ver):
    m = re.match(r'^(\d+)\.(\d+)\.(\d+)(.*)$', ver)
    if not m:
        return ver
    return f'{m[1]}.{int(m[2]) + 1}.{m[3]}{m[4]}'


def apply(root, args):
    P = Patcher(root)
    print('== files')
    P.put('src/material/material.css', material_css(P))
    for page in PAGES:
        # one wrapper per page keeps the stylesheet inside that page's own chunk,
        # i.e. loaded after the page CSS (src/css/* would land in the early shared chunk)
        P.put(f'src/material/{page}.css', "@import './material.css';\n")
    P.put('src/edit/clipboard-bar.js', CLIPBOARD_JS)

    print('== icons')
    for name, spec in ICONS.items():
        rel = f'src/icons/{name}.svg'
        p = P.path(rel)
        if isinstance(spec, tuple):
            ch, d = spec
        else:
            d = spec
            if not p.exists():
                warn(f'icon file missing, skipped: {rel}')
                continue
            m = re.search(r'<svg[^>]*?\sid="\s*([^\s"]+)\s*"', read(p))
            if not m:
                warn(f'no glyph id in {rel}')
                continue
            ch = m.group(1)
        write(p, SVG_TPL.format(id=ch, d=d))
    log('ok', f'{len(ICONS)} svg files')

    print('== html')
    E = 'src/edit.html'
    P.edit(E, '<input type="checkbox" id="enabled">',
           '<input type="checkbox" id="enabled" class="slider">', marker='id="enabled" class="slider"')
    for old, new in [
        ('<button id="cancel-button" ', '<button id="cancel-button" data-label="Styles" '),
        ('<a id="beautify" ', '<a id="beautify" data-label="Beautify" '),
        ('<a id="testRE" ', '<a id="testRE" data-label="RegExp" '),
        ('<a tabindex="0" id="from-mozilla" ', '<a tabindex="0" id="from-mozilla" data-label="Import" '),
        ('<a tabindex="0" id="to-mozilla" ', '<a tabindex="0" id="to-mozilla" data-label="Export" '),
        ('<a class="icon" target="_blank" i18n="title:linkStylusWiki"',
         '<a class="icon" target="_blank" data-label="Docs" i18n="title:linkStylusWiki"'),
        ('id="usercss-docs"', 'id="usercss-docs" data-label="UserCSS docs"'),
        ('<a id="url" target="_blank"', '<a id="url" data-label="Homepage" target="_blank"'),
        ('id="preview-error" target="_blank"', 'id="preview-error" data-label="Preview error" target="_blank"'),
    ]:
        P.edit(E, old, new, marker=re.search(r'data-label="[^"]+"', new).group(0))
    P.edit(E, r'(id="to-mozilla"[^>]*>\s*<i class="i-export"></i>\s*</a>)',
           r'\1\n' + TOOLBAR_NEW.replace('\\', '\\\\'), marker='id="cm-copy"', regex=True)
    P.edit(E, '<div id="details-wrapper">',
           '<div class="md-break md-break-1"></div><div class="md-break md-break-2"></div>\n'
           '      <div id="details-wrapper">', marker='md-break-1')
    for old, new in [
        ('<a id="popup-manage-button" ', '<a id="popup-manage-button" data-label="Manage" '),
        ('<a id="find-styles-btn" ', '<a id="find-styles-btn" data-label="Find styles" '),
        ('<a id="help" ', '<a id="help" data-label="Help" '),
        ('<a id="options-btn" ', '<a id="options-btn" data-label="Options" '),
    ]:
        P.edit('src/popup.html', old, new, marker=re.search(r'data-label="[^"]+"', new).group(0))
    P.edit('src/options.html',
           r'(<input type="time" required id="schemeSwitcher\.nightStart">)\s*~\s*'
           r'(<input type="time" required id="schemeSwitcher\.nightEnd">)',
           r'<span class="md-time-range">\1<span class="md-to">to</span>\2</span>',
           marker='md-time-range', regex=True)
    for rel in ('src/manage.html', 'src/popup.html'):
        P.edit(rel, r'<svg class="hollow-gear"[^>]*>\s*<text[^>]*>\u2699</text>\s*</svg>',
               '<i class="i-config"></i>', regex=True, count=0, optional=True)

    print('== js entry points')
    for page in PAGES:
        P.add_import(f'src/{page}/index.js', f"import '@/material/{page}.css';\n", f'@/material/{page}.css')
    P.add_import('src/edit/index.js', "import ClipboardBar from './clipboard-bar';\n",
                 'ClipboardBar from', after="import EditorHeader from './editor-header';\n")
    P.edit('src/edit/index.js', '  EditorHeader();\n', '  EditorHeader();\n  ClipboardBar();\n',
           marker='ClipboardBar();')

    print('== mobile behavior (card list always, compact layout always, editor gutter)')
    # backups can import prefs (manage.newUI=false, compactWidth) that break the card layout
    P.edit('src/manage/ui.js', 'const tableView_ = __values[pManageNewUi];',
           'const tableView_ = true; // mobile fork: card list only', marker='const tableView_ = true')
    P.edit('src/background/index.js', "if (MOBILE) prefs.set('manage.newUI', false);",
           "if (MOBILE) prefs.set('manage.newUI', true);", marker="prefs.set('manage.newUI', true)")
    P.edit('src/js/dom-init.js', "prefs.subscribe('compactWidth', (k, val) => {\n",
           "prefs.subscribe('compactWidth', (k, val) => {\n    if (MOBILE) val = 99999; // mobile fork: always compact\n",
           marker='val = 99999')
    P.edit('src/edit/moz-section-widget.js',
           "        const value = cm.display.barWidth + 'px';\n"
           "        if (widget[KEY] !== value) {\n"
           "          widget[KEY] = value;\n"
           "          node.style.setProperty('--cm-bar-width', value);\n"
           "        }",
           "        const value = cm.display.barWidth + 'px';\n"
           "        const gutterW = cm.display.gutters.offsetWidth + 'px';\n"
           "        if (widget[KEY] !== value + gutterW) {\n"
           "          widget[KEY] = value + gutterW;\n"
           "          node.style.setProperty('--cm-bar-width', value);\n"
           "          node.style.setProperty('--cm-gutter-w', gutterW);\n"
           "        }",
           marker='--cm-gutter-w')

    print('== manifest / version')
    P.edit('src/manifest.json', '"alarms",\n', '"alarms",\n    "clipboardRead",\n    "clipboardWrite",\n',
           marker='"clipboardRead"')
    pj = P.path('package.json')
    m = re.search(r'"version":\s*"([^"]+)"', read(pj))
    if m and (not args.no_bump or args.build_number is not None):
        old = m.group(1)
        new = old if args.no_bump else bump_minor(old)
        if args.build_number is not None:
            core = re.match(r'^\d+\.\d+\.\d+', new)
            new = f'{core.group(0) if core else new}.{args.build_number}'
        if new != old:
            P.edit('package.json', f'"version": "{old}"', f'"version": "{new}"')
        mj = P.path('src/manifest.json')
        mm = re.search(r'"version":\s*"([^"]+)"', read(mj))
        if mm and mm.group(1) != new:
            P.edit('src/manifest.json', f'"version": "{mm.group(1)}"', f'"version": "{new}"')
        log('ver', f'{old} -> {new}')
    if args.name:
        P.edit('src/manifest.json', r'^(\{\s*"name":\s*)"[^"]*"', rf'\1"{args.name}"', regex=True)
    if args.id:
        P.edit('src/manifest-mv2-firefox.json', r'("id":\s*)"[^"]*"', rf'\1"{args.id}"', regex=True)
    if args.update_url:
        mf = 'src/manifest-mv2-firefox.json'
        if '"update_url"' in read(P.path(mf)):
            P.edit(mf, r'("update_url":\s*)"[^"]*"', rf'\1"{args.update_url}"', regex=True)
        else:
            P.edit(mf, r'("gecko":\s*\{)', rf'\1\n      "update_url": "{args.update_url}",', regex=True)


def run(cmd, cwd, **kw):
    print('  $', ' '.join(cmd))
    return subprocess.run(cmd, cwd=cwd, check=True, shell=(os.name == 'nt'), **kw)


def build_icons(root):
    print('== icon font')
    if not (root / 'node_modules' / 'svg2ttf').exists():
        warn('node_modules missing: run `pnpm install` then `pnpm build-icons` '
             '(regenerates src/css/icons.woff2 + glyph list in global.css)')
        return
    run(['node', 'tools/build-icons.mjs'], root)


def build(root):
    print('== build (firefox mv2)')
    run(['node', 'tools/build.js', 'build', 'firefox'], root)
    dist = root / ('dist' if os.environ.get('GITHUB_ACTIONS') else 'dist-firefox-mv2')
    if not dist.is_dir():
        warn(f'build output not found: {dist}')
        return
    import json
    ver = json.loads(read(dist / 'manifest.json')).get('version', 'x')
    xpi = root / f'stylus-material-{ver}.xpi'
    with zipfile.ZipFile(xpi, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(dist.rglob('*')):
            if f.is_file():
                z.write(f, f.relative_to(dist).as_posix())
    log('xpi', str(xpi))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('repo', nargs='?', default=None, help='Stylus checkout (default: cwd, else script dir)')
    ap.add_argument('--build', action='store_true', help='pnpm install + build firefox mv2 + pack .xpi')
    ap.add_argument('--no-bump', action='store_true', help='do not bump the minor version')
    ap.add_argument('--id', help='gecko add-on id for src/manifest-mv2-firefox.json')
    ap.add_argument('--name', help='extension name for src/manifest.json')
    ap.add_argument('--update-url', help='gecko update_url (Firefox auto-update manifest)')
    ap.add_argument('--build-number', type=int, help='append as 4th version part (must grow every release)')
    ap.add_argument('--strict', action='store_true', help='exit 1 if any anchor was not found')
    args = ap.parse_args()

    cands = [Path(args.repo)] if args.repo else [Path.cwd(), Path(__file__).resolve().parent]
    root = next((c for c in cands if (c / 'src' / 'edit.html').exists()), None)
    if not root:
        sys.exit('Stylus checkout not found (src/edit.html missing). Pass the repo path.')
    root = root.resolve()
    print(f'Stylus repo: {root}')

    if args.build and not (root / 'node_modules' / 'svg2ttf').exists():
        print('== pnpm install')
        run(['pnpm', 'install'], root)

    apply(root, args)
    build_icons(root)
    if args.build:
        build(root)

    print(f'\nDone. {len(warnings)} warning(s).')
    for w in warnings:
        print('  -', w)
    if not args.build:
        print('Next: pnpm build-firefox   (output: dist-firefox-mv2/)')
    if args.strict and warnings:
        sys.exit(1)


if __name__ == '__main__':
    main()
