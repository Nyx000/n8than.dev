/**
 * Render a resolved BOM as a printable build sheet (V2.7), mirroring the paper layout.
 * Port of work/ordersheet/engine/render.py — returns the INNER markup of `.buildsheet`
 * (the CSS lives in the page's global styles so re-renders don't re-inject a stylesheet).
 *
 * Left column:  Base Model Components  /  Base Model Hardware
 * Right column: Add-Ons  /  Add-On Hardware
 * Each sub-grouped by shipping box with the familiar C/Pr/Pa and St/Pa columns. Only the
 * parts THIS order needs are shown; the stage checkboxes stay empty for workers to tick.
 */
import type { Catalog } from './4runnerCatalog';
import type { BomItem, Order } from './resolveBuildSheet';

const SOURCE_LABELS: Record<string, string> = {
  bed_extension: 'Bed Extension',
  second_row_delete: '2nd Row Delete',
  separators: 'Separators',
  extra_dividers: 'Extra Dividers',
  false_tops: 'False Tops',
};
const ADDON_SOURCES = Object.keys(SOURCE_LABELS);
const BASE_COMPONENT_SOURCES = new Set(['base', 'variant']);
const STAGE_HEADER: Record<string, string> = { cut: 'C · Pr · Pa', stocked: 'St · Pa' };
const STAGE_BOXES: Record<string, number> = { cut: 3, stocked: 2 };

function esc(s: unknown): string {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function sortkey(it: BomItem): [string, number] {
  const m = /^([A-Za-z]+)(\d+)?/.exec(String(it.id ?? ''));
  return m ? [m[1], parseInt(m[2] || '0', 10)] : [String(it.id ?? ''), 0];
}

function cmpSort(a: BomItem, b: BomItem): number {
  const [al, an] = sortkey(a);
  const [bl, bn] = sortkey(b);
  if (al < bl) return -1;
  if (al > bl) return 1;
  return an - bn;
}

function rows(items: BomItem[]): string {
  let out = '';
  for (const it of items) {
    const n = STAGE_BOXES[it.stage_type] ?? 3;
    const chks = '<span class="chk">&#9744;</span>'.repeat(n);
    const qty = it.qty;
    const qtyS = qty !== null && qty !== undefined && qty !== 1 ? `<span class="qty">&times;${qty}</span>` : '';
    out += `<tr><td class="stages">${chks}</td><td class="pid">${esc(it.id)}</td><td>${esc(it.desc)} ${qtyS}</td></tr>`;
  }
  return out;
}

function boxed(items: BomItem[], boxNames: Record<number, string>): string {
  const byBox = new Map<number, BomItem[]>();
  for (const it of items) {
    const b = it.box ?? 0;
    if (!byBox.has(b)) byBox.set(b, []);
    byBox.get(b)!.push(it);
  }
  let out = '';
  for (const b of [...byBox.keys()].sort((x, y) => x - y)) {
    const list = byBox.get(b)!;
    const r = rows([...list].sort(cmpSort));
    const stage = list[0].stage_type ?? 'cut';
    out +=
      `<div class="boxgrp"><div class="boxhdr">` +
      `<span class="bx">Box ${b}</span><span class="bn">${esc(boxNames[b] ?? '')}</span>` +
      `<span class="cols">${esc(STAGE_HEADER[stage] ?? '')}</span></div>` +
      `<table class="parts">${r}</table></div>`;
  }
  return out;
}

function addonBlocks(items: BomItem[], boxNames: Record<number, string>): string {
  const bySrc = new Map<string, BomItem[]>();
  for (const it of items) {
    if (!bySrc.has(it.source)) bySrc.set(it.source, []);
    bySrc.get(it.source)!.push(it);
  }
  let out = '';
  for (const src of ADDON_SOURCES) {
    const list = bySrc.get(src);
    if (list) {
      out += `<div class="addon"><div class="addonname">${esc(SOURCE_LABELS[src])}</div>${boxed(list, boxNames)}</div>`;
    }
  }
  return out;
}

export function renderBuildSheet(order: Order, bom: BomItem[], warnings: string[], catalog: Catalog): string {
  const meta = catalog.meta;
  const boxNames = catalog.legend.boxes;
  const cust = order.customer ?? {};

  const baseComp = bom.filter((i) => BASE_COMPONENT_SOURCES.has(i.source) && i.stage_type === 'cut');
  const baseHw = bom.filter((i) => i.source === 'base_hw');
  const addonComp = bom.filter((i) => ADDON_SOURCES.includes(i.source) && i.stage_type === 'cut');
  const addonHw = bom.filter((i) => ADDON_SOURCES.includes(i.source) && i.stage_type === 'stocked');

  const left =
    `<h2>Base Model Components</h2>${boxed(baseComp, boxNames)}` +
    `<h2>Base Model Hardware</h2>${boxed(baseHw, boxNames)}`;

  let right = '';
  if (addonComp.length) right += `<h2>Add-Ons</h2>${addonBlocks(addonComp, boxNames)}`;
  if (addonHw.length) right += `<h2>Add-On Hardware</h2>${addonBlocks(addonHw, boxNames)}`;
  if (!right) right = `<h2>Add-Ons</h2><div class="none">None selected on this order.</div>`;

  const addons = order.add_ons ?? {};
  const addonSummary =
    Object.entries(addons)
      .filter(([, v]) => v !== null && v !== undefined && v !== 'none' && v !== '')
      .map(([k, v]) => `${k}=${v}`)
      .join(', ') || 'none';

  let flagsHtml = '';
  if (warnings.length) {
    const lis = warnings.map((w) => `<li>${esc(w)}</li>`).join('');
    flagsHtml = `<div class="flags"><b>&#9888; Review flags (human check before build):</b><ul>${lis}</ul></div>`;
  }

  const now = new Date();
  const pad = (n: number): string => String(n).padStart(2, '0');
  const generated =
    `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ` +
    `${pad(now.getHours())}:${pad(now.getMinutes())}`;

  let shipLine = '';
  if (cust.shipping_address || cust.contact) {
    shipLine =
      `<div class="meta"><span><b>Ship</b> ${esc(cust.shipping_address)}</span>` +
      `<span><b>Contact</b> ${esc(cust.contact)}</span></div>`;
  }

  const header =
    `<header><h1>4Runner 4th &amp; 5th Gen &mdash; Build Sheet</h1>` +
    `<div class="sub">${esc(meta.kit_version)} &middot; ${esc(meta.hardware_variant)} &middot; ` +
    `pre-filled for this order &middot; generated ${generated}</div>` +
    `<div class="meta">` +
    `<span><b>Order #</b> ${esc(order.order_number)}</span><span><b>Customer</b> ${esc(cust.name)}</span>` +
    `<span><b>Generation</b> ${esc(order.generation)}</span><span><b>Rear</b> ${esc(order.rear_config)}</span>` +
    `<span><b>Fulfillment</b> ${esc(order.fulfillment)}</span><span><b>Add-ons</b> ${esc(addonSummary)}</span>` +
    `</div>${shipLine}</header>`;

  const footer =
    `<footer><span class="sign">Packed By<span class="line"></span></span>` +
    `<span class="sign">QA Check By<span class="line"></span></span>` +
    `<span class="sign">Date<span class="line"></span></span></footer>`;

  const body = `<div class="sheet"><div class="col">${left}</div><div class="col">${right}</div></div>`;

  return `${header}${flagsHtml}${body}${footer}`;
}
