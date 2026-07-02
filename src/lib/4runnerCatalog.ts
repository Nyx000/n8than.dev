/**
 * SOURCE OF TRUTH — 4Runner 4th & 5th Gen (F-series) · Pilot catalog.
 *
 * Ported verbatim from work/ordersheet/catalog/4runner-4th-5th-gen.yaml, which was
 * transcribed from a phone photo of the "V2.7 Checklist (China Hex + China Slides)".
 *
 * DRAFT — every id / description / qty was read off a photo. Rules the sheet does not
 * state (cubby selection, set/pair quantities, 2nd-row-delete behaviour, duplicate-id
 * summing) are applied as sensible defaults AND surfaced as review flags, never guessed
 * silently. Verify against a clean V2.7 source before trusting for production.
 */

export type StageType = 'cut' | 'stocked';

export interface Part {
  id?: string;
  key?: string;
  desc: string;
  box: number;
  stage_type: StageType;
  qty?: number;
  unit?: string;
}

export interface SelectRule {
  when: { generation?: string; rear_config?: string };
  id: string;
}

export interface VariantPart {
  label: string;
  box: number;
  stage_type: StageType;
  qty: number;
  options: string[];
  select: SelectRule[];
}

export interface Module {
  parts?: Part[];
  hardware?: Part[];
}

export interface FalseTops {
  types: Record<string, string>;
  box: number;
  stage_type: StageType;
  per_side: boolean;
  qty_per_side: number;
}

export interface Catalog {
  meta: {
    vehicle: string;
    generations: string[];
    kit_version: string;
    hardware_variant: string;
    source_document: string;
    source_updated: string;
    status: string;
  };
  legend: {
    boxes: Record<number, string>;
    stage_types: Record<StageType, string[]>;
  };
  base_model: Part[];
  variant_parts: Record<string, VariantPart>;
  base_hardware: Part[];
  modules: {
    second_row_delete: Module;
    bed_extension: Module;
    separators: Module;
    extra_dividers: Module;
    false_tops: FalseTops;
  };
}

