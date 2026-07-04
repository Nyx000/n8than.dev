import { describe, it, expect } from 'bun:test';
import {
  fmtClock,
  ruleLine,
  whyLine,
  detailLines,
  phaseBadge,
  type PublicEquipment,
} from './grow-equipment';

const eq = (over: Partial<PublicEquipment>): PublicEquipment => ({
  key: 'exhaust',
  label: 'Exhaust Fan',
  state: 'on',
  rule: null,
  ...over,
});

describe('fmtClock', () => {
  it('renders minutes-since-midnight as 12h tent time', () => {
    expect(fmtClock(1020)).toBe('5:00 PM');
    expect(fmtClock(660)).toBe('11:00 AM');
    expect(fmtClock(0)).toBe('12:00 AM');
    expect(fmtClock(750)).toBe('12:30 PM');
  });
});

describe('ruleLine', () => {
  it('schedule', () => {
    expect(ruleLine(eq({ rule: { kind: 'schedule', onMin: 1020, offMin: 660 } }))).toBe(
      'Runs on a schedule — on 5:00 PM, off 11:00 AM',
    );
  });
  it('auto with both high triggers', () => {
    expect(ruleLine(eq({ rule: { kind: 'auto', rhHigh: 70, tempHighF: 86 } }))).toBe(
      'Turns on above 70% humidity or above 86°F',
    );
  });
  it('auto low trigger', () => {
    expect(ruleLine(eq({ rule: { kind: 'auto', rhLow: 40 } }))).toBe('Turns on below 40% humidity');
  });
  it('vpd high', () => {
    expect(ruleLine(eq({ rule: { kind: 'vpd', high: 1.1 } }))).toBe(
      'Turns on when VPD rises above 1.1 kPa',
    );
  });
  it('cycle', () => {
    expect(ruleLine(eq({ rule: { kind: 'cycle', onSec: 45, offSec: 900 } }))).toBe(
      'Cycles — 45s on, 15m off',
    );
  });
  it('always_on on the circulation fan mentions wind simulation', () => {
    expect(
      ruleLine(eq({ key: 'circulation', label: 'Circulation Fan', rule: { kind: 'always_on' } })),
    ).toBe('Always on — speed varies (wind simulation)');
  });
  it('manual and missing rules', () => {
    expect(ruleLine(eq({ rule: { kind: 'manual' } }))).toBe('Switched manually');
    expect(ruleLine(eq({ rule: null }))).toBe('Settings unavailable');
  });
});

describe('whyLine', () => {
  const sensors = { canopyRh: 72, canopyTempF: 84, canopyVpd: 0.9 };
  it('names the breached trigger when ON agrees with the rule', () => {
    expect(
      whyLine(eq({ state: 'on', rule: { kind: 'auto', rhHigh: 70, tempHighF: 86 } }), sensors),
    ).toBe('Humidity is 72% — above the 70% trigger → running');
  });
  it('reports in-range when OFF agrees', () => {
    expect(whyLine(eq({ state: 'off', rule: { kind: 'auto', rhHigh: 80 } }), sensors)).toBe(
      'Humidity is 72% — within range → idle',
    );
  });
  it('degrades to null on contradiction (never invents a cause)', () => {
    expect(whyLine(eq({ state: 'off', rule: { kind: 'auto', rhHigh: 70 } }), sensors)).toBeNull();
  });
  it('vpd comparison uses canopy VPD', () => {
    expect(whyLine(eq({ state: 'off', rule: { kind: 'vpd', high: 1.1 } }), sensors)).toBe(
      'VPD is 0.9 kPa — within range → idle',
    );
  });
  it('null when sensors are missing', () => {
    expect(
      whyLine(eq({ state: 'on', rule: { kind: 'auto', rhHigh: 70 } }), {
        canopyRh: null,
        canopyTempF: null,
        canopyVpd: null,
      }),
    ).toBeNull();
  });
});

describe('detailLines', () => {
  it('schedule details are tent-time labelled', () => {
    expect(detailLines(eq({ rule: { kind: 'schedule', onMin: 1020, offMin: 660 } }))).toEqual([
      'On at 5:00 PM (tent time)',
      'Off at 11:00 AM (tent time)',
    ]);
  });
  it('auto details list each configured threshold', () => {
    expect(detailLines(eq({ rule: { kind: 'auto', rhHigh: 70, tempHighF: 86 } }))).toEqual([
      'On above 86°F',
      'On above 70% humidity',
    ]);
  });
});

describe('phaseBadge', () => {
  it('night → moon badge with the next lights-on in tent time', () => {
    // 2026-07-04T00:00:00Z = 5:00 PM PDT on 2026-07-03
    expect(phaseBadge('night', Date.parse('2026-07-04T00:00:00Z'))).toBe(
      '🌙 lights off · back on at 5:00 PM',
    );
  });
  it('day or unknown → no badge', () => {
    expect(phaseBadge('day', 123)).toBeNull();
    expect(phaseBadge(null, null)).toBeNull();
    expect(phaseBadge('night', null)).toBe('🌙 lights off');
  });
});
