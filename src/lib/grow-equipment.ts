// Pure prose formatting for the public EQUIPMENT card. Mirrors the growtent
// /api/grow/live payload shapes (the repos share no code — keep in sync with
// growtent web/lib/public-equipment.ts).

export type PublicRule =
  | { kind: 'schedule'; onMin: number; offMin: number }
  | { kind: 'auto'; tempHighF?: number; rhHigh?: number; tempLowF?: number; rhLow?: number }
  | { kind: 'vpd'; high?: number; low?: number; target?: number }
  | { kind: 'cycle'; onSec: number; offSec: number }
  | { kind: 'always_on' }
  | { kind: 'manual' };

export interface PublicEquipment {
  key: 'light' | 'exhaust' | 'humidifier' | 'circulation';
  label: string;
  state: 'on' | 'off' | 'unknown';
  rule: PublicRule | null;
}

export interface EquipmentSensors {
  canopyRh: number | null;
  canopyTempF: number | null;
  canopyVpd: number | null;
}

const TENT_TZ = 'America/Los_Angeles';

// minutes-since-midnight (tent time) → "5:00 PM"
export function fmtClock(min: number): string {
  const h24 = Math.floor(min / 60) % 24;
  const m = min % 60;
  const ampm = h24 < 12 ? 'AM' : 'PM';
  const h12 = h24 % 12 === 0 ? 12 : h24 % 12;
  return `${h12}:${String(m).padStart(2, '0')} ${ampm}`;
}

function fmtDur(sec: number): string {
  if (sec < 60) return `${sec}s`;
  if (sec % 3600 === 0) return `${sec / 3600}h`;
  return `${Math.round(sec / 60)}m`;
}

// One trigger phrase per configured threshold, high side first (matches how the
// operator thinks about these: the ceiling is the active lever in this tent).
function autoPhrases(rule: PublicRule & { kind: 'auto' }): string[] {
  const out: string[] = [];
  if (rule.tempHighF != null) out.push(`above ${rule.tempHighF}°F`);
  if (rule.rhHigh != null) out.push(`above ${rule.rhHigh}% humidity`);
  if (rule.tempLowF != null) out.push(`below ${rule.tempLowF}°F`);
  if (rule.rhLow != null) out.push(`below ${rule.rhLow}% humidity`);
  return out;
}

export function ruleLine(eq: PublicEquipment): string {
  const rule = eq.rule;
  if (!rule) return 'Settings unavailable';
  switch (rule.kind) {
    case 'schedule':
      return `Runs on a schedule — on ${fmtClock(rule.onMin)}, off ${fmtClock(rule.offMin)}`;
    case 'auto': {
      // humidity-first reads more naturally when both are set
      const phrases: string[] = [];
      if (rule.rhHigh != null) phrases.push(`above ${rule.rhHigh}% humidity`);
      if (rule.tempHighF != null) phrases.push(`above ${rule.tempHighF}°F`);
      if (rule.rhLow != null) phrases.push(`below ${rule.rhLow}% humidity`);
      if (rule.tempLowF != null) phrases.push(`below ${rule.tempLowF}°F`);
      return phrases.length ? `Turns on ${phrases.join(' or ')}` : 'Automatic';
    }
    case 'vpd': {
      const phrases: string[] = [];
      if (rule.high != null) phrases.push(`rises above ${rule.high} kPa`);
      if (rule.low != null) phrases.push(`falls below ${rule.low} kPa`);
      if (phrases.length) return `Turns on when VPD ${phrases.join(' or ')}`;
      if (rule.target != null) return `Holds VPD near ${rule.target} kPa`;
      return 'VPD-controlled';
    }
    case 'cycle':
      return `Cycles — ${fmtDur(rule.onSec)} on, ${fmtDur(rule.offSec)} off`;
    case 'always_on':
      return eq.key === 'circulation' ? 'Always on — speed varies (wind simulation)' : 'Always on';
    case 'manual':
      return 'Switched manually';
  }
}