export const CATALOG_4RUNNER: Catalog = {
  meta: {
    vehicle: '4Runner',
    generations: ['4th', '5th'],
    kit_version: 'V2.7',
    hardware_variant: 'China Hex + China Slides',
    source_document: '4Runner 4th & 5th Gen V2.7 Checklist (China Hex + China Slides)',
    source_updated: '2026-06-03',
    status: 'DRAFT — unverified',
  },

  legend: {
    boxes: {
      1: 'Main Pieces (Big)',
      2: 'Main Pieces (Small)',
      3: 'Jams',
      4: 'False Tops',
      5: 'Bed',
    },
    stage_types: {
      cut: ['Cut', 'Processed', 'Packed'],
      stocked: ['Stocked', 'Packed'],
    },
  },

  // ── ALWAYS INCLUDED (wood, stage_type: cut) ─────────────────────────────────
  base_model: [
    // Box 1 — Main Pieces (Big)
    { id: 'F4', desc: 'Box Back', box: 1, stage_type: 'cut', qty: 1 },
    { id: 'F5', desc: 'Box Bottom (Back)', box: 1, stage_type: 'cut', qty: 1 },
    { id: 'F6', desc: 'Box Bottom (Front)', box: 1, stage_type: 'cut', qty: 1 },
    { id: 'F7', desc: 'Box Top (Left)', box: 1, stage_type: 'cut', qty: 1 },
    { id: 'F8', desc: 'Box Top (Right)', box: 1, stage_type: 'cut', qty: 1 },
    { id: 'F18', desc: 'Drawer Bottom', box: 1, stage_type: 'cut', qty: 2 },
    // Box 2 — Main Pieces (Small)   [cubbies are in variant_parts below]
    { id: 'F17', desc: 'Drawer Back', box: 2, stage_type: 'cut', qty: 2 },
    { id: 'F19', desc: 'Drawer Face (Left)', box: 2, stage_type: 'cut', qty: 1 },
    { id: 'F20', desc: 'Drawer Face (Right)', box: 2, stage_type: 'cut', qty: 1 },
    { id: 'F21', desc: 'Divider', box: 2, stage_type: 'cut', qty: 4 },
    // Box 3 — Jams
    { id: 'F1', desc: 'Left Box Jam', box: 3, stage_type: 'cut', qty: 1 },
    { id: 'F2', desc: 'Right Box Jam', box: 3, stage_type: 'cut', qty: 1 },
    { id: 'F3', desc: 'Centre Box Jam', box: 3, stage_type: 'cut', qty: 1 },
    { id: 'F13', desc: 'Left Drawer, Left Jam', box: 3, stage_type: 'cut', qty: 1 },
    { id: 'F14', desc: 'Right Drawer, Left Jam', box: 3, stage_type: 'cut', qty: 1 },
    { id: 'F15', desc: 'Left Drawer, Right Jam', box: 3, stage_type: 'cut', qty: 1 },
    { id: 'F16', desc: 'Right Drawer, Right Jam', box: 3, stage_type: 'cut', qty: 1 },
  ],

  // ── PICK-ONE LINES (one sku per cubby, by generation + rear_config) ─────────
  // The V2.7 sheet prints THREE skus per cubby; the selection RULE below is inferred
  // from the assembly manual and is surfaced as a review flag on every sheet.
  variant_parts: {
    top_cubby_left: {
      label: 'Top Cubby (Left)',
      box: 2,
      stage_type: 'cut',
      qty: 1,
      options: ['F9', 'F39', 'F41'],
      select: [
        { when: { generation: '5th', rear_config: 'standard' }, id: 'F9' },
        { when: { generation: '5th', rear_config: '3rd_row_delete' }, id: 'F39' },
        { when: { generation: '4th' }, id: 'F41' },
      ],
    },
    top_cubby_right: {
      label: 'Top Cubby (Right)',
      box: 2,
      stage_type: 'cut',
      qty: 1,
      options: ['F10', 'F40', 'F42'],
      select: [
        { when: { generation: '5th', rear_config: 'standard' }, id: 'F10' },
        { when: { generation: '5th', rear_config: '3rd_row_delete' }, id: 'F40' },
        { when: { generation: '4th' }, id: 'F42' },
      ],
    },
    side_cubby_left: {
      label: 'Side Cubby (Left)',
      box: 2,
      stage_type: 'cut',
      qty: 1,
      options: ['F11', 'F43', 'F45'],
      select: [
        { when: { generation: '5th', rear_config: 'standard' }, id: 'F11' },
        { when: { generation: '5th', rear_config: '3rd_row_delete' }, id: 'F43' },
        { when: { generation: '4th' }, id: 'F45' },
      ],
    },
    side_cubby_right: {
      label: 'Side Cubby (Right)',
      box: 2,
      stage_type: 'cut',
      qty: 1,
      options: ['F12', 'F44', 'F46'],
      select: [
        { when: { generation: '5th', rear_config: 'standard' }, id: 'F12' },
        { when: { generation: '5th', rear_config: '3rd_row_delete' }, id: 'F44' },
        { when: { generation: '4th' }, id: 'F46' },
      ],
    },
  },

  // ── BASE HARDWARE (stage_type: stocked) ─────────────────────────────────────
  base_hardware: [
    { key: 'SLIDE-LOCK-36', desc: 'Pair of Locking 36" Slides (China — pack with order)', box: 1, stage_type: 'stocked', qty: 1, unit: 'pair' },
    { key: 'SLIDE-NONLOCK-36', desc: 'Pair of Nonlocking 36" Slides (China — pack with order)', box: 1, stage_type: 'stocked', qty: 1, unit: 'pair' },
    { id: 'H1', desc: '7/16" Framing Screw (Hinges)', box: 2, stage_type: 'stocked', qty: 20 },
    { id: 'H3', desc: '1/4" Black Wood Screws', box: 2, stage_type: 'stocked', qty: 140 },
    { id: 'H7', desc: 'Medium Turnbuckle', box: 2, stage_type: 'stocked', qty: 2 },
    { id: 'H9', desc: 'D-Ring [Ring & Back Plate]', box: 2, stage_type: 'stocked', qty: 2 },
    { id: 'H10', desc: '1/4-20 x 3/4" Bolts', box: 2, stage_type: 'stocked', qty: 8 },
    { id: 'H11', desc: '10-32 x 1/2" Screws', box: 2, stage_type: 'stocked', qty: 35 },
    { id: 'H13', desc: '10-32 x 1/2" T-Nut', box: 2, stage_type: 'stocked', qty: 35 },
    { id: 'H14', desc: '1/4-20 x 3/4" T-Nut', box: 2, stage_type: 'stocked', qty: 8 },
    { id: 'PH16', desc: 'Piano Hinge 16"', box: 2, stage_type: 'stocked', qty: 2 },
    { id: 'H19', desc: 'L Bracket', box: 2, stage_type: 'stocked', qty: 2 },
  ],

  // ── ADD-ON MODULES (included only if the order selects them) ─────────────────
  modules: {
    second_row_delete: {
      parts: [
        { id: 'F35', desc: '50% Bed Split (Left)', box: 1, stage_type: 'cut', qty: 1 },
        { id: 'F36', desc: '50% Bed Split (Right)', box: 1, stage_type: 'cut', qty: 1 },
        { id: 'F37', desc: '2nd Row Delete Plate', box: 1, stage_type: 'cut', qty: 1 },
      ],
      hardware: [
        { id: 'PH32', desc: 'Piano Hinge 32"', box: 2, stage_type: 'stocked', qty: 1 },
        { id: 'H1', desc: '7/16" Framing Screw', box: 2, stage_type: 'stocked', qty: 20 },
        { id: 'H10', desc: '1/4-20 x 3/4" Bolt', box: 2, stage_type: 'stocked', qty: 4 },
        { id: 'H14', desc: '1/4-20 x 3/4" T-Nut', box: 2, stage_type: 'stocked', qty: 4 },
        { id: 'H00', desc: '30° bracket', box: 2, stage_type: 'stocked', qty: 4 },
      ],
    },

    bed_extension: {
      parts: [
        { id: 'F25', desc: 'Cleat', box: 1, stage_type: 'cut', qty: 1 },
        { id: 'F28', desc: '40% Horizontal Support', box: 2, stage_type: 'cut', qty: 1 },
        { id: 'F29', desc: '40% Vertical Support', box: 2, stage_type: 'cut', qty: 1 },
        { id: 'F30', desc: '60% Horizontal Support', box: 2, stage_type: 'cut', qty: 1 },
        { id: 'F31', desc: '60% Vertical Support', box: 2, stage_type: 'cut', qty: 1 },
        { id: 'F26', desc: '40% Bed Piece', box: 5, stage_type: 'cut', qty: 1 },
        { id: 'F27', desc: '60% Bed Piece', box: 5, stage_type: 'cut', qty: 1 },
      ],
      hardware: [
        { id: 'PH14', desc: 'Piano Hinge 14"', box: 2, stage_type: 'stocked', qty: 1 },
        { id: 'PH24', desc: 'Piano Hinge 24"', box: 2, stage_type: 'stocked', qty: 1 },
        { id: 'H1', desc: '7/16" Framing Screw', box: 2, stage_type: 'stocked', qty: 20 },
      ],
    },

    separators: {
      parts: [
        { id: 'F22', desc: 'Separator - Small', box: 2, stage_type: 'cut', qty: 1 },
        { id: 'F23', desc: 'Separator - Medium', box: 2, stage_type: 'cut', qty: 1 },
        { id: 'F24', desc: 'Separator - Large', box: 2, stage_type: 'cut', qty: 1 },
      ],
    },

    extra_dividers: {
      parts: [{ id: 'F21', desc: 'Divider', box: 2, stage_type: 'cut', qty: 2 }],
    },

    false_tops: {
      types: { bamboo: 'F32', metal: 'F33', normal: 'F34' },
      box: 4,
      stage_type: 'cut',
      per_side: true,
      qty_per_side: 2,
    },
  },
};
