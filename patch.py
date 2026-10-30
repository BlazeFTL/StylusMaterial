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

MATERIAL_CSS = r'''/* Flat Material mobile theme: Violentmonkey layout + Gboard-style settings (added by patch.py) */

/* ===== tokens ===== */
:root {
  --md-primary: #0b57d0;
  --md-on-primary: #fff;
  --md-primary-c: #d3e3fd;
  --md-on-primary-c: #041e49;
  --md-accent: #0b57d0;
  --md-on-accent: #fff;
  --md-accent-c: #c2d7fa;
  --md-on-accent-c: #041e49;
  --md-lav: #5b8def;
  --md-grad: var(--md-primary);
  --md-cta: var(--md-primary);
  --md-on-cta: #fff;
  --md-surface: #fff;
  --md-bg: #eef1f9;
  --md-surface-v: #e3e7f2;
  --md-outline: #747780;
  --md-outline-v: #d5d9e5;
  --md-text: #1a1c22;
  --md-text-2: #4a4e59;
  --md-danger: #b3261e;
  --md-hover: rgba(11, 87, 208, .07);
  --md-press: rgba(11, 87, 208, .13);
  --md-elev1: 0 1px 2px rgba(20, 30, 70, .10), 0 1px 3px 1px rgba(20, 30, 70, .05);
  --md-elev2: 0 2px 6px rgba(20, 30, 70, .16), 0 8px 20px 2px rgba(20, 30, 70, .10);
  --family: Roboto, "Google Sans", "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif;
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
  --accent-4: #eaf0fc;
  --accent-5: #f3f6fd;
  --header-bg: var(--md-surface);
  --zebra: rgba(11, 87, 208, .04);
  --red1: var(--md-danger);
  --focus-color1: var(--md-primary);
  --focus-color2: transparent;
}
:root[data-ui-theme="dark"] {
  --md-primary: #a8c7fa;
  --md-on-primary: #062e6f;
  --md-primary-c: #0842a0;
  --md-on-primary-c: #d3e3fd;
  --md-accent: #a8c7fa;
  --md-on-accent: #062e6f;
  --md-accent-c: #0b3a82;
  --md-on-accent-c: #d3e3fd;
  --md-lav: #8ab4f8;
  --md-grad: var(--md-primary);
  --md-cta: var(--md-primary);
  --md-on-cta: #062e6f;
  --md-surface: #1f2227;
  --md-bg: #12141a;
  --md-surface-v: #2c3038;
  --md-outline: #8e9099;
  --md-outline-v: #3a3e47;
  --md-text: #e3e2e6;
  --md-text-2: #c4c6d0;
  --bg: var(--md-surface);
  --fg: var(--md-text);
  --md-danger: #f2b8b5;
  --md-hover: rgba(168, 199, 250, .09);
  --md-press: rgba(168, 199, 250, .16);
  --md-elev1: 0 1px 3px rgba(0, 0, 0, .55);
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
html input[type=checkbox]:not(.slider, .entry .style-name > input, #menu header input) {
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
html input[type=checkbox]:not(.slider, .entry .style-name > input, #menu header input)::after,
html input[type=checkbox]:not(.slider, .entry .style-name > input, #menu header input):checked::after {
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
html input[type=checkbox]:not(.slider, .entry .style-name > input, #menu header input):checked {
  background: var(--md-primary) !important;
  border-color: var(--md-primary) !important;
}
html input[type=checkbox]:not(.slider, .entry .style-name > input, #menu header input):checked::after { transform: rotate(45deg) scale(1); }
html input[type=checkbox]:not(.slider, .entry .style-name > input, #menu header input):hover:not(:disabled) { border-color: var(--md-primary) !important; }
html input[type=checkbox]:not(.slider, .entry .style-name > input, #menu header input):disabled { opacity: .45; cursor: default; }
html input[type=checkbox]:not(.slider, .entry .style-name > input, #menu header input) + span { color: inherit; }

/* ===== switch (M3 geometry, check icon in the thumb) ===== */
html input.slider,
html .entry .style-name > input[type=checkbox],
html #menu header input[type=checkbox] {
  --sw-h: 32px;
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  box-sizing: border-box;
  position: relative;
  display: inline-block;
  flex: 0 0 auto;
  width: calc(var(--sw-h) * 1.625) !important;
  height: var(--sw-h) !important;
  margin: 0 !important;
  vertical-align: middle;
  border: 2px solid var(--md-outline) !important;
  border-radius: calc(var(--sw-h) / 2) !important;
  background: var(--md-surface-v) !important;
  box-shadow: none !important;
  cursor: pointer;
  transition: background-color .2s, border-color .2s;
}
html input.slider::before,
html .entry .style-name > input[type=checkbox]::before,
html #menu header input[type=checkbox]::before { display: none !important; }
html input.slider::after,
html .entry .style-name > input[type=checkbox]::after,
html #menu header input[type=checkbox]::after {
  content: "" !important;
  position: absolute;
  top: 50%;
  left: calc(var(--sw-h) * .25 - 2px);
  width: calc(var(--sw-h) * .5) !important;
  height: calc(var(--sw-h) * .5) !important;
  margin: 0;
  border: 0;
  border-radius: 50%;
  background: var(--md-outline);
  box-shadow: none;
  transform: translateY(-50%);
  transition: left .2s, width .2s, height .2s, background-color .2s;
}
html input.slider:checked,
html .entry .style-name > input[type=checkbox]:checked,
html #menu header input[type=checkbox]:checked {
  background: var(--md-primary) !important;
  border-color: var(--md-primary) !important;
}
html input.slider:checked::after,
html .entry .style-name > input[type=checkbox]:checked::after,
html #menu header input[type=checkbox]:checked::after {
  left: calc(var(--sw-h) * .75 - 2px);
  width: calc(var(--sw-h) * .75) !important;
  height: calc(var(--sw-h) * .75) !important;
  background: url("@@CHECK_L@@") center / 64% no-repeat, var(--md-on-primary);
}
:root[data-ui-theme="dark"] input.slider:checked::after,
:root[data-ui-theme="dark"] .entry .style-name > input[type=checkbox]:checked::after,
:root[data-ui-theme="dark"] #menu header input[type=checkbox]:checked::after {
  background: url("@@CHECK_D@@") center / 64% no-repeat, var(--md-on-primary);
}
html input.slider:focus-visible,
html .entry .style-name > input[type=checkbox]:focus-visible,
html #menu header input[type=checkbox]:focus-visible {
  outline: 2px solid var(--md-primary);
  outline-offset: 2px;
}
html input.slider:disabled,
html .entry .style-name > input[type=checkbox]:disabled,
html #menu header input[type=checkbox]:disabled { opacity: .45; cursor: default; }
html .entry .style-name > input[type=checkbox],
html #menu header input[type=checkbox] { --sw-h: 26px; }

/* master switch: the checkbox is "disable all", so the switch reads inverted (on = Stylus active) */
html #disableAll#disableAll:not(:checked) { background: var(--md-primary) !important; border-color: var(--md-primary) !important; }
html #disableAll#disableAll:not(:checked)::after {
  left: calc(var(--sw-h) * .75 - 2px);
  width: calc(var(--sw-h) * .75) !important;
  height: calc(var(--sw-h) * .75) !important;
  background: url("@@CHECK_L@@") center / 64% no-repeat, var(--md-on-primary);
}
:root[data-ui-theme="dark"] #disableAll#disableAll:not(:checked)::after { background: url("@@CHECK_D@@") center / 64% no-repeat, var(--md-on-primary); }
html #disableAll#disableAll:checked { background: var(--md-surface-v) !important; border-color: var(--md-outline) !important; }
html #disableAll#disableAll:checked::after {
  left: calc(var(--sw-h) * .25 - 2px);
  width: calc(var(--sw-h) * .5) !important;
  height: calc(var(--sw-h) * .5) !important;
  background: var(--md-outline);
}

html #stylus-edit input.slider.slider { --sw-h: 28px; }

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

/* ===== options page (Gboard-style settings) ===== */
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
#stylus-options { background: var(--md-bg); color: var(--md-text); }
#stylus-options header {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 14px;
  box-sizing: border-box;
  min-height: 72px;
  padding: calc(12px + env(safe-area-inset-top, 0px)) 8px 8px 20px;
  border: 0;
  background: var(--md-bg) !important;
  box-shadow: none;
  color: var(--md-text);
}
#stylus-options header img { flex: 0 0 auto; width: 30px; height: 30px; border-radius: 8px; }
#stylus-options header h1 { flex: 1 1 auto; margin: 0; color: var(--md-text); font: 400 28px/1.2 var(--family); }
#stylus-options header i {
  flex: 0 0 auto;
  box-sizing: content-box;
  padding: 12px;
  border-radius: 50%;
  color: var(--md-text-2) !important;
  font-size: 24px;
  cursor: pointer;
}
#stylus-options header i:active { background: var(--md-press); }
#stylus-options main { box-sizing: border-box; padding: 0 12px 28px; background: var(--md-bg); }
#stylus-options .block {
  display: block;
  margin: 0 0 6px;
  padding: 0;
  overflow: visible;
  border: 0 !important;
  border-radius: 0;
  background: none;
  box-shadow: none;
}
#stylus-options .block > h2 {
  position: static;
  margin: 0;
  padding: 18px 16px 8px;
  border: 0;
  background: none;
  color: var(--md-primary);
  font: 500 14px/1.3 var(--family);
  letter-spacing: .01em;
  text-transform: none;
}
#stylus-options .block > h2::before { content: none; }
#stylus-options .block > :not(h2) {
  box-sizing: border-box;
  padding-left: 16px;
  padding-right: 16px;
  border-radius: 24px;
  background: var(--md-surface);
}
#stylus-options .block > :not(h2) { width: auto; }
#stylus-options .items { width: auto; padding-top: 4px; padding-bottom: 4px; }
#stylus-options .items > label,
#stylus-options .items .radio-wrapper { min-height: 56px; }
#stylus-options .items.swap > label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}
#stylus-options .items.swap > label > p:first-child {
  order: 0 !important;
  flex: 1 1 auto;
  margin: 0;
  color: var(--md-text);
  font-size: 16px;
  line-height: 1.3;
}
#stylus-options .items.swap > label > input,
#stylus-options .items.swap > label > input[type=number] {
  order: 1;
  flex: 0 0 auto;
  margin: 0 !important;
}
#stylus-options .items.swap > label > input[type=number] { width: 84px; text-align: center; }
#stylus-options .items.swap > label > input[type=color] { width: 56px; height: 36px; padding: 2px !important; }
#stylus-options input[type=number] { padding: 0 8px !important; }
#stylus-options .items > label + label { border-top: 1px solid var(--md-outline-v); }
#stylus-options .items label, #stylus-options .items .radio-wrapper { font-size: 16px; line-height: 1.3; }
#stylus-options label.radio-wrapper { align-items: center; justify-content: flex-start; flex-wrap: nowrap; row-gap: 2px; }
#stylus-options .radio-wrapper + span { margin-left: 8px; }
#stylus-options input[type=time] { width: 9.2em; min-width: 0; margin: 0 6px 0 0; padding: 0 8px !important; }
#stylus-options label.radio-wrapper:has(.md-time-range) { flex-wrap: wrap; }
#stylus-options .md-time-range {
  display: flex;
  flex: 1 0 calc(100% - 30px);
  align-items: center;
  gap: 10px;
  box-sizing: border-box;
  margin: 2px 0 12px 30px;
}
#stylus-options .md-time-range input[type=time] { flex: 1 1 0; width: auto; min-width: 0; margin: 0; }
#stylus-options .md-time-range .md-to { flex: 0 0 auto; color: var(--md-text-2); font-size: 13px; }
#stylus-options .sync-options > div { gap: 12px !important; padding-top: 12px; padding-bottom: 12px; }
#stylus-options .sync-options[data-enabled] .actions { display: flex; flex-wrap: wrap; gap: 8px; }
#stylus-options .drive-options input { height: var(--input-height); }
#stylus-options textarea { border-color: var(--md-outline) !important; }
#stylus-options #FOUC h2 { color: var(--md-danger); }
#stylus-options footer {
  display: flex;
  gap: 8px;
  height: auto;
  padding: 10px 16px calc(10px + env(safe-area-inset-bottom, 0px));
  border: 0 !important;
  background: var(--md-bg) !important;
  box-shadow: none;
}
#stylus-options footer button { flex: 1 1 0; min-width: 0; margin: 0 !important; padding: 0 8px !important; }
html #stylus-options footer #manage { background: var(--md-primary) !important; color: var(--md-on-primary) !important; }
html #stylus-options footer #reset { background: var(--md-primary-c) !important; color: var(--md-danger) !important; }
@media (max-width: 549px) {
  #stylus-options { width: 100%; border: 0; box-shadow: none; }
}

/* ===== manage page ===== */
#stylus-manage { background: var(--md-bg); color: var(--md-text); }
#stylus-manage #installed { background: transparent; }
#stylus-manage .select-wrapper { margin-left: 0; }
#stylus-manage .select-wrapper::after { top: 50%; right: 6px; margin: 0; }
#stylus-manage #wide-inputs .select-wrapper select { max-width: 100%; }
#stylus-manage .style-info[data-type=version] { color: var(--md-text-2); }
#stylus-manage .entry i { color: var(--md-text-2); }
#stylus-manage .entry.usercss .style-name-link::after {
  background: var(--md-primary-c);
  color: var(--md-on-primary-c);
  border-radius: 6px;
  padding: 2px 6px;
  font-weight: 500;
}

/* --- header = app bar + toolbar + search + chips --- */
.compact-layout #stylus-manage #header {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  width: 100% !important;
  height: auto;
  padding: 0;
  overflow: visible;
  z-index: 5;
  border: 0 !important;
  border-radius: 0 0 20px 20px;
  background: var(--md-surface) !important;
  box-shadow: var(--md-elev1);
}
.compact-layout #stylus-manage #header h1 {
  display: flex;
  visibility: visible;
  grid-column: 1;
  align-items: center;
  gap: 12px;
  margin: 0;
  padding: calc(12px + env(safe-area-inset-top, 0px)) 16px 8px;
  background: none;
  color: var(--md-text);
  font: 500 21px/1.2 var(--family);
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
.compact-layout #stylus-manage #header #disableAll-label {
  grid-column: 1 / -1;
  grid-row: 2;
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 4px 12px 4px;
  padding: 10px 14px;
  border-radius: 14px;
  background: color-mix(in srgb, var(--md-danger) 14%, var(--md-surface));
  color: var(--md-danger);
  font-weight: 500;
}
.compact-layout #stylus-manage #header #disableAll-label input { --sw-h: 26px; margin: 0; }
.compact-layout #stylus-manage #manage-settings {
  grid-column: 1 / -1;
  display: flex;
  flex-flow: column;
  align-items: stretch;
  gap: 10px;
  padding: 0 12px 14px;
}
.compact-layout #stylus-manage #actions { order: 1; display: block; }
.compact-layout #stylus-manage #wide-inputs { order: 2; gap: 8px; }
.compact-layout #stylus-manage #filters { order: 3; }
.compact-layout #stylus-manage #links { order: 4; }
.compact-layout #stylus-manage #backup-hint { order: 5; }
html:not(.all-disabled) #stylus-manage #disableAll-label:not([data-persist]) { display: none !important; }
.compact-layout #stylus-manage #wide-inputs > * { gap: 8px; }
.compact-layout #stylus-manage #header .filter-selection > label,
.compact-layout #stylus-manage #header label { background: none; }

/* toolbar: [+ New style] and round icon buttons, import/export below */
.compact-layout #stylus-manage #actions > details { display: none; }
.compact-layout #stylus-manage #actions main {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 2px;
  width: 100%;
  min-width: 0;
  margin: 0;
  box-sizing: border-box;
}
.compact-layout #stylus-manage #actions main > * { margin: 0; min-width: 0; }
html #stylus-manage #actions main button.icon,
html #stylus-manage #actions details + main button.icon {
  position: relative;
  box-sizing: border-box;
  width: 44px;
  min-width: 44px;
  height: 44px;
  padding: 0 !important;
  border-radius: 50% !important;
  background: transparent !important;
  color: var(--md-text-2) !important;
}
html #stylus-manage #actions main button.icon::before { content: none; }
html #stylus-manage #actions main button.icon:active { background: var(--md-press) !important; }
#stylus-manage #actions main button.icon > :is(i, svg) { position: static; margin: 0; font-size: 23px; color: var(--md-text-2) !important; }
#stylus-manage #check-all-updates { order: 1; }
#stylus-manage #update-history-button { order: 2; }
#stylus-manage #injection-order-button { order: 3; }
#stylus-manage #sync-styles { order: 4; }
#stylus-manage #manage-options-button { order: 5; }
#stylus-manage #update-progress { position: absolute; right: 2px; bottom: 2px; font-size: 10px; }
#stylus-manage #actions a#add-style {
  order: 0;
  display: inline-flex;
  margin: 0 8px 0 0;
}
html #stylus-manage #actions a#add-style > button.icon {
  width: auto !important;
  min-width: 0;
  height: 44px;
  padding: 0 20px 0 14px !important;
  gap: 8px;
  border-radius: 22px !important;
  background: var(--md-primary) !important;
  color: var(--md-on-primary) !important;
}
html #stylus-manage #actions a#add-style > button.icon::before {
  content: attr(title);
  order: 2;
  font: 500 14px/1 var(--family);
  white-space: nowrap;
}
#stylus-manage #actions a#add-style > button.icon > i { order: 1; font-size: 22px; color: var(--md-on-primary) !important; }
#stylus-manage #update-all { order: 6; flex: 1 0 100%; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 8px; }
#stylus-manage #update-all:empty { display: none; }
#stylus-manage #update-all > * { margin: 0; }
#stylus-manage #update-all-no-updates { color: var(--md-text-2); font-size: 13px; }
#stylus-manage #backup { order: 7; flex: 1 0 100%; display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 8px; }
#stylus-manage #backup > #sync-styles { order: -1; }
#stylus-manage #backup > button:not(.icon) { flex: 1 1 0; height: 40px; }
#stylus-manage #backup > .split-btn { flex: 1 1 0; display: flex; min-width: 0; }
#stylus-manage #backup > .split-btn > button:first-child { flex: 1 1 auto; }
#stylus-manage #backup > p { flex: 1 0 100%; margin: 0; }
#stylus-manage #backup > p:empty { display: none; }

/* search pill + selects */
#stylus-manage #search-wrapper { display: flex; align-items: center; gap: 8px; }
html #stylus-manage #search {
  flex: 1 1 auto;
  width: auto;
  min-width: 0;
  height: 46px;
  padding: 0 16px 0 46px !important;
  border: 0 !important;
  border-radius: 23px !important;
  background: var(--md-surface-v) url("@@SEARCH@@") no-repeat 15px center / 22px !important;
  color: var(--md-text);
  font-size: 15px;
}
html #stylus-manage #search:focus { box-shadow: 0 0 0 2px var(--md-primary) !important; }
html #stylus-manage #search::placeholder { color: var(--md-text-2); opacity: 1; }
:root[data-ui-theme="dark"] #stylus-manage #search { background-image: url("@@SEARCH_D@@") !important; }
html #stylus-manage #header select {
  height: 40px;
  padding: 0 30px 0 14px !important;
  border: 0 !important;
  border-radius: 20px !important;
  background: var(--md-primary-c) !important;
  color: var(--md-on-primary-c);
  font: 500 14px/1 var(--family);
}
#stylus-manage #search-wrapper .select-wrapper::after, #stylus-manage #sort-wrapper .select-wrapper::after { color: var(--md-on-primary-c); }
#stylus-manage #sort-wrapper { display: flex; align-items: center; gap: 8px; }
#stylus-manage #sort-wrapper .select-wrapper { flex: 1 1 auto; min-width: 0; }
#stylus-manage #sort-wrapper select { width: 100%; }

/* filters: scrolling chip row */
.compact-layout #stylus-manage #filters {
  display: flex;
  flex-wrap: nowrap;
  gap: 8px;
  margin: 0 -12px;
  padding: 2px 12px;
  overflow-x: auto;
  scrollbar-width: none;
}
.compact-layout #stylus-manage #filters::-webkit-scrollbar { display: none; }
.compact-layout #stylus-manage #filters > * { flex: 0 0 auto; }
.compact-layout #stylus-manage .filter-selection {
  left: 0;
  display: flex;
  align-items: center;
  gap: 0;
  min-width: 0;
  min-height: 0;
  height: 38px;
  padding: 0 2px 0 12px;
  border: 1px solid var(--md-outline-v);
  border-radius: 19px;
  background: transparent;
}
.compact-layout #stylus-manage .filter-selection[hidden] { display: none; }
.compact-layout #stylus-manage .filter-selection:has(input:checked) { border-color: transparent; background: var(--md-primary-c); }
.compact-layout #stylus-manage .filter-selection > label { margin: 0; padding: 0 !important; display: flex; align-items: center; }
.compact-layout #stylus-manage .filter-selection > label > input { margin: 0 !important; }
.compact-layout #stylus-manage .filter-selection > #only-updates > input { margin-right: 10px !important; }
.compact-layout #stylus-manage .filter-selection .select-wrapper { flex: 0 0 auto; min-width: 0; margin-left: 6px; }
html #stylus-manage #header .filter-selection select {
  width: auto;
  min-width: 0;
  height: 36px;
  padding: 0 28px 0 4px !important;
  background: transparent !important;
  color: var(--md-text);
  font: 400 14px/1 var(--family);
}
.compact-layout #stylus-manage .filter-selection:has(input:checked) select { color: var(--md-on-primary-c); }
#stylus-manage #stats {
  position: static;
  display: flex;
  align-items: center;
  gap: 4px;
  height: 38px;
  box-sizing: border-box;
  padding: 0 6px 0 14px;
  border-radius: 19px;
  background: var(--md-primary);
  color: var(--md-on-primary);
  font-size: 14px;
  font-weight: 500;
}
#stylus-manage #stats i { color: var(--md-on-primary); }

/* links / backup reminder */
.compact-layout:not(.empty) #stylus-manage #links summary::after { content: "Links"; }
.compact-layout #stylus-manage #backup-hint summary::after { content: "Backup reminder"; }
.compact-layout:not(.empty) #stylus-manage #links summary::after,
.compact-layout #stylus-manage #backup-hint summary::after {
  display: inline-block;
  padding: 8px 14px;
  border-radius: 16px;
  background: var(--md-surface-v);
  color: var(--md-text-2);
  font: 500 13px/1 var(--family);
}
.compact-layout #stylus-manage #links summary h2::after { content: none; }
.compact-layout #stylus-manage :is(#links, #backup-hint) details { gap: 8px; }
.compact-layout #stylus-manage #links main { gap: 4px 16px; }
.compact-layout.empty #stylus-manage #links { padding: 20px 4px 28px; font-size: 14px; line-height: 1.3; }
.compact-layout.empty #stylus-manage #links::before {
  content: "Get styles";
  display: block;
  margin: 0 4px 12px;
  color: var(--md-primary);
  font: 500 13px/1 var(--family);
  letter-spacing: .02em;
}
.compact-layout #stylus-manage #links main { display: flex; flex-flow: column; gap: 8px; }
.compact-layout #stylus-manage #links main a {
  display: flex;
  align-items: center;
  gap: 12px;
  box-sizing: border-box;
  width: 100%;
  min-height: 56px;
  padding: 8px;
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
  flex: 0 0 38px;
  height: 38px;
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
  padding: 9px;
  border-radius: 12px;
  background: var(--md-primary-c);
}
[data-ui-theme="dark"].compact-layout #stylus-manage #links main a::before {
  background: url("@@EXT_D@@") center / 20px no-repeat, var(--md-primary-c);
}
.compact-layout #stylus-manage #backup-hint main {
  padding: 12px 14px;
  border-radius: 14px;
  background: var(--md-surface-v);
  color: var(--md-text-2);
  font-size: 13px;
}

/* --- style cards --- */
.compact-layout #stylus-manage #installed { padding: 14px 12px 28px; flex-direction: column; flex-wrap: nowrap; gap: 10px; }
.compact-layout #stylus-manage .entry {
  display: grid !important;
  grid-template-columns: auto auto minmax(0, 1fr) auto;
  align-items: center;
  width: 100%;
  box-sizing: border-box;
  padding: 10px 6px 12px 14px !important;
  border: 0 !important;
  border-radius: 18px;
  background: var(--md-surface);
  box-shadow: var(--md-elev1);
  contain-intrinsic-block-size: auto 7em;
}
.compact-layout #stylus-manage .entry.odd { background: var(--md-surface); }
.compact-layout #stylus-manage .entry > * { margin: 0; padding: 0; min-width: 0; max-width: none; flex: none; }
.compact-layout #stylus-manage .entry > .style-name {
  grid-area: 1 / 1 / 2 / 4;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0;
  font-size: 15px;
  font-weight: 500;
}
.compact-layout #stylus-manage .entry .style-name input { margin: 0 !important; flex: 0 0 auto; }
.compact-layout #stylus-manage .entry .style-name-link { width: auto; flex: 1 1 auto; min-width: 0; color: var(--md-text); }
.compact-layout #stylus-manage .entry .homepage { flex: 0 0 auto; margin-left: 0; }
.compact-layout #stylus-manage .entry > .actions { grid-area: 1 / 4 / 2 / 5; justify-self: end; display: flex; align-items: center; }
.compact-layout #stylus-manage .entry > .style-info[data-type=size] {
  grid-area: 2 / 1 / 3 / 4;
  justify-self: start;
  padding: 0 0 0 54px;
  font-size: 12.5px;
  color: var(--md-text-2);
}
.compact-layout #stylus-manage .entry > .style-info[data-type=age] {
  grid-area: 2 / 1 / 3 / 4;
  justify-self: start;
  padding: 0 0 0 calc(54px + 5ch);
  font-size: 12.5px;
  color: var(--md-text-2);
}
.compact-layout #stylus-manage .entry > .applies-to {
  grid-area: 3 / 1 / 4 / 5;
  position: relative;
  padding: 10px 34px 0 0 !important;
}
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
  height: 28px;
  line-height: 28px;
  padding: 0 11px !important;
  border-radius: 8px;
  background: var(--md-bg);
  color: var(--md-text);
  font-size: 12.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.compact-layout.has-favicons #stylus-manage .entry .target { padding-left: 30px !important; }
.compact-layout #stylus-manage .entry .target img { position: absolute; left: 8px; top: 6px; width: 16px; height: 16px; margin: 0; }
.compact-layout #stylus-manage .entry .expander { position: absolute; right: 0; top: 6px; bottom: auto; width: 32px; height: 32px; justify-content: center; border-radius: 50%; }
.compact-layout #stylus-manage .entry .applies-to:not(.has-more) .expander { display: none; }
.compact-layout #stylus-manage .entry .actions > a,
.compact-layout #stylus-manage .entry .actions > span {
  width: 40px;
  height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}
.compact-layout #stylus-manage .entry .actions a:active { background: var(--md-press); }
.compact-layout #stylus-manage .entry .updater-icons { display: contents; }
.compact-layout #stylus-manage .entry .updater-icons > * { display: none; width: 40px; height: 40px; align-items: center; justify-content: center; }
.compact-layout #stylus-manage .entry .can-update .update,
.compact-layout #stylus-manage .entry.can-update .updater-icons .update,
.compact-layout #stylus-manage .entry.no-update:not(.update-problem):not(.update-done) .up-to-date,
.compact-layout #stylus-manage .entry.update-done .updated,
.compact-layout #stylus-manage .entry.updatable:not(.checking-update) .updater-icons .check-update { display: inline-flex; }
.compact-layout #stylus-manage .entry.updatable .updater-icons .update i { color: var(--md-primary); }
.compact-layout #stylus-manage .entry.disabled { box-shadow: none; background: color-mix(in srgb, var(--md-surface) 55%, var(--md-bg)); }
.compact-layout #stylus-manage .entry.disabled .style-name-link { color: var(--md-text-2); font-weight: 400; }
.compact-layout #stylus-manage .entry.disabled .target { background: var(--md-surface); }
.compact-layout #stylus-manage .entry .updater-icons .update-note { display: none; }
.compact-layout #stylus-manage .updater-icons > :not(.check-update)::after { max-width: 60vw; }

/* ===== manage v2: icon toolbar, one search row, filter popover ===== */
.compact-layout #stylus-manage #header h1 {
  grid-column: 1 / -1;
  justify-content: center;
  text-transform: capitalize;
  padding: calc(14px + env(safe-area-inset-top, 0px)) 16px 6px;
}
.compact-layout #stylus-manage #manage-settings {
  display: flex;
  flex-flow: row wrap;
  align-items: center;
  gap: 8px;
  padding: 4px 12px 14px;
}
.compact-layout #stylus-manage #wide-inputs,
.compact-layout #stylus-manage #filters { display: contents; }
.compact-layout #stylus-manage #actions { order: 1; flex: 1 0 100%; display: block; }
.compact-layout #stylus-manage #actions main { justify-content: space-between; gap: 0; }

/* toolbar: [+] update history order sync import export options */
#stylus-manage #backup { display: contents; }
html #stylus-manage #actions main button.icon,
html #stylus-manage #actions details + main button.icon {
  flex: 1 1 0;
  width: auto;
  min-width: 34px;
  max-width: 46px;
  height: 44px;
  border-radius: 22px !important;
}
html #stylus-manage #actions a#add-style > button.icon,
html #stylus-manage #actions details + main a#add-style > button.icon {
  flex: 0 0 44px;
  width: 44px !important;
  min-width: 44px;
  max-width: 44px;
  padding: 0 !important;
  border-radius: 50% !important;
}
html #stylus-manage #actions a#add-style > button.icon::before { content: none; }
#stylus-manage #actions a#add-style { order: 0; flex: 0 0 auto; margin: 0; }
#stylus-manage #check-all-updates { order: 1; }
#stylus-manage #update-history-button { order: 2; }
#stylus-manage #injection-order-button { order: 3; }
#stylus-manage #backup > #sync-styles { order: 4; }
#stylus-manage #backup > #import { order: 5; }
#stylus-manage #backup > .split-btn { order: 6; display: flex; flex: 1 1 0; min-width: 0; max-width: 62px; }
#stylus-manage #backup > .split-btn > button:first-child { flex: 1 1 0; max-width: none; }
#stylus-manage #backup > .split-btn > .split-btn-pedal {
  flex: 0 0 16px;
  width: 16px;
  min-width: 0;
  height: 44px;
  margin: 0 0 0 -8px;
  padding: 0 !important;
  border-radius: 0 22px 22px 0 !important;
  background: none !important;
  color: var(--md-outline) !important;
}
#stylus-manage #manage-options-button { order: 7; }
#stylus-manage #update-all { order: 8; flex: 1 0 100%; }
#stylus-manage #backup > p { order: 9; flex: 1 0 100%; margin: 0; }
#stylus-manage #backup > p:empty { display: none; }

/* search pill with the mode picker inside */
#stylus-manage #search-wrapper {
  order: 2;
  flex: 1 1 170px;
  min-width: 0;
  display: flex;
  align-items: center;
  box-sizing: border-box;
  height: 46px;
  padding: 0 4px 0 0;
  border-radius: 23px;
  background: var(--md-surface-v);
}
#stylus-manage #search-wrapper:focus-within { box-shadow: 0 0 0 2px var(--md-primary); }
html #stylus-manage #search-wrapper #search {
  flex: 1 1 auto;
  min-width: 0;
  height: 46px;
  padding: 0 4px 0 46px !important;
  border-radius: 23px 0 0 23px !important;
  background: transparent url("@@SEARCH@@") no-repeat 15px center / 22px !important;
  box-shadow: none !important;
}
:root[data-ui-theme="dark"] #stylus-manage #search-wrapper #search { background-image: url("@@SEARCH_D@@") !important; }
#stylus-manage #search-wrapper .select-wrapper { flex: 0 0 auto; }
html #stylus-manage #search-wrapper select {
  height: 36px;
  padding: 0 20px 0 6px !important;
  background: transparent !important;
  color: var(--md-primary);
  font: 500 13px/1 var(--family);
}
#stylus-manage #search-wrapper .select-wrapper::after { color: var(--md-primary); right: 2px; }
#stylus-manage #search-wrapper > a.icon { display: none; }

/* filter, help and sort are round icon buttons */
.compact-layout #stylus-manage #header :is(#md-filter-btn, #md-help-btn, #sort-wrapper) {
  flex: 0 0 46px;
  position: relative;
  display: grid;
  place-items: center;
  box-sizing: border-box;
  width: 46px;
  height: 46px;
  margin: 0;
  padding: 0;
  border-radius: 50%;
  background: var(--md-surface-v);
  cursor: pointer;
}
.compact-layout #stylus-manage #header #md-filter-btn { order: 3; }
.compact-layout #stylus-manage #header #sort-wrapper { order: 4; }
.compact-layout #stylus-manage #header #md-help-btn { order: 5; }
#stylus-manage #header :is(#md-filter-btn, #md-help-btn, #sort-wrapper) > i { font-size: 24px; color: var(--md-text-2); pointer-events: none; }
.compact-layout #stylus-manage #header :is(#md-filter-btn, #md-help-btn):has(input:checked) { background: var(--md-primary-c); }
#stylus-manage #header :is(#md-filter-btn, #md-help-btn):has(input:checked) > i { color: var(--md-on-primary-c); }
#stylus-manage #header:has(#filters input:checked) #md-filter-btn::after {
  content: "";
  position: absolute;
  top: 9px;
  right: 9px;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--md-primary);
  box-shadow: 0 0 0 2px var(--md-surface-v);
}
/* the native select sits invisibly on top of the sort icon and keeps its own picker */
#stylus-manage #sort-wrapper .select-wrapper { position: absolute; inset: 0; margin: 0; }
#stylus-manage #sort-wrapper .select-wrapper::after,
#stylus-manage #sort-wrapper > a.icon { display: none; }
html #stylus-manage #header #sort-wrapper select {
  position: absolute;
  inset: 0;
  width: 100%;
  min-width: 0;
  height: 100%;
  margin: 0;
  padding: 0 !important;
  border: 0 !important;
  border-radius: 50% !important;
  opacity: 0;
  cursor: pointer;
}
#stylus-manage #sort-wrapper select option { background: var(--md-surface); color: var(--md-text); }

/* filter chips live in a panel that opens from the filter button */
#stylus-manage #stats { order: 5; flex: 0 0 auto; }
.compact-layout #stylus-manage #filters .filter-selection { order: 6; flex: 1 1 100%; }
.compact-layout #stylus-manage #header:not(:has(#md-filter-toggle:checked)) #filters .filter-selection { display: none; }

/* links + backup reminder live behind the help button */
.compact-layout #stylus-manage #header :is(#links, #backup-hint) { display: none; }
.compact-layout #stylus-manage #header:has(#md-help-toggle:checked) :is(#links, #backup-hint) {
  display: block;
  flex: 1 1 100%;
  box-sizing: border-box;
  border-radius: 18px;
  background: var(--md-bg);
  overflow: hidden;
}
.compact-layout #stylus-manage #links { order: 8; }
.compact-layout #stylus-manage #backup-hint { order: 9; }
.compact-layout #stylus-manage #header :is(#links, #backup-hint) details { gap: 0; }
.compact-layout #stylus-manage #header :is(#links, #backup-hint) summary {
  display: flex;
  align-items: center;
  box-sizing: border-box;
  min-height: 50px;
  padding: 0 16px;
  list-style: none;
  cursor: pointer;
}
.compact-layout #stylus-manage #header :is(#links, #backup-hint) summary::-webkit-details-marker { display: none; }
.compact-layout #stylus-manage #header :is(#links, #backup-hint) summary::before {
  content: "";
  flex: 0 0 auto;
  width: 0;
  height: 0;
  margin-right: 14px;
  border: solid transparent;
  border-width: 5px 0 5px 7px;
  border-left-color: var(--md-text-2);
  transition: transform .15s;
}
.compact-layout #stylus-manage #header :is(#links, #backup-hint) details[open] > summary::before { transform: rotate(90deg); }
.compact-layout:not(.empty) #stylus-manage #header #links summary::after,
.compact-layout #stylus-manage #header #backup-hint summary::after {
  padding: 0;
  border-radius: 0;
  background: none;
  color: var(--md-text);
  font: 500 15px/1 var(--family);
}
.compact-layout #stylus-manage #header :is(#links, #backup-hint) details[open] > main { padding: 0 16px 14px; }
.compact-layout #stylus-manage #header #links main { display: flex; flex-flow: row wrap; gap: 8px; }
.compact-layout #stylus-manage #header #links main a {
  width: auto;
  min-height: 0;
  padding: 8px 14px;
  border-radius: 16px;
  background: var(--md-surface);
  box-shadow: none;
  font-size: 14px;
}
.compact-layout #stylus-manage #header #links main a::before,
.compact-layout #stylus-manage #header #links main a::after,
.compact-layout #stylus-manage #header #links main a > img { display: none; }
.compact-layout #stylus-manage #header #backup-hint main { padding: 0 16px 14px; background: none; border-radius: 0; }

/* no styles yet: a centred "Get styles" board instead of a long list */
.compact-layout.empty #stylus-manage #installed { padding: 0; min-height: 0; }
.compact-layout.empty #stylus-manage #links {
  flex: none;
  box-sizing: border-box;
  margin: 0;
  padding: 26px 16px 32px;
  line-height: 1.25;
}
.compact-layout.empty #stylus-manage #links::before {
  content: "Get styles";
  display: block;
  margin: 0 0 16px;
  color: var(--md-text);
  font: 500 20px/1.2 var(--family);
  text-align: center;
  letter-spacing: 0;
}
.compact-layout.empty #stylus-manage #links main {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.compact-layout.empty #stylus-manage #links main a {
  flex-direction: column;
  justify-content: center;
  gap: 10px;
  min-height: 108px;
  padding: 16px 10px 14px;
  border-radius: 22px;
  text-align: center;
  font-size: 14px;
}
.compact-layout.empty #stylus-manage #links main a::before { flex: 0 0 48px; width: 48px; height: 48px; border-radius: 16px; }
.compact-layout.empty #stylus-manage #links main a::after { display: none; }
.compact-layout.empty #stylus-manage #links main a:last-child:nth-child(odd) { grid-column: 1 / -1; }
.compact-layout.empty #stylus-manage #links main a.target > img { flex: 0 0 20px; margin: 0; padding: 14px; border-radius: 16px; }

#stylus-manage .entry .actions .delete:hover i { color: var(--md-danger); }

/* ===== popup: top bar, find row, list (Violentmonkey layout) ===== */
html.mobile:not(.sidebar) { width: 100% !important; }
html.mobile #stylus-popup { min-width: 100% !important; max-width: none !important; width: 100%; }
html.mobile body#stylus-popup {
  min-height: var(--100dvh, 100dvh);
  background: var(--md-bg);
  color: var(--md-text);
}
html.touch body#stylus-popup { --entry-h: 58px; --outer-padding: 16px; --inner-padding: 28px; --border: 1px solid var(--md-outline-v); }
#stylus-popup #pct { order: -20; }

/* top bar */
html body#stylus-popup #popup-options {
  order: -10;
  position: relative;
  z-index: 3;
  display: flex;
  flex: 0 0 auto;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-start;
  gap: 0;
  margin: 0;
  padding: calc(6px + env(safe-area-inset-top, 0px)) 8px 0 16px;
  border: 0;
  border-bottom: 1px solid var(--md-outline-v);
  background: var(--md-surface);
  box-shadow: none;
}
#stylus-popup #popup-options .md-brand {
  order: 0;
  display: flex;
  flex: 1 1 auto;
  align-items: center;
  gap: 12px;
  min-width: 0;
  padding: 6px 0;
  color: var(--md-text);
  font: 500 20px/1.2 var(--family);
}
#stylus-popup #popup-options .md-brand img { flex: 0 0 auto; width: 30px; height: 30px; border-radius: 8px; }
#stylus-popup #disableAll-label {
  order: 1;
  position: static;
  display: flex;
  align-items: center;
  margin: 0 6px 0 8px;
  padding: 0;
  border: 0;
  background: none;
}
#stylus-popup #disableAll-label img, #stylus-popup #disableAll-label::after { display: none !important; }
#stylus-popup #disableAll-label:hover { background: none; }
html #stylus-popup #disableAll { --sw-h: 28px; color: inherit; justify-content: center; }
html.all-disabled #stylus-popup #disableAll { border-color: var(--md-danger) !important; }
#stylus-popup #popup-options > .split-btn:has(#popup-manage-button) { order: 2; display: flex; align-items: center; position: relative; margin-right: -2px; }
#stylus-popup #popup-options > #help { order: 3; }
#stylus-popup #popup-options > #options-btn { order: 4; }
#stylus-popup #popup-options > #help,
#stylus-popup #popup-options > #options-btn,
#stylus-popup #popup-options #popup-manage-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  width: 44px;
  height: 44px;
  padding: 0;
  border-radius: 50%;
  color: var(--md-text-2);
}
#stylus-popup #popup-options .i-manage, #stylus-popup #popup-options .i-info, #stylus-popup #popup-options .i-config { font-size: 22px; color: var(--md-text-2); }
#stylus-popup #popup-options > a:active, #stylus-popup #popup-options #popup-manage-button:active { background: var(--md-press); }
#stylus-popup #popup-options > .split-btn:has(#popup-manage-button) > a.dropdown {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  width: 22px;
  height: 44px;
  margin-left: -8px;
  padding: 0;
  border-radius: 0 22px 22px 0;
}
#stylus-popup #popup-options a.dropdown i { font-size: 18px; color: var(--md-outline); }

/* find row */
html body#stylus-popup #popup-options > .split-btn:has(#find-styles-btn) {
  order: 10;
  position: relative;
  display: flex;
  align-items: stretch;
  flex: 0 0 calc(100% + 24px);
  box-sizing: border-box;
  margin: 4px -8px 0 -16px;
  border-top: 1px solid var(--md-outline-v);
}
#stylus-popup #find-styles-btn {
  display: flex;
  flex: 1 1 auto;
  align-items: center;
  justify-content: flex-start;
  gap: 16px;
  box-sizing: border-box;
  min-width: 0;
  height: 54px;
  padding: 0 16px;
  border-radius: 0;
  color: var(--md-text);
  font: 500 15px/1.2 var(--family);
  text-decoration: none;
}
#stylus-popup #find-styles-btn::after { content: attr(data-label); }
#stylus-popup #find-styles-btn i { flex: 0 0 auto; font-size: 22px; color: var(--md-primary); }
#stylus-popup #find-styles-btn:active, #stylus-popup #popup-options a.dropdown:active { background: var(--md-press); }
#stylus-popup #popup-options > .split-btn:has(#find-styles-btn) > a.dropdown {
  display: inline-flex;
  flex: 0 0 56px;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  height: auto;
  margin: 0;
  padding: 0;
  border-left: 1px solid var(--md-outline-v);
  border-radius: 0;
}

/* dropdown menus: open downwards, as a sheet */
html body#stylus-popup #popup-options .split-btn-menu {
  position: absolute;
  top: calc(100% + 4px);
  bottom: auto;
  left: auto;
  right: 8px;
  z-index: 1000;
  width: max-content;
  min-width: 200px;
  max-width: calc(100vw - 16px);
  padding: 6px;
  border: 0;
  border-radius: 16px;
  background: var(--md-surface);
  box-shadow: var(--md-elev2);
  transform: none;
}
html body#stylus-popup #popup-options > .split-btn:has(#find-styles-btn) .split-btn-menu { right: 8px; }
#stylus-popup #popup-options .split-btn-menu::before {
  display: block;
  padding: 10px 14px 6px;
  color: var(--md-primary);
  font: 500 12px/1 var(--family);
  letter-spacing: .04em;
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
  border-radius: 10px;
  background: none;
  box-shadow: none;
  color: var(--md-text);
  font: 400 15px/1 var(--family);
  text-decoration: none;
  white-space: nowrap;
}
#stylus-popup #popup-options .split-btn-menu > :is(:hover, :focus, :active) {
  background: var(--md-primary-c) !important;
  color: var(--md-on-primary-c);
}

/* notices */
#stylus-popup #unstylable,
#stylus-popup #no-styles {
  order: 1;
  margin: 12px 12px 0;
  padding: 16px;
  border: 0;
  border-radius: 16px;
  background: var(--md-surface);
  box-shadow: var(--md-elev1);
  color: var(--md-text-2);
  line-height: 1.4;
}
#stylus-popup #no-styles { padding: 22px 20px; text-align: center; cursor: pointer; }
#stylus-popup #no-styles:hover { color: var(--md-text-2); }
#stylus-popup #no-styles b { display: block; margin-top: 6px; color: var(--md-primary); font-weight: 500; }
#stylus-popup #unstylable a { color: var(--md-text-2); }

/* style list: "Styles for this site" */
html body#stylus-popup #installed {
  order: 2;
  flex: 0 0 auto;
  margin: 32px 12px 0;
  overflow: visible;
  border: 0 !important;
  border-radius: 16px;
  background: var(--md-surface);
  box-shadow: var(--md-elev1);
  position: relative;
}
#stylus-popup #installed:empty { display: none; }
#stylus-popup #installed::before {
  content: "Styles for this site";
  position: absolute;
  left: 4px;
  bottom: 100%;
  padding-bottom: 6px;
  color: var(--md-primary);
  font: 500 13px/1 var(--family);
  letter-spacing: .02em;
}
html.blocked #stylus-popup #installed::before { display: none; }
#stylus-popup #installed .entry { border-radius: 0; background: none; border: 0; }
#stylus-popup #installed .entry:first-child { border-radius: 16px 16px 0 0; }
#stylus-popup #installed .entry:last-child { border-radius: 0 0 16px 16px; }
#stylus-popup #installed .entry:only-child { border-radius: 16px; }
#stylus-popup #installed .entry + .entry { border-top: 1px solid var(--md-outline-v); }
#stylus-popup .entry-content { height: var(--entry-h); padding: 0 6px 0 14px; align-items: center; }
#stylus-popup .entry .main-controls { overflow: hidden; }
#stylus-popup .style-name {
  display: block;
  padding: 0;
  color: var(--md-text);
  font: 500 15px/var(--entry-h) var(--family);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
#stylus-popup .entry .style-name > input { margin: 0 14px 0 0 !important; }
#stylus-popup .entry.enabled .style-name { font-weight: 500; }
#stylus-popup .entry.disabled .style-name, #stylus-popup .entry.disabled .actions i { color: var(--md-text-2); }
#stylus-popup .entry.disabled .style-name { font-weight: 400; }
#stylus-popup .entry:hover :not(i), #stylus-popup .entry.disabled:hover *:not(i) { color: inherit; }
#stylus-popup .entry .actions { flex: 0 0 auto; }
#stylus-popup .entry .actions > :not([hidden]) {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  color: var(--md-text-2);
}
#stylus-popup .entry .actions > :hover { background: none; }
#stylus-popup .entry .actions > :active { background: var(--md-press); }
#stylus-popup .entry .actions i { font-size: 21px; color: var(--md-text-2); }
#stylus-popup .entry .actions .i-edit { color: var(--md-primary); }

/* toggle-all, write style */
html body#stylus-popup #toggler {
  order: 4;
  flex: 0 0 auto;
  margin: 12px 12px 0;
  border: 0;
  border-radius: 16px;
  background: var(--md-surface);
  box-shadow: var(--md-elev1);
}
#stylus-popup #toggler summary { padding: 0 16px; min-height: 52px; display: flex; align-items: center; color: var(--md-text); font-weight: 500; }
#stylus-popup #toggler details[open] { padding: 8px 8px 12px; }
#stylus-popup #toggler details[open] summary { padding-left: 8px; }
html body#stylus-popup #main-actions {
  order: 5;
  flex: 0 0 auto;
  margin: 12px 12px calc(16px + env(safe-area-inset-bottom, 0px));
  border: 0 !important;
  border-radius: 16px;
  background: var(--md-surface);
  box-shadow: var(--md-elev1);
  align-items: center;
}
#stylus-popup #write-wrapper { padding: 12px 16px; align-items: flex-start; gap: 12px; }
#stylus-popup #write-wrapper::after { display: none; }
#stylus-popup #write-wrapper > .icon {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  margin: 0;
  border-radius: 50%;
  background: var(--md-primary);
  color: var(--md-on-primary);
}
#stylus-popup #write-wrapper > .icon i { font-size: 22px; color: var(--md-on-primary); }
#stylus-popup #write-style { align-self: center; font-size: 14px; min-width: 0; }
#stylus-popup #write-style::before {
  content: "Write new style for";
  display: block;
  margin-bottom: 2px;
  color: var(--md-text-2);
  font: 400 12px/1.3 var(--family);
}
#stylus-popup #write-style .breadcrumbs { gap: 0; }
#stylus-popup .write-style-link { color: var(--md-primary); line-height: 1.7; }
#stylus-popup .write-style-link:last-child { color: var(--md-text-2); }
#stylus-popup .breadcrumbs:hover a { color: var(--md-primary); }
#stylus-popup #write-for-frames { color: var(--md-text-2); }

/* ----- popup: per-style menu (3 dots) ----- */
#stylus-popup #menu {
  box-sizing: border-box;
  padding-left: 16px;
  padding-right: 16px;
  background: rgba(0, 0, 0, .45);
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
  padding: 16px 20px !important;
  border-bottom: 0;
  background: var(--md-surface);
  color: var(--md-text);
  font-size: 16px;
  font-weight: 500;
}
#stylus-popup #menu.enabled header { background: var(--md-surface); color: var(--md-text); }
#stylus-popup #menu.delete header { background: var(--md-danger); color: #fff; }
#stylus-popup #menu.delete header i { color: #fff; }
#stylus-popup #menu header label { display: flex; align-items: center; gap: 14px; flex: 1 1 auto; min-width: 0; }
#stylus-popup #menu header a { margin-left: 0; }
#stylus-popup #menu header i { color: var(--md-text-2); font-size: 22px; }
#stylus-popup #menu [data-ovr]:not([hidden]) { min-height: 52px; font-size: 15px; }
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
  background: var(--md-bg);
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
html #stylus-popup #menu footer [data-cmd=cancel] { order: 1; background: transparent !important; color: var(--md-primary) !important; }
html #stylus-popup #menu footer [data-cmd=edit] { order: 2; background: var(--md-primary) !important; color: var(--md-on-primary) !important; }
html #stylus-popup #menu footer [data-cmd=delete] {
  order: 0;
  margin-right: auto;
  background: transparent !important;
  color: var(--md-danger) !important;
}
html #stylus-popup #menu.delete footer [data-cmd=delete] { background: var(--md-danger) !important; color: #fff !important; }

/* ===== popup v2: manage pill, toggle-all card, search progress + results ===== */
/* manage keeps its caret as the second half of the pill */
html body#stylus-popup #popup-options > .split-btn:has(#popup-manage-button) { margin-right: 2px; }
html body#stylus-popup #popup-options > .split-btn:has(#popup-manage-button) > #popup-manage-button { border-radius: 20px 0 0 20px; padding-right: 12px; }
html body#stylus-popup #popup-options > .split-btn:has(#popup-manage-button) > a.dropdown {
  width: 30px;
  height: 40px;
  margin: 0 0 0 2px;
  border-radius: 0 20px 20px 0;
  background: var(--md-primary-c);
}
#stylus-popup #popup-options > .split-btn:has(#popup-manage-button) > a.dropdown i { color: var(--md-on-primary-c); }
/* both dropdowns open as a sheet aligned to the screen margins, right under the bar */
html body#stylus-popup #popup-options > .split-btn { position: static; }
html body#stylus-popup #popup-options .split-btn-menu,
html body#stylus-popup #popup-options > .split-btn:has(#find-styles-btn) .split-btn-menu {
  top: calc(100% + 6px);
  left: 12px;
  right: 12px;
  width: auto;
  min-width: 0;
  max-width: none;
}
html body#stylus-popup #popup-options #popup-manage-button {
  width: auto;
  height: 40px;
  padding: 0 16px 0 12px;
  gap: 8px;
  border-radius: 20px;
  background: var(--md-primary-c);
  color: var(--md-on-primary-c);
  font: 500 14px/1 var(--family);
}
#stylus-popup #popup-manage-button::after { content: attr(data-label); }
#stylus-popup #popup-options #popup-manage-button i { font-size: 20px; color: var(--md-on-primary-c); }
#stylus-popup #popup-options .i-m-cog { font-size: 22px; color: var(--md-text-2); }
#stylus-popup .entry .actions .i-m-tune { font-size: 21px; }
#stylus-popup .entry .actions .i-m-edit { font-size: 21px; color: var(--md-primary); }
#stylus-popup .entry.disabled .actions .i-m-edit { color: var(--md-text-2); }
@media (max-width: 399px) { #stylus-popup #popup-options .md-brand span { display: none; } }

/* toggle-all card (upstream turns the open summary into an invisible overlay; keep it as the first row) */
html body#stylus-popup #toggler details[open] > summary {
  position: static;
  width: auto;
  height: auto;
  color: var(--md-text);
  cursor: pointer;
}
html body#stylus-popup #toggler details[open] { padding: 0; position: static; }
html body#stylus-popup #toggler { padding: 0 !important; }
html body#stylus-popup #toggler details > div { display: flex; margin: 0; position: relative; }
html body#stylus-popup #toggler { display: block; position: relative; padding: 0; overflow: hidden; }
#stylus-popup #toggler details { padding: 0; }
#stylus-popup #toggler summary {
  display: flex;
  align-items: center;
  box-sizing: border-box;
  min-height: 52px;
  padding: 0 52px 0 16px;
  list-style: none;
  color: var(--md-text);
  font-weight: 500;
  cursor: pointer;
}
#stylus-popup #toggler summary::-webkit-details-marker { display: none; }
#stylus-popup #toggler summary::before {
  content: "";
  flex: 0 0 auto;
  width: 0;
  height: 0;
  margin: 0 12px 0 2px;
  border: solid transparent;
  border-width: 5px 0 5px 7px;
  border-left-color: var(--md-text-2);
  transition: transform .15s;
}
#stylus-popup #toggler details[open] > summary::before { transform: rotate(90deg); }
#stylus-popup #toggler details > div {
  display: flex;
  align-items: center;
  gap: 8px;
  box-sizing: border-box;
  min-height: 54px;
  padding: 6px 16px;
  border-top: 1px solid var(--md-outline-v);
}
#stylus-popup #toggler details > div > label {
  order: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1 1 auto;
  min-width: 0;
  margin: 0;
  color: var(--md-text);
  font-size: 14px;
  text-transform: capitalize;
}
#stylus-popup #toggler details > .icon {
  position: absolute;
  top: 6px;
  right: 8px;
  bottom: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  margin: 0;
  border-radius: 50%;
}
#stylus-popup #toggler details > .icon i { font-size: 20px; color: var(--md-outline); }
#stylus-popup #toggler details > .icon:has(input:checked) i { color: var(--md-primary); }
/* enable / disable become labelled chips */
html #stylus-popup #toggler input[data-toggle^="+"],
html #stylus-popup #toggler input[data-toggle^="-"] {
  -moz-appearance: none;
  appearance: none;
  order: 2;
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  width: auto !important;
  min-width: 78px;
  height: 36px !important;
  margin: 0 !important;
  padding: 0 14px;
  border: 1px solid var(--md-outline) !important;
  border-radius: 18px !important;
  background: transparent !important;
  box-shadow: none !important;
  cursor: pointer;
}
html #stylus-popup #toggler input[data-toggle^="+"] { order: 1; }
html #stylus-popup #toggler input[data-toggle^="+"]::before,
html #stylus-popup #toggler input[data-toggle^="-"]::before { display: none !important; }
html #stylus-popup #toggler input[data-toggle^="+"]::after,
html #stylus-popup #toggler input[data-toggle^="-"]::after {
  content: attr(title) !important;
  position: static;
  width: auto !important;
  height: auto !important;
  margin: 0;
  border: 0;
  background: none !important;
  box-shadow: none;
  transform: none;
  color: var(--md-text);
  font: 500 13px/1 var(--family);
  -webkit-mask: none;
  mask: none;
  opacity: 1;
}
html #stylus-popup #toggler input[data-toggle^="+"]:checked,
html #stylus-popup #toggler input[data-toggle^="-"]:checked {
  border-color: transparent !important;
  background: var(--md-primary-c) !important;
}
html #stylus-popup #toggler input[data-toggle^="+"]:checked::after,
html #stylus-popup #toggler input[data-toggle^="-"]:checked::after { color: var(--md-on-primary-c); }

/* find: progress strip right under the bar, results next */
html body#stylus-popup #pct {
  order: -9;
  position: relative;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-start;
  gap: 2px 14px;
  box-sizing: border-box;
  margin: 0 !important;
  padding: 0 16px;
  overflow: hidden;
  background: var(--md-surface);
  border-bottom: 1px solid var(--md-outline-v);
  color: var(--md-primary);
  font: 500 13px/1 var(--family);
}
#stylus-popup #pct > * { padding: 14px 0 12px; }
#stylus-popup #pct::after {
  content: "";
  position: absolute;
  left: 0;
  bottom: 0;
  width: 35%;
  height: 3px;
  border-radius: 2px;
  background: var(--md-primary);
  animation: md-indet 1.2s ease-in-out infinite;
}
#stylus-popup #pct:not(:has(> :not([style*="opacity: 0"]))) { display: none; }
html.search-results-shown #stylus-popup #pct { display: none; }
@keyframes md-indet { 0% { left: -35%; } 100% { left: 100%; } }
html body#stylus-popup #search-results-error {
  order: -8;
  margin: 12px 12px 0;
  padding: 14px 16px;
  border-radius: 16px;
  background: var(--md-danger);
  color: #fff;
}
html body#stylus-popup #search-results {
  order: -8;
  margin: 12px 12px 0;
  padding: 0;
  border: 0;
  background: none;
}
#stylus-popup #search-params { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; padding: 4px 0 12px; }
#stylus-popup #search-params #search-query { flex: 1 1 140px; min-width: 0; border-radius: 20px; }
#stylus-popup .search-results-nav { margin: 0 0 8px; background: none; border: 0 !important; }
#stylus-popup #search-results-list { min-height: 0; }
#stylus-popup .search-result {
  border: 0;
  border-radius: 16px;
  background: var(--md-surface);
  box-shadow: var(--md-elev1);
  overflow: hidden;
}
#stylus-popup .search-result:hover { background: var(--md-surface); }
#stylus-popup .search-result[data-installed] { box-shadow: 0 0 0 2px var(--md-primary); }
#stylus-popup .search-result-title { color: var(--md-text); }
#stylus-popup .search-result-screenshot { border-radius: 10px; }
#stylus-popup .search-result-status { background-color: color-mix(in srgb, var(--md-primary) 82%, transparent); color: var(--md-on-primary); border-radius: 10px 10px 0 0; }
#stylus-popup .search-result-actions button { box-shadow: var(--md-elev2); }
#stylus-popup .search-result-meta::before { background: var(--md-surface); }
#stylus-popup .search-result:hover .search-result-meta::before { background: var(--md-surface); }
#stylus-popup .not-matching-explainer { border: 0; border-radius: 10px; background: var(--md-primary-c); color: var(--md-on-primary-c); }


/* top bar: brand yields first so the caret + icons never wrap */
html body#stylus-popup #popup-options .md-brand { flex: 1 1 0; gap: 10px; font-size: 18px; overflow: hidden; }
html body#stylus-popup #popup-options .md-brand span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
html body#stylus-popup #popup-options > #help,
html body#stylus-popup #popup-options > #options-btn { width: 40px; height: 40px; }
html body#stylus-popup #disableAll-label { margin: 0 4px 0 6px; }
/* ===== install-usercss ===== */
#stylus-install-usercss { background: var(--md-bg); }
#stylus-install-usercss #header { background: var(--md-surface) !important; box-shadow: var(--md-elev1); }

/* ===== embedded dialogs / config ===== */
.config-dialog #message-box-contents { padding-top: 4px; }

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

/* ===== dialogs: title never clipped, injection order in the same palette ===== */
html #message-box-title:not(:empty) {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  box-sizing: border-box;
  min-height: 60px;
  line-height: 1.25;
}
#message-box:not(.injection-order) #message-box-contents { flex: 1 1 auto; min-height: 0; overflow-y: auto; }
#message-box-buttons { flex: 0 0 auto; }
.injection-order > div { max-width: 92vw; }
.injection-order header { background: none; color: var(--md-text-2); font-size: 14px; line-height: 1.45; }
.injection-order [data-prio] header { background-color: var(--md-primary-c) !important; color: var(--md-on-primary-c); }
.injection-order .draggable-list-target { background: var(--md-primary-c); }
.injection-order-entry { color: var(--md-text); }
.injection-order-entry a, .injection-order-entry a[href] { color: inherit; }
.injection-order-entry.enabled a[href] { font-weight: 500; }
.injection-order-toggle::after { color: var(--md-outline); }
[data-prio] .injection-order-toggle::after, .injection-order-toggle:hover::after { color: var(--md-primary); }
.injection-order [data-prio] header,
.injection-order :is(ol, #message-box-buttons),
.injection-order-entry:nth-child(n + 2) { border-top-color: var(--md-outline-v); }

/* ===== v3 fixes ===== */
/* manage: help panel. Upstream makes every header <details> a flex row (summary beside content); stack them */
.compact-layout #stylus-manage #header :is(#links, #backup-hint) details {
  display: block;
  gap: 0;
  margin: 0;
}
.compact-layout #stylus-manage #header :is(#links, #backup-hint) summary { margin: 0; }
.compact-layout #stylus-manage #header :is(#links, #backup-hint) summary::after {
  white-space: nowrap;
  hyphens: none;
  -webkit-hyphens: none;
}
.compact-layout #stylus-manage #header #backup-hint main {
  min-width: 0;
  max-height: none;
  overflow: visible;
  hyphens: manual;
  -webkit-hyphens: manual;
  line-height: 1.45;
}
/* manage: switch sits a touch lower so it centres on the title text */
.compact-layout #stylus-manage .entry .style-name > input[type=checkbox] { top: 2px; }

/* popup: the Manage menu opened inside the narrow pill, so it was ~100px wide and its text overflowed */
html body#stylus-popup #popup-options > .split-btn:has(#popup-manage-button) > .split-btn-menu {
  left: auto;
  right: 0;
  width: max-content;
  min-width: 232px;
  max-width: calc(100vw - 24px);
}

/* editor toolbar: Styles / Homepage / UserCSS glyphs match the other icons; Homepage lines up with the first column */
.compact-layout #stylus-edit #header #cancel-button::after,
.compact-layout #stylus-edit #header #url > i { transform: scale(1.18); }
.compact-layout #stylus-edit #header #usercss-docs::before { mask-size: 84%; -webkit-mask-size: 84%; }
.compact-layout #stylus-edit #header #url {
  flex: 0 0 56px;
  width: 56px;
  max-width: 56px;
  margin: 0;
}

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
    'm-dashboard': ('\u2460', 'M19,5V7H15V5H19M9,5V11H5V5H9M19,13V19H15V13H19M9,17V19H5V17H9M21,3H13V9H21V3M11,3H3V13H11V3M21,11H13V21H21V11M11,15H3V21H11V15Z'),
    'm-update': ('\u2461', 'M12,18A6,6 0 0,1 6,12C6,11 6.25,10.03 6.7,9.2L5.24,7.74C4.46,8.97 4,10.43 4,12A8,8 0 0,0 12,20V23L16,19L12,15M12,4V1L8,5L12,9V6A6,6 0 0,1 18,12C18,13 17.75,13.97 17.3,14.8L18.76,16.26C19.54,15.03 20,13.57 20,12A8,8 0 0,0 12,4Z'),
    'm-install': ('\u2462', 'M8 17V15H16V17H8M16 10L12 14L8 10H10.5V6H13.5V10H16M12 2C17.5 2 22 6.5 22 12C22 17.5 17.5 22 12 22C6.5 22 2 17.5 2 12C2 6.5 6.5 2 12 2M12 4C7.58 4 4 7.58 4 12C4 16.42 7.58 20 12 20C16.42 20 20 16.42 20 12C20 7.58 16.42 4 12 4Z'),
    'm-order': ('\u2463', 'M7,13V11H21V13H7M7,19V17H21V19H7M7,7V5H21V7H7M3,8V5H2V4H4V8H3M2,17V16H5V20H2V19H4V18.5H3V17.5H4V17H2M4.25,10A0.75,0.75 0 0,1 5,10.75C5,10.95 4.92,11.14 4.79,11.27L3.12,13H5V14H2V13.08L4,11H2V10H4.25Z'),
    'm-sync': ('\u2464', 'M13.03 18C13.08 18.7 13.24 19.38 13.5 20H6.5C5 20 3.69 19.5 2.61 18.43C1.54 17.38 1 16.09 1 14.58C1 13.28 1.39 12.12 2.17 11.1S4 9.43 5.25 9.15C5.67 7.62 6.5 6.38 7.75 5.43S10.42 4 12 4C13.95 4 15.6 4.68 16.96 6.04C18.32 7.4 19 9.05 19 11C19.04 11 19.07 11 19.1 11C18.36 11.07 17.65 11.23 17 11.5V11C17 9.62 16.5 8.44 15.54 7.46C14.56 6.5 13.38 6 12 6S9.44 6.5 8.46 7.46C7.5 8.44 7 9.62 7 11H6.5C5.53 11 4.71 11.34 4.03 12.03C3.34 12.71 3 13.53 3 14.5S3.34 16.29 4.03 17C4.71 17.66 5.53 18 6.5 18H13.03M19 13.5V12L16.75 14.25L19 16.5V15C20.38 15 21.5 16.12 21.5 17.5C21.5 17.9 21.41 18.28 21.24 18.62L22.33 19.71C22.75 19.08 23 18.32 23 17.5C23 15.29 21.21 13.5 19 13.5M19 20C17.62 20 16.5 18.88 16.5 17.5C16.5 17.1 16.59 16.72 16.76 16.38L15.67 15.29C15.25 15.92 15 16.68 15 17.5C15 19.71 16.79 21.5 19 21.5V23L21.25 20.75L19 18.5V20Z'),
    'm-import': ('\u2465', 'M2 12H4V17H20V12H22V17C22 18.11 21.11 19 20 19H4C2.9 19 2 18.11 2 17V12M12 15L17.55 9.54L16.13 8.13L13 11.25V2H11V11.25L7.88 8.13L6.46 9.55L12 15Z'),
    'm-export': ('\u2466', 'M2 12H4V17H20V12H22V17C22 18.11 21.11 19 20 19H4C2.9 19 2 18.11 2 17V12M12 2L6.46 7.46L7.88 8.88L11 5.75V15H13V5.75L16.13 8.88L17.55 7.45L12 2Z'),
    'm-sort': ('\u2467', 'M20 17H23L19 21L15 17H18V3H20V17M8 5C4.14 5 1 8.13 1 12C1 15.87 4.13 19 8 19C11.86 19 15 15.87 15 12C15 8.13 11.87 5 8 5M8 7.15C10.67 7.15 12.85 9.32 12.85 12C12.85 14.68 10.68 16.85 8 16.85C5.32 16.85 3.15 14.68 3.15 12C3.15 9.32 5.32 7.15 8 7.15M7 9V12.69L10.19 14.53L10.94 13.23L8.5 11.82V9'),
    'm-filter': ('\u2468', 'M15,19.88C15.04,20.18 14.94,20.5 14.71,20.71C14.32,21.1 13.69,21.1 13.3,20.71L9.29,16.7C9.06,16.47 8.96,16.16 9,15.87V10.75L4.21,4.62C3.87,4.19 3.95,3.56 4.38,3.22C4.57,3.08 4.78,3 5,3V3H19V3C19.22,3 19.43,3.08 19.62,3.22C20.05,3.56 20.13,4.19 19.79,4.62L15,10.75V19.88M7.04,5L11,10.06V15.58L13,17.58V10.05L16.96,5H7.04Z'),
    'm-trash': ('\u2469', 'M9,3V4H4V6H5V19A2,2 0 0,0 7,21H17A2,2 0 0,0 19,19V6H20V4H15V3H9M7,6H17V19H7V6M9,8V17H11V8H9M13,8V17H15V8H13Z'),
    'm-home': ('\u246a', 'M12 5.69L17 10.19V18H15V12H9V18H7V10.19L12 5.69M12 3L2 12H5V20H11V14H13V20H19V12H22'),
    'm-tune': ('\u246b', 'M8 13C6.14 13 4.59 14.28 4.14 16H2V18H4.14C4.59 19.72 6.14 21 8 21S11.41 19.72 11.86 18H22V16H11.86C11.41 14.28 9.86 13 8 13M8 19C6.9 19 6 18.1 6 17C6 15.9 6.9 15 8 15S10 15.9 10 17C10 18.1 9.1 19 8 19M19.86 6C19.41 4.28 17.86 3 16 3S12.59 4.28 12.14 6H2V8H12.14C12.59 9.72 14.14 11 16 11S19.41 9.72 19.86 8H22V6H19.86M16 9C14.9 9 14 8.1 14 7C14 5.9 14.9 5 16 5S18 5.9 18 7C18 8.1 17.1 9 16 9Z'),
    'm-cog': ('\u246c', 'M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8M12,10A2,2 0 0,0 10,12A2,2 0 0,0 12,14A2,2 0 0,0 14,12A2,2 0 0,0 12,10M10,22C9.75,22 9.54,21.82 9.5,21.58L9.13,18.93C8.5,18.68 7.96,18.34 7.44,17.94L4.95,18.95C4.73,19.03 4.46,18.95 4.34,18.73L2.34,15.27C2.21,15.05 2.27,14.78 2.46,14.63L4.57,12.97L4.5,12L4.57,11L2.46,9.37C2.27,9.22 2.21,8.95 2.34,8.73L4.34,5.27C4.46,5.05 4.73,4.96 4.95,5.05L7.44,6.05C7.96,5.66 8.5,5.32 9.13,5.07L9.5,2.42C9.54,2.18 9.75,2 10,2H14C14.25,2 14.46,2.18 14.5,2.42L14.87,5.07C15.5,5.32 16.04,5.66 16.56,6.05L19.05,5.05C19.27,4.96 19.54,5.05 19.66,5.27L21.66,8.73C21.79,8.95 21.73,9.22 21.54,9.37L19.43,11L19.5,12L19.43,13L21.54,14.63C21.73,14.78 21.79,15.05 21.66,15.27L19.66,18.73C19.54,18.95 19.27,19.04 19.05,18.95L16.56,17.95C16.04,18.34 15.5,18.68 14.87,18.93L14.5,21.58C14.46,21.82 14.25,22 14,22H10M11.25,4L10.88,6.61C9.68,6.86 8.62,7.5 7.85,8.39L5.44,7.35L4.69,8.65L6.8,10.2C6.4,11.37 6.4,12.64 6.8,13.8L4.68,15.36L5.43,16.66L7.86,15.62C8.63,16.5 9.68,17.14 10.87,17.38L11.24,20H12.76L13.13,17.39C14.32,17.14 15.37,16.5 16.14,15.62L18.57,16.66L19.32,15.36L17.2,13.81C17.6,12.64 17.6,11.37 17.2,10.2L19.31,8.65L18.56,7.35L16.15,8.39C15.38,7.5 14.32,6.86 13.12,6.62L12.75,4H11.25Z'),
    'm-history': ('\u246d', 'M13.5,8H12V13L16.28,15.54L17,14.33L13.5,12.25V8M13,3A9,9 0 0,0 4,12H1L4.96,16.03L9,12H6A7,7 0 0,1 13,5A7,7 0 0,1 20,12A7,7 0 0,1 13,19C11.07,19 9.32,18.21 8.06,16.94L6.64,18.36C8.27,20 10.5,21 13,21A9,9 0 0,0 22,12A9,9 0 0,0 13,3'),
    'm-edit': ('\u246e', 'M14.06,9L15,9.94L5.92,19H5V18.08L14.06,9M17.66,3C17.41,3 17.15,3.1 16.96,3.29L15.13,5.12L18.88,8.87L20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18.17,3.09 17.92,3 17.66,3M14.06,6.19L3,17.25V21H6.75L17.81,9.94L14.06,6.19Z'),
    'm-help': ('\u246f', 'M11,18H13V16H11V18M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,6A4,4 0 0,0 8,10H10A2,2 0 0,1 12,8A2,2 0 0,1 14,10C14,12 11,11.75 11,15H13C13,12.75 16,12.5 16,10A4,4 0 0,0 12,6Z'),
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
            .replace('@@EXT_P@@', svg_uri(ICONS['external'], '#0b57d0'))
            .replace('@@EXT_D@@', svg_uri(ICONS['external'], '#a8c7fa'))
            .replace('@@CHEV@@', svg_uri(EXTRA_PATHS['chev'], '#747780'))
            .replace('@@CHECK_L@@', svg_uri(ICONS['check1'], '#0b57d0'))
            .replace('@@CHECK_D@@', svg_uri(ICONS['check1'], '#a8c7fa'))
            .replace('@@SEARCH@@', svg_uri(ICONS['search'], '#4a4e59'))
            .replace('@@SEARCH_D@@', svg_uri(ICONS['search'], '#c4c6d0'))
            .replace('@@SORT@@', svg_uri(ICONS['m-sort'][1], '#4a4e59'))
            .replace('@@SORT_D@@', svg_uri(ICONS['m-sort'][1], '#c4c6d0')))


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
        ('<a id="find-styles-btn" ', '<a id="find-styles-btn" data-label="Find styles for this site" '),
    ]:
        P.edit('src/popup.html', old, new, marker=re.search(r'data-label="[^"]+"', new).group(0))
    P.edit('src/popup.html', '<div id="popup-options">\n',
           '<div id="popup-options">\n'
           '    <div class="md-brand"><img srcset="icon/32.png, icon/48.png 2x" width="30" height="30" alt="">'
           '<span>Stylus</span></div>\n', marker='class="md-brand"')
    P.edit('src/options.html',
           r'(<input type="time" required id="schemeSwitcher\.nightStart">)\s*~\s*'
           r'(<input type="time" required id="schemeSwitcher\.nightEnd">)',
           r'<span class="md-time-range">\1<span class="md-to">to</span>\2</span>',
           marker='md-time-range', regex=True)
    for rel in ('src/manage.html', 'src/popup.html'):
        P.edit(rel, r'<svg class="hollow-gear"[^>]*>\s*<text[^>]*>\u2699</text>\s*</svg>',
               '<i class="i-config"></i>', regex=True, count=0, optional=True)

    print('== icons: clearer glyphs for popup + manager')
    for rel, old, new, mk in [
        ('src/popup.html', '<a id="popup-manage-button" ', '<a id="popup-manage-button" data-label="Manage" ', 'data-label="Manage"'),
        ('src/popup.html', '<i class="i-manage"></i>', '<i class="i-m-dashboard"></i>', 'i-m-dashboard'),
        ('src/popup.html', '<a class="configure" tabindex="0">\n            <i class="i-config"></i>',
         '<a class="configure" tabindex="0">\n            <i class="i-m-tune"></i>', 'i-m-tune'),
        ('src/popup.html', '<i class=i-edit></i>', '<i class=i-m-edit></i>', 'i-m-edit'),
        ('src/popup.html', '<a id="options-btn" i18n="title:openOptions" tabindex="0">\n      <i class="i-config"></i>',
         '<a id="options-btn" i18n="title:openOptions" tabindex="0">\n      <i class="i-m-cog"></i>', 'i-m-cog'),
        ('src/manage.html', '<i class=i-update-check></i>', '<i class=i-m-update></i>', 'i-m-update'),
        ('src/manage.html', '<i class=i-install></i>', '<i class=i-m-install></i>', 'i-m-install'),
        ('src/manage.html', '<i class=i-log></i>', '<i class=i-m-history></i>', 'i-m-history'),
        ('src/manage.html', '<i class=i-reorder></i>', '<i class=i-m-order></i>', 'i-m-order'),
        ('src/manage.html', '<i class=i-cloud></i>', '<i class=i-m-sync></i>', 'i-m-sync'),
        ('src/manage.html', '<a class="configure-usercss" i18n="title:configureStyle" tabindex="0">\n      <i class=i-config></i>',
         '<a class="configure-usercss" i18n="title:configureStyle" tabindex="0">\n      <i class=i-m-tune></i>', 'i-m-tune'),
        ('src/manage.html', '<i class="i-config"></i>', '<i class="i-m-cog"></i>', 'i-m-cog'),
        ('src/manage.html', '<i class=i-external></i>', '<i class=i-m-home></i>', 'i-m-home'),
        ('src/manage.html', '<a class="delete" i18n="title:deleteStyleLabel" tabindex="0">\n          <i class=i-close></i>',
         '<a class="delete" i18n="title:deleteStyleLabel" tabindex="0">\n          <i class=i-m-trash></i>', 'i-m-trash'),
        ('src/manage.html', '<button id="import" i18n="importLabel"></button>',
         '<button id="import" class="icon" i18n="title:importLabel"><i class=i-m-import></i></button>', 'i-m-import'),
        ('src/manage.html', '<button id="export" i18n="exportLabel"></button',
         '<button id="export" class="icon" i18n="title:exportLabel"><i class=i-m-export></i></button', 'i-m-export'),
        ('src/manage.html', '      <div id="sort-wrapper">',
         '      <label id="md-filter-btn" title="Filters"><input type="checkbox" id="md-filter-toggle" hidden>'
         '<i class=i-m-filter></i></label>\n\n'
         '      <label id="md-help-btn" title="Links and backup"><input type="checkbox" id="md-help-toggle" hidden>'
         '<i class=i-m-help></i></label>\n\n      <div id="sort-wrapper">', 'md-filter-toggle'),
        ('src/manage.html', '<div id="sort-wrapper">\n        <div class="select-wrapper" i18n="title:sortLabel">',
         '<div id="sort-wrapper">\n        <i class=i-m-sort></i>\n        <div class="select-wrapper" i18n="title:sortLabel">', 'i-m-sort'),
    ]:
        P.edit(rel, old, new, marker=mk, count=0 if mk in ('i-m-update', 'i-m-home') else 1)

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
    P.edit('src/popup/render.js',
           "    initNoStyles?.();\n    $('#main-actions').append(disabler);\n  } else {\n    $('#toggler').append(disabler);\n  }\n",
           "    initNoStyles?.();\n  }\n  $('#popup-options .md-brand').after(disabler); // mobile fork: master switch in the top bar\n",
           marker=".md-brand').after(disabler)")
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
