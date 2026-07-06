// GENERATED — DO NOT EDIT. Mirror of growtent web/lib/public-contract.ts. Regenerate via `npm run contract:public` in growtent.

// Canonical, dependency-free source of truth for the PUBLIC /api/public/live payload — the
// shapes growtent serves and n8than.dev consumes. The two repos share no package; n8than mirrors
// this file verbatim (src/lib/growtent-public-contract.ts) and the `contract:public --check` drift
// guard fails on any mismatch. Keep this file IMPORT-FREE so it can be copied across the repo
// boundary unchanged.
//
// Everything here is the deliberately-public projection: no device IDs, ports, alerts, or
// coordinates ever cross this boundary. Temps are °F (display convention), rounded.

// Reading freshness of the live feed (mirrors web/lib/time.ts Freshness).
export type PublicFreshness = 'live' | 'stale' | 'none'

// Honest on/off of a load (mirrors web/lib/port-display.ts OnState).
export type PublicOnState = 'on' | 'off' | 'unknown'

// Light day/night phase (mirrors src/profiles/selection.ts LightPhase).
export type PublicLightPhase = 'day' | 'night'

// The four curated public loads.
export type PublicEquipmentKey = 'light' | 'exhaust' | 'humidifier' | 'circulation'

// One probe's public readout (canopy / lower / room-intake).
export interface PublicSensor {
  tempF: number | null
  rh: number | null
  vpdKpa: number | null
  dewF: number | null
}

// One point on a public probe sparkline.
export interface PublicSparkPoint {
  t: number
  tempF: number | null
  rh: number | null
  vpd: number | null
}

// The climate half of the payload (toPublicLive). All three probe sparklines are published.
export interface PublicLive {
  ts: number | null
  freshness: PublicFreshness
  sensors: Record<'canopy' | 'lower' | 'room', PublicSensor | null>
  spark: Record<'canopy' | 'lower' | 'room', PublicSparkPoint[]>
}

// A structured automation rule (the page renders the prose). °F thresholds, kPa VPD,
// minutes-since-midnight in tent tz.
export type PublicRule =
  | { kind: 'schedule'; onMin: number; offMin: number }
  | { kind: 'auto'; tempHighF?: number; rhHigh?: number; tempLowF?: number; rhLow?: number }
  | { kind: 'vpd'; high?: number; low?: number; target?: number }
  | { kind: 'cycle'; onSec: number; offSec: number }
  | { kind: 'always_on' }
  | { kind: 'manual' }

// One curated public load with its on/off state and structured rule.
export interface PublicEquipment {
  key: PublicEquipmentKey
  label: string
  state: PublicOnState
  rule: PublicRule | null
}

// The equipment half of the payload (buildPublicEquipment).
export interface PublicEquipmentSlice {
  equipment: PublicEquipment[]
  lightPhase: PublicLightPhase | null
  nextPhaseChange: number | null // epoch ms of the next lights on/off flip
}

// The non-locating seasonal hint (buildPublicNotice). No numbers, no place name, no coordinates.
export interface PublicNotice {
  conditions: 'warm_spell' | 'humid_spell' | 'nominal' | null
  note: string | null // curated phrase; NO numbers, NO place. null = show nothing.
}

// The full /api/public/live response: climate + equipment + notice, merged flat.
export interface PublicLivePayload extends PublicLive, PublicEquipmentSlice {
  notice: PublicNotice
}