// The live cause-and-effect line, shown in the expanded row. Compares the rule against
// the canopy reading from the SAME payload. If the reported state contradicts what the
// rule predicts, return null — never invent a cause. (The exhaust actually gates on the
// strip's own probe, which we don't publish; the canopy comparison is representative
// and the contradiction guard keeps it honest.)
export function whyLine(eq: PublicEquipment, s: EquipmentSensors): string | null {
  const rule = eq.rule;
  if (!rule || eq.state === 'unknown') return null;

  type Check = { label: string; value: number; unit: string; over?: number; under?: number };
  const checks: Check[] = [];
  if (rule.kind === 'auto') {
    if (rule.rhHigh != null && s.canopyRh != null)
      checks.push({ label: 'Humidity', value: s.canopyRh, unit: '%', over: rule.rhHigh });
    if (rule.tempHighF != null && s.canopyTempF != null)
      checks.push({ label: 'Temperature', value: s.canopyTempF, unit: '°F', over: rule.tempHighF });
    if (rule.rhLow != null && s.canopyRh != null)
      checks.push({ label: 'Humidity', value: s.canopyRh, unit: '%', under: rule.rhLow });
    if (rule.tempLowF != null && s.canopyTempF != null)
      checks.push({ label: 'Temperature', value: s.canopyTempF, unit: '°F', under: rule.tempLowF });
  } else if (rule.kind === 'vpd') {
    if (rule.high != null && s.canopyVpd != null)
      checks.push({ label: 'VPD', value: s.canopyVpd, unit: ' kPa', over: rule.high });
    if (rule.low != null && s.canopyVpd != null)
      checks.push({ label: 'VPD', value: s.canopyVpd, unit: ' kPa', under: rule.low });
  } else {
    return null;
  }
  if (!checks.length) return null;

  const tripped = checks.find(
    (c) => (c.over != null && c.value > c.over) || (c.under != null && c.value < c.under),
  );
  if (eq.state === 'on' && tripped) {
    const dir = tripped.over != null ? 'above' : 'below';
    const threshold = tripped.over ?? tripped.under;
    return `${tripped.label} is ${tripped.value}${tripped.unit} — ${dir} the ${threshold}${tripped.unit} trigger → running`;
  }
  if (eq.state === 'off' && !tripped) {
    const c = checks[0];
    return `${c.label} is ${c.value}${c.unit} — within range → idle`;
  }
  return null; // state and rule disagree (gating lag, hysteresis) — stay quiet
}

// Exact configured values for the expanded view.
export function detailLines(eq: PublicEquipment): string[] {
  const rule = eq.rule;
  if (!rule) return [];
  switch (rule.kind) {
    case 'schedule':
      return [
        `On at ${fmtClock(rule.onMin)} (tent time)`,
        `Off at ${fmtClock(rule.offMin)} (tent time)`,
      ];
    case 'auto':
      return autoPhrases(rule).map((p) => `On ${p}`);
    case 'vpd': {
      const out: string[] = [];
      if (rule.high != null) out.push(`On above ${rule.high} kPa VPD`);
      if (rule.low != null) out.push(`On below ${rule.low} kPa VPD`);
      if (rule.target != null) out.push(`Target ${rule.target} kPa VPD`);
      return out;
    }
    case 'cycle':
      return [`${fmtDur(rule.onSec)} on, then ${fmtDur(rule.offSec)} off, repeating`];
    default:
      return [];
  }
}

// Header badge for the night theme. Day (or unknown phase) → no badge.
export function phaseBadge(
  phase: 'day' | 'night' | null,
  nextChange: number | null,
): string | null {
  if (phase !== 'night') return null;
  if (nextChange == null) return '🌙 lights off';
  const at = new Date(nextChange).toLocaleTimeString('en-US', {
    timeZone: TENT_TZ,
    hour: 'numeric',
    minute: '2-digit',
  });
  return `🌙 lights off · back on at ${at}`;
}
