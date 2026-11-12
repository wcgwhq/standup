/**
 * Copied from slopmeter-ai (src/components/WhackAMole.tsx), Radu's own WCGW arcade.
 * Only the four slopmeter colour classes were swapped for Tailwind neutrals.
 * It keeps its own dark palette; WcgwFooter.astro gives it a dark band to sit on.
 *
 * WhackAMole — Self-contained whack-a-mole arcade mini-game using the WCGW logo.
 * Zero dependencies beyond React. All SVGs and CSS keyframes are inline.
 * Designed to be extractable for reuse across WCGW project sites.
 *
 * Features:
 *  - Autoplay (no rounds, no buttons — runs continuously from mount)
 *  - Click ripples anywhere on the game area
 *  - Mother + Baby easter egg every 5th popup
 *  - Warning escalation at 3, 5, 7, 9 cumulative hits
 *  - Doomsday sequence at 10 cumulative hits
 */

import { useReducer, useEffect, useRef, useState, useCallback } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface WhackAMoleProps {
  holeCount?: number;
  className?: string;
}

/** Keyboard keys mapped to each hole (middle row: a-l) */
const HOLE_KEYS = ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'] as const;

interface HoleState {
  readonly status: 'empty' | 'up' | 'whacked' | 'missed';
  readonly variant: 'mole' | 'mother';
}

interface GameState {
  readonly phase: 'playing' | 'doomsday';
  readonly score: number;
  readonly misses: number;
  readonly holes: ReadonlyArray<HoleState>;
}

type GameAction =
  | { type: 'MOLE_UP'; index: number; variant: 'mole' | 'mother' }
  | { type: 'MOLE_DOWN'; index: number }
  | { type: 'WHACK'; index: number }
  | { type: 'CLEAR_HOLE'; index: number }
  | { type: 'DOOM' };

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const LS_KEY = 'wam-high-score';
const DEFAULT_HOLES = 9;
const MAX_MOLES = 2;
const HIT_CLEAR_MS = 2000;
const MISS_CLEAR_MS = 250;
const FIRST_SPAWN_MS = 800;
const SPAWN_INTERVAL_MS = 2200;
const MOLE_VISIBLE_MS = 4000;
const WARNING_DURATION_MS = 2000;
const MONSTER_DURATION_MS = 3000;

const WARNING_THRESHOLDS: ReadonlyArray<{
  readonly hits: number;
  readonly message: string;
  readonly color: string;
  readonly flash: boolean;
}> = [
  { hits: 3, message: 'CAREFUL...', color: 'text-amber-400', flash: false },
  { hits: 5, message: "YOU'RE PUSHING IT", color: 'text-orange-500', flash: false },
  { hits: 7, message: 'SERIOUSLY.', color: 'text-red-500', flash: false },
  { hits: 9, message: 'FINAL WARNING', color: 'text-red-500', flash: true },
];

// ---------------------------------------------------------------------------
// High-score persistence
// ---------------------------------------------------------------------------

function readHigh(): number {
  try {
    return parseInt(localStorage.getItem(LS_KEY) ?? '0', 10) || 0;
  } catch {
    return 0;
  }
}

function writeHigh(score: number): void {
  try {
    localStorage.setItem(LS_KEY, String(score));
  } catch {
    /* localStorage unavailable */
  }
}

// ---------------------------------------------------------------------------
// Reducer
// ---------------------------------------------------------------------------

function initState(holeCount: number): GameState {
  return {
    phase: 'playing',
    score: 0,
    misses: 0,
    holes: Array.from({ length: holeCount }, (): HoleState => ({
      status: 'empty',
      variant: 'mole',
    })),
  };
}

function reducer(state: GameState, action: GameAction): GameState {
  switch (action.type) {
    case 'MOLE_UP': {
      if (state.phase !== 'playing') return state;
      if (state.holes[action.index].status !== 'empty') return state;
      return {
        ...state,
        holes: state.holes.map((h, i) =>
          i === action.index ? { status: 'up' as const, variant: action.variant } : h,
        ),
      };
    }

    case 'MOLE_DOWN': {
      if (state.phase !== 'playing') return state;
      if (state.holes[action.index].status !== 'up') return state;
      return {
        ...state,
        misses: state.misses + 1,
        holes: state.holes.map((h, i) => (i === action.index ? { ...h, status: 'missed' as const } : h)),
      };
    }

    case 'WHACK': {
      if (state.phase !== 'playing') return state;
      if (state.holes[action.index].status !== 'up') return state;
      const hole = state.holes[action.index];
      const isMole = hole.variant === 'mole';
      return {
        ...state,
        score: isMole ? state.score + 1 : state.score,
        holes: state.holes.map((h, i) => (i === action.index ? { ...h, status: 'whacked' as const } : h)),
      };
    }

    case 'CLEAR_HOLE': {
      if (state.holes[action.index].status === 'empty') return state;
      return {
        ...state,
        holes: state.holes.map((h, i) =>
          i === action.index ? { status: 'empty' as const, variant: 'mole' as const } : h,
        ),
      };
    }

    case 'DOOM':
      return {
        ...state,
        phase: 'doomsday',
        holes: state.holes.map((): HoleState => ({
          status: 'empty',
          variant: 'mole',
        })),
      };

    default:
      return state;
  }
}

// ---------------------------------------------------------------------------
// Inline SVGs (game-internal, not exported)
// ---------------------------------------------------------------------------

function WcgwMole({ hit }: { hit?: boolean }) {
  return (
    <svg
      width="48"
      height="32"
      viewBox="0 0 100 68"
      fill="none"
      className={hit ? 'text-neutral-500' : 'text-amber-400'}
      aria-hidden="true"
    >
      <path
        d="M4 50 A46 14 0 0 1 25 37"
        stroke="currentColor"
        strokeWidth="3.5"
        fill="none"
        strokeLinecap="round"
      />
      <path
        d="M75 37 A46 14 0 0 1 96 50"
        stroke="currentColor"
        strokeWidth="3.5"
        fill="none"
        strokeLinecap="round"
      />
      <path
        d="M4 50 A46 14 0 0 0 96 50"
        stroke="currentColor"
        strokeWidth="3.5"
        fill="none"
        strokeLinecap="round"
      />
      <path
        d="M25 50 C25 50 25 20 50 20 C75 20 75 50 75 50"
        stroke="currentColor"
        strokeWidth="3.5"
        fill="none"
        strokeLinecap="round"
      />
      {hit ? (
        <>
          <g stroke="currentColor" strokeWidth="3" strokeLinecap="round">
            <line x1="32" y1="32" x2="44" y2="44" />
            <line x1="44" y1="32" x2="32" y2="44" />
          </g>
          <g stroke="currentColor" strokeWidth="3" strokeLinecap="round">
            <line x1="56" y1="32" x2="68" y2="44" />
            <line x1="68" y1="32" x2="56" y2="44" />
          </g>
        </>
      ) : (
        <>
          <g stroke="currentColor" strokeWidth="3" strokeLinecap="round">
            <line x1="38" y1="32" x2="38" y2="44" />
            <line x1="32" y1="38" x2="44" y2="38" />
          </g>
          <g stroke="currentColor" strokeWidth="3" strokeLinecap="round">
            <line x1="56" y1="32" x2="68" y2="44" />
            <line x1="68" y1="32" x2="56" y2="44" />
          </g>
        </>
      )}
    </svg>
  );
}

function DoomMascotWithSign() {
  return (
    <svg width="260" height="220" viewBox="0 0 260 220" fill="none" aria-hidden="true">
      {/* ── Sign board (held UP by mascot) ─────────────────── */}
      {/* Sign pole — runs from mascot hands up into sign */}
      <line x1="130" y1="68" x2="130" y2="130" stroke="#525252" strokeWidth="2" strokeLinecap="round" />
      {/* Sign background */}
      <rect
        x="30"
        y="4"
        width="200"
        height="64"
        rx="2"
        fill="#0a0a0a"
        stroke="#404040"
        strokeWidth="1.5"
        strokeDasharray="6 3"
      />
      {/* Inner border — decorative double-frame */}
      <rect x="36" y="10" width="188" height="52" rx="1" fill="none" stroke="#333" strokeWidth="0.75" />
      {/* Corner brackets — top-left */}
      <path d="M34 18 L34 8 L44 8" stroke="#525252" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      {/* Corner brackets — top-right */}
      <path d="M226 18 L226 8 L216 8" stroke="#525252" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      {/* Corner brackets — bottom-left */}
      <path d="M34 54 L34 64 L44 64" stroke="#525252" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      {/* Corner brackets — bottom-right */}
      <path
        d="M226 54 L226 64 L216 64"
        stroke="#525252"
        strokeWidth="1.5"
        fill="none"
        strokeLinecap="round"
      />
      {/* Warning stripes — left */}
      <line x1="42" y1="32" x2="50" y2="32" stroke="#ef4444" strokeWidth="1" opacity="0.5" />
      <line x1="42" y1="36" x2="50" y2="36" stroke="#ef4444" strokeWidth="1" opacity="0.5" />
      <line x1="42" y1="40" x2="50" y2="40" stroke="#ef4444" strokeWidth="1" opacity="0.5" />
      {/* Warning stripes — right */}
      <line x1="210" y1="32" x2="218" y2="32" stroke="#ef4444" strokeWidth="1" opacity="0.5" />
      <line x1="210" y1="36" x2="218" y2="36" stroke="#ef4444" strokeWidth="1" opacity="0.5" />
      <line x1="210" y1="40" x2="218" y2="40" stroke="#ef4444" strokeWidth="1" opacity="0.5" />
      {/* Sign text */}
      <text
        x="130"
        y="34"
        textAnchor="middle"
        fill="#ef4444"
        fontSize="13"
        fontFamily="'Kode Mono',ui-monospace,monospace"
        letterSpacing="2"
      >
        THIS COULD GO WRONG
      </text>
      <text
        x="130"
        y="52"
        textAnchor="middle"
        fill="#737373"
        fontSize="9"
        fontFamily="'Kode Mono',ui-monospace,monospace"
        letterSpacing="1.5"
      >
        YOU WERE WARNED
      </text>

      {/* ── Smiling mascot (below sign, holding it up) ──── */}
      <g transform="translate(80, 100)">
        {/* Left arm — shoulder → elbow bend → wrist */}
        <path
          d="M34 22 C28 14 34 2 49 -5"
          stroke="#34d399"
          strokeWidth="2.5"
          fill="none"
          strokeLinecap="round"
        />
        {/* Right arm — shoulder → elbow bend → wrist */}
        <path
          d="M66 22 C72 14 66 2 51 -5"
          stroke="#34d399"
          strokeWidth="2.5"
          fill="none"
          strokeLinecap="round"
        />
        {/* Left hand grip — C-shape wrapping pole */}
        <path
          d="M47 -9 C43 -6 43 -1 47 2"
          stroke="#34d399"
          strokeWidth="2"
          fill="none"
          strokeLinecap="round"
        />
        {/* Right hand grip — C-shape wrapping pole */}
        <path
          d="M53 -9 C57 -6 57 -1 53 2"
          stroke="#34d399"
          strokeWidth="2"
          fill="none"
          strokeLinecap="round"
        />
        {/* Left thumb — angled outward */}
        <line
          x1="46"
          y1="-1"
          x2="43"
          y2="1"
          stroke="#34d399"
          strokeWidth="1.5"
          strokeLinecap="round"
          opacity="0.7"
        />
        {/* Right thumb — angled outward */}
        <line
          x1="54"
          y1="-1"
          x2="57"
          y2="1"
          stroke="#34d399"
          strokeWidth="1.5"
          strokeLinecap="round"
          opacity="0.7"
        />
        {/* Knuckle details */}
        <circle cx="45" cy="-5" r="1" fill="#34d399" opacity="0.5" />
        <circle cx="55" cy="-5" r="1" fill="#34d399" opacity="0.5" />
        {/* Ring arcs */}
        <path
          d="M4 50 A46 14 0 0 1 25 37"
          stroke="#34d399"
          strokeWidth="3.5"
          fill="none"
          strokeLinecap="round"
        />
        <path
          d="M75 37 A46 14 0 0 1 96 50"
          stroke="#34d399"
          strokeWidth="3.5"
          fill="none"
          strokeLinecap="round"
        />
        <path
          d="M4 50 A46 14 0 0 0 96 50"
          stroke="#34d399"
          strokeWidth="3.5"
          fill="none"
          strokeLinecap="round"
        />
        {/* Dome */}
        <path
          d="M25 50 C25 50 25 20 50 20 C75 20 75 50 75 50"
          stroke="#34d399"
          strokeWidth="3.5"
          fill="none"
          strokeLinecap="round"
        />
        {/* Happy arc eyes ⌒ ⌒ */}
        <path d="M32 42 Q38 32 44 42" stroke="#34d399" strokeWidth="3" fill="none" strokeLinecap="round" />
        <path d="M56 42 Q62 32 68 42" stroke="#34d399" strokeWidth="3" fill="none" strokeLinecap="round" />
      </g>

      {/* ── Hazard indicator ── */}
      <circle cx="130" cy="172" r="3" fill="#ef4444" opacity="0.6" className="wam-blink" />
      <text
        x="130"
        y="187"
        textAnchor="middle"
        fill="#404040"
        fontSize="7"
        fontFamily="'Kode Mono',ui-monospace,monospace"
        letterSpacing="3"
      >
        SYSTEM OFFLINE
      </text>
    </svg>
  );
}

function MotherAndBaby({ hit }: { hit?: boolean }) {
  return (
    <svg
      width="48"
      height="32"
      viewBox="0 0 100 68"
      fill="none"
      className={hit ? 'text-red-500' : 'text-pink-400'}
      aria-hidden="true"
    >
      {/* Mother ring arcs — slightly wider */}
      <path
        d="M2 52 A48 14 0 0 1 22 38"
        stroke="currentColor"
        strokeWidth="3"
        fill="none"
        strokeLinecap="round"
      />
      <path
        d="M78 38 A48 14 0 0 1 98 52"
        stroke="currentColor"
        strokeWidth="3"
        fill="none"
        strokeLinecap="round"
      />
      <path
        d="M2 52 A48 14 0 0 0 98 52"
        stroke="currentColor"
        strokeWidth="3"
        fill="none"
        strokeLinecap="round"
      />
      {/* Mother dome — wider, rounder */}
      <path
        d="M22 52 C22 52 22 18 50 18 C78 18 78 52 78 52"
        stroke="currentColor"
        strokeWidth="3"
        fill="none"
        strokeLinecap="round"
      />
      {/* Mother heart eyes */}
      <path
        d="M34 34 L37 31 L40 34 L37 38 Z"
        stroke="currentColor"
        strokeWidth="1.5"
        fill="currentColor"
        strokeLinejoin="round"
      />
      <path
        d="M56 34 L59 31 L62 34 L59 38 Z"
        stroke="currentColor"
        strokeWidth="1.5"
        fill="currentColor"
        strokeLinejoin="round"
      />
      {/* Baby dome — small, ~40% size, held below-right */}
      <path
        d="M56 56 C56 56 56 44 66 44 C76 44 76 56 76 56"
        stroke="currentColor"
        strokeWidth="2.5"
        fill="none"
        strokeLinecap="round"
      />
      {/* Baby eyes — tiny dots */}
      <circle cx="63" cy="50" r="1.5" fill="currentColor" />
      <circle cx="70" cy="50" r="1.5" fill="currentColor" />
    </svg>
  );
}

function SplatEffect() {
  return (
    <svg width="64" height="64" viewBox="0 0 64 64" fill="none" aria-hidden="true">
      {/* Center impact dot */}
      <circle cx="32" cy="32" r="5" fill="#f59e0b" opacity="0.9" />
      {/* Inner ring */}
      <circle cx="32" cy="32" r="11" stroke="#ef4444" strokeWidth="2.5" fill="none" opacity="0.8" />
      {/* Middle ring */}
      <circle cx="32" cy="32" r="20" stroke="#ef4444" strokeWidth="1.5" fill="none" opacity="0.5" />
      {/* Outer ring */}
      <circle cx="32" cy="32" r="30" stroke="#ef4444" strokeWidth="1" fill="none" opacity="0.3" />
      {/* Impact lines — star burst */}
      <g stroke="#f59e0b" strokeWidth="1.5" strokeLinecap="round" opacity="0.7">
        <line x1="32" y1="4" x2="32" y2="16" />
        <line x1="32" y1="48" x2="32" y2="60" />
        <line x1="4" y1="32" x2="16" y2="32" />
        <line x1="48" y1="32" x2="60" y2="32" />
        <line x1="12" y1="12" x2="20" y2="20" />
        <line x1="44" y1="44" x2="52" y2="52" />
        <line x1="52" y1="12" x2="44" y2="20" />
        <line x1="20" y1="44" x2="12" y2="52" />
      </g>
    </svg>
  );
}

function HammerIcon() {
  return (
    <svg width="64" height="80" viewBox="0 0 40 50" fill="none" className="text-amber-400" aria-hidden="true">
      {/* Handle — wrapped grip */}
      <line x1="20" y1="24" x2="20" y2="46" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
      {/* Grip wraps */}
      <line x1="17" y1="30" x2="23" y2="30" stroke="currentColor" strokeWidth="1" opacity="0.5" />
      <line x1="17" y1="34" x2="23" y2="34" stroke="currentColor" strokeWidth="1" opacity="0.5" />
      <line x1="17" y1="38" x2="23" y2="38" stroke="currentColor" strokeWidth="1" opacity="0.5" />
      {/* Pommel — small endcap */}
      <rect
        x="16"
        y="44"
        width="8"
        height="3"
        rx="1"
        stroke="currentColor"
        strokeWidth="1"
        fill="currentColor"
        fillOpacity="0.2"
      />
      {/* Head — blocky Mjolnir shape */}
      <rect
        x="4"
        y="6"
        width="32"
        height="18"
        rx="1"
        stroke="currentColor"
        strokeWidth="2"
        fill="currentColor"
        fillOpacity="0.15"
      />
      {/* Head — inner face plate */}
      <rect
        x="7"
        y="9"
        width="26"
        height="12"
        rx="0.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="0.75"
        opacity="0.4"
      />
      {/* Striking face — left flat edge */}
      <line x1="4" y1="8" x2="4" y2="22" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      {/* Striking face — right flat edge */}
      <line x1="36" y1="8" x2="36" y2="22" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      {/* Technical markings — crosshair on head */}
      <line x1="14" y1="15" x2="26" y2="15" stroke="currentColor" strokeWidth="0.75" opacity="0.5" />
      <line x1="20" y1="10" x2="20" y2="20" stroke="currentColor" strokeWidth="0.75" opacity="0.5" />
      {/* Corner brackets on head */}
      <path
        d="M8 10 L8 8 L10 8"
        stroke="currentColor"
        strokeWidth="1"
        fill="none"
        opacity="0.6"
        strokeLinecap="round"
      />
      <path
        d="M32 10 L32 8 L30 8"
        stroke="currentColor"
        strokeWidth="1"
        fill="none"
        opacity="0.6"
        strokeLinecap="round"
      />
      <path
        d="M8 20 L8 22 L10 22"
        stroke="currentColor"
        strokeWidth="1"
        fill="none"
        opacity="0.6"
        strokeLinecap="round"
      />
      <path
        d="M32 20 L32 22 L30 22"
        stroke="currentColor"
        strokeWidth="1"
        fill="none"
        opacity="0.6"
        strokeLinecap="round"
      />
      {/* Rune / tech glyph — center of head */}
      <circle cx="20" cy="15" r="3" stroke="currentColor" strokeWidth="1" fill="none" opacity="0.5" />
      <circle cx="20" cy="15" r="1" fill="currentColor" opacity="0.6" />
    </svg>
  );
}

function CrosshairIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <line
        x1="10"
        y1="3"
        x2="10"
        y2="7"
        stroke="#f59e0b"
        strokeWidth="1"
        opacity="0.5"
        strokeLinecap="round"
      />
      <line
        x1="10"
        y1="13"
        x2="10"
        y2="17"
        stroke="#f59e0b"
        strokeWidth="1"
        opacity="0.5"
        strokeLinecap="round"
      />
      <line
        x1="3"
        y1="10"
        x2="7"
        y2="10"
        stroke="#f59e0b"
        strokeWidth="1"
        opacity="0.5"
        strokeLinecap="round"
      />
      <line
        x1="13"
        y1="10"
        x2="17"
        y2="10"
        stroke="#f59e0b"
        strokeWidth="1"
        opacity="0.5"
        strokeLinecap="round"
      />
      <circle cx="10" cy="10" r="1.5" stroke="#f59e0b" strokeWidth="0.75" fill="none" opacity="0.4" />
    </svg>
  );
}

function MissX() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-red-500" aria-hidden="true">
      <line x1="3" y1="3" x2="13" y2="13" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="13" y1="3" x2="3" y2="13" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Inline CSS keyframes (prefixed wam- to avoid collisions)
// ---------------------------------------------------------------------------

const WAM_STYLES = `
@keyframes wam-pop-up {
  from { transform: translateY(100%); opacity: 0; }
  to   { transform: translateY(15%);  opacity: 1; }
}
@keyframes wam-duck-down {
  from { transform: translateY(15%);  opacity: 1; }
  to   { transform: translateY(100%); opacity: 0; }
}
@keyframes wam-hammer-emerge {
  0%   { transform: scale(0.01); }
  15%  { transform: scale(1.15); }
  35%  { transform: scale(1.05); }
  70%  { transform: scale(1.0); }
  100% { transform: scale(0.01); }
}
@keyframes wam-hammer-rotate {
  0%   { transform: rotate(-45deg); }
  15%  { transform: rotate(-50deg); }
  35%  { transform: rotate(75deg); }
  50%  { transform: rotate(65deg); }
  70%  { transform: rotate(-15deg); }
  100% { transform: rotate(-45deg); }
}
@keyframes wam-splat {
  from { transform: scale(0.3); opacity: 0.9; }
  to   { transform: scale(2.5); opacity: 0; }
}
@keyframes wam-impact-shake {
  0%, 100% { transform: translate(0, 0); }
  20% { transform: translate(-3px, 2px); }
  40% { transform: translate(3px, -3px); }
  60% { transform: translate(-2px, -2px); }
  80% { transform: translate(2px, 1px); }
}
@keyframes wam-impact-flash {
  from { opacity: 0.6; }
  to { opacity: 0; }
}
@keyframes wam-sign-shake {
  0%   { transform: rotate(0deg); }
  10%  { transform: rotate(-6deg); }
  20%  { transform: rotate(6deg); }
  30%  { transform: rotate(-5deg); }
  40%  { transform: rotate(5deg); }
  50%  { transform: rotate(-3deg); }
  60%  { transform: rotate(3deg); }
  70%  { transform: rotate(-1.5deg); }
  80%  { transform: rotate(1.5deg); }
  90%  { transform: rotate(-0.5deg); }
  100% { transform: rotate(0deg); }
}
@keyframes wam-sign-rock {
  0%, 100% { transform: rotate(-3deg); }
  50%      { transform: rotate(3deg); }
}
@keyframes wam-page-shake {
  0%, 100% { transform: translate(0, 0); }
  10% { transform: translate(-4px, 3px); }
  20% { transform: translate(4px, -3px); }
  30% { transform: translate(-3px, -4px); }
  40% { transform: translate(3px, 4px); }
  50% { transform: translate(-2px, 2px); }
  60% { transform: translate(2px, -2px); }
  70% { transform: translate(-1px, 1px); }
  80% { transform: translate(1px, -1px); }
}
@keyframes wam-red-flash {
  0% { opacity: 0.4; }
  100% { opacity: 0; }
}
@keyframes wam-miss-flash {
  0%   { opacity: 1; transform: scale(1); }
  100% { opacity: 0; transform: scale(1.5); }
}
@keyframes wam-score-bump {
  0%, 100% { transform: scale(1); }
  50%      { transform: scale(1.2); }
}
@keyframes wam-ripple {
  from { transform: scaleX(0) scaleY(0); opacity: 0.7; }
  to   { transform: scaleX(5) scaleY(2); opacity: 0; }
}
@keyframes wam-hit-rise {
  0%   { transform: translateY(0) scale(0.6); opacity: 1; }
  15%  { transform: translateY(-6px) scale(1.15); opacity: 1; }
  40%  { opacity: 1; }
  100% { transform: translateY(-52px) scale(1); opacity: 0; }
}
@keyframes wam-slow-rise {
  from { transform: translateY(100%); opacity: 0; }
  to   { transform: translateY(15%);  opacity: 1; }
}
@keyframes wam-blackout {
  from { opacity: 0; }
  to   { opacity: 1; }
}
@keyframes wam-sign-rise {
  from { transform: translateY(60px); opacity: 0; }
  to   { transform: translateY(0); opacity: 1; }
}
@keyframes wam-tilt-left {
  from { transform: rotate(0deg); }
  to   { transform: rotate(15deg); }
}
@keyframes wam-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }
}
@keyframes wam-flicker {
  0%, 100% { border-color: #525252; }
  20% { border-color: #ef4444; }
  40% { border-color: #525252; }
  60% { border-color: #ef4444; }
  80% { border-color: #525252; }
}
.wam-pop-up      { animation: wam-pop-up 500ms ease-out forwards; }
.wam-duck-down   { animation: wam-duck-down 400ms ease-in forwards; }
.wam-hammer-idle    { transform: scale(0.01); transform-origin: 0px 0px; }
.wam-hammer-emerge  { animation: wam-hammer-emerge 400ms ease-out forwards; transform-origin: 0px 0px; }
.wam-hammer-rest    { transform: rotate(-45deg); transform-origin: bottom center; }
.wam-hammer-rotate  { animation: wam-hammer-rotate 400ms ease-out forwards; transform-origin: bottom center; }
.wam-splat       { animation: wam-splat 400ms ease-out forwards; }
.wam-hit-rise    { animation: wam-hit-rise 900ms ease-out forwards; }
.wam-miss-flash  { animation: wam-miss-flash 250ms ease-out forwards; }
.wam-score-bump  { animation: wam-score-bump 150ms ease-out; }
.wam-ripple      { animation: wam-ripple 600ms ease-out forwards; }
.wam-slow-rise   { animation: wam-slow-rise 600ms ease-out forwards; }
.wam-blackout    { animation: wam-blackout 800ms ease-in forwards; }
.wam-sign-rise   { animation: wam-sign-rise 500ms ease-out forwards; }
.wam-tilt-left   { animation: wam-tilt-left 300ms ease-out forwards; }
.wam-blink       { animation: wam-blink 600ms ease-in-out infinite; }
.wam-flicker     { animation: wam-flicker 600ms linear forwards; }
.wam-fade-in-late { animation: wam-blackout 400ms ease-out 1.8s both; }
.wam-impact-shake { animation: wam-impact-shake 250ms ease-out; }
.wam-impact-flash { animation: wam-impact-flash 200ms ease-out forwards; }
.wam-sign-wave    { animation: wam-sign-shake 800ms ease-out, wam-sign-rock 2.5s ease-in-out 800ms infinite; transform-origin: center bottom; }
.wam-page-shake   { animation: wam-page-shake 300ms ease-out; }
.wam-red-flash    { animation: wam-red-flash 500ms ease-out forwards; }
@media (prefers-reduced-motion: reduce) {
  .wam-pop-up,
  .wam-duck-down,
  .wam-hammer-emerge,
  .wam-hammer-rotate,
  .wam-splat,
  .wam-hit-rise,
  .wam-miss-flash,
  .wam-score-bump,
  .wam-ripple,
  .wam-slow-rise,
  .wam-blackout,
  .wam-sign-rise,
  .wam-tilt-left,
  .wam-blink,
  .wam-flicker,
  .wam-impact-shake,
  .wam-impact-flash,
  .wam-sign-wave,
  .wam-page-shake,
  .wam-red-flash,
  .wam-fade-in-late {
    animation-duration: 0.01s !important;
  }
}
`;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmtScore(n: number): string {
  return String(n).padStart(3, '0');
}

// ---------------------------------------------------------------------------
// Evasive "I WANT BACK" button — dodges the cursor
// ---------------------------------------------------------------------------

function EvasiveButton() {
  const [pos, setPos] = useState({ x: 50, y: 78 });

  const evade = useCallback(() => {
    setPos(() => ({
      x: 8 + Math.random() * 84,
      y: 18 + Math.random() * 68,
    }));
  }, []);

  return (
    <div
      className="absolute wam-fade-in-late"
      style={{
        left: `${pos.x}%`,
        top: `${pos.y}%`,
        transform: 'translate(-50%, -50%)',
        transition: 'left 180ms ease-out, top 180ms ease-out',
        padding: '28px',
        zIndex: 10,
      }}
      onPointerEnter={evade}
    >
      <button
        type="button"
        className="
          font-mono text-xs sm:text-sm uppercase tracking-widest
          px-4 py-2
          border border-neutral-600 text-neutral-400
          bg-neutral-900/80
          hover:text-emerald-400 hover:border-emerald-400
          transition-colors cursor-pointer
          whitespace-nowrap
        "
        onClick={evade}
        aria-label="I want back (this button evades your cursor)"
      >
        I WANT BACK
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function WhackAMole({ holeCount = DEFAULT_HOLES, className = '' }: WhackAMoleProps) {
  const [state, dispatch] = useReducer(reducer, holeCount, initState);
  const [highScore, setHighScore] = useState(() => readHigh());
  const [warning, setWarning] = useState<{ message: string; color: string; flash: boolean } | null>(null);
  const [monsterWarning, setMonsterWarning] = useState(false);
  const [doomStep, setDoomStep] = useState(0);

  const stateRef = useRef(state);
  stateRef.current = state;

  const timeoutsRef = useRef(new Set<ReturnType<typeof setTimeout>>());
  const hitPosRef = useRef(new Map<number, { x: number; y: number }>());
  const molePopCountRef = useRef(0);
  const cumulativeHitsRef = useRef(0);
  const lastHitHoleRef = useRef(8);
  const doomStepRef = useRef(0);
  const doomTimeoutsRef = useRef(new Set<ReturnType<typeof setTimeout>>());
  const gameContainerRef = useRef<HTMLDivElement>(null);
  const hammerRef = useRef<HTMLDivElement>(null);
  const hammerInnerRef = useRef<HTMLDivElement>(null);
  const hammerScaleRef = useRef<HTMLDivElement>(null);
  const ripplesContainerRef = useRef<HTMLDivElement>(null);
  const gameRectRef = useRef<DOMRect | null>(null);

  // -- timeout helpers ------------------------------------------------------

  const schedule = useCallback((cb: () => void, ms: number) => {
    const id = setTimeout(() => {
      timeoutsRef.current.delete(id);
      cb();
    }, ms);
    timeoutsRef.current.add(id);
    return id;
  }, []);

  const clearTimeouts = useCallback(() => {
    timeoutsRef.current.forEach(clearTimeout);
    timeoutsRef.current.clear();
  }, []);

  // -- effects --------------------------------------------------------------

  // Cleanup on unmount
  useEffect(() => clearTimeouts, [clearTimeouts]);

  // Mole spawner — runs when phase is 'playing'
  useEffect(() => {
    if (state.phase !== 'playing') return;
    let cancelled = false;

    const spawn = () => {
      const cur = stateRef.current;
      if (cur.phase !== 'playing' || cancelled) return;

      const upCount = cur.holes.filter((h) => h.status === 'up').length;
      if (upCount >= MAX_MOLES) return;

      const empty: number[] = [];
      cur.holes.forEach((h, i) => {
        if (h.status === 'empty') empty.push(i);
      });
      if (empty.length === 0) return;

      const idx = empty[Math.floor(Math.random() * empty.length)];

      molePopCountRef.current += 1;
      const variant: 'mole' | 'mother' = molePopCountRef.current % 5 === 0 ? 'mother' : 'mole';

      dispatch({ type: 'MOLE_UP', index: idx, variant });

      schedule(() => {
        dispatch({ type: 'MOLE_DOWN', index: idx });
        schedule(() => dispatch({ type: 'CLEAR_HOLE', index: idx }), MISS_CLEAR_MS);
      }, MOLE_VISIBLE_MS);
    };

    const loop = () => {
      if (cancelled || stateRef.current.phase !== 'playing') return;
      schedule(() => {
        if (cancelled || stateRef.current.phase !== 'playing') return;
        spawn();
        loop();
      }, SPAWN_INTERVAL_MS);
    };

    schedule(() => {
      if (cancelled) return;
      spawn();
      loop();
    }, FIRST_SPAWN_MS);

    return () => {
      cancelled = true;
    };
  }, [state.phase, schedule]);

  // Clear pending timeouts when leaving playing phase
  useEffect(() => {
    if (state.phase !== 'playing') clearTimeouts();
  }, [state.phase, clearTimeouts]);

  // Persist high score when it changes
  useEffect(() => {
    if (state.score > highScore) {
      writeHigh(state.score);
      setHighScore(state.score);
    }
  }, [state.score, highScore]);

  // -- doomsday sequence effect ---------------------------------------------

  useEffect(() => {
    if (state.phase !== 'doomsday') return;
    if (doomStepRef.current !== 0) return;

    const tracked = doomTimeoutsRef.current;
    const scheduleDoom = (cb: () => void, ms: number) => {
      const id = setTimeout(() => {
        tracked.delete(id);
        cb();
      }, ms);
      tracked.add(id);
    };

    // Step 1: mascot rises from last hit hole
    // Step 2: mascot tilts + INITIATING SHUTDOWN text
    // Step 3: screen flickers red
    // Step 4: full blackout overlay
    setDoomStep(1);
    doomStepRef.current = 1;

    scheduleDoom(() => {
      setDoomStep(2);
      doomStepRef.current = 2;
    }, 800);
    scheduleDoom(() => {
      setDoomStep(3);
      doomStepRef.current = 3;
    }, 1600);
    scheduleDoom(() => {
      setDoomStep(4);
      doomStepRef.current = 4;
    }, 2200);

    return () => {
      tracked.forEach(clearTimeout);
      tracked.clear();
    };
  }, [state.phase]);

  // -- handlers -------------------------------------------------------------

  const handleWhack = useCallback(
    (index: number, x?: number, y?: number) => {
      if (stateRef.current.phase !== 'playing') return;
      if (stateRef.current.holes[index].status !== 'up') return;

      const hole = stateRef.current.holes[index];

      if (x !== undefined && y !== undefined) {
        hitPosRef.current.set(index, { x, y });
      }

      dispatch({ type: 'WHACK', index });

      // Page shake on every hit
      const container = gameContainerRef.current;
      if (container) {
        container.getAnimations().forEach((a) => {
          if (a instanceof CSSAnimation && a.animationName === 'wam-page-shake') a.cancel();
        });
        container.animate(
          [
            { transform: 'translate(0, 0)' },
            { transform: 'translate(-3px, 2px)', offset: 0.2 },
            { transform: 'translate(3px, -3px)', offset: 0.4 },
            { transform: 'translate(-2px, -2px)', offset: 0.6 },
            { transform: 'translate(2px, 1px)', offset: 0.8 },
            { transform: 'translate(0, 0)' },
          ],
          { duration: 250, easing: 'ease-out' },
        );
      }

      if (hole.variant === 'mother') {
        // Mother hit — delay overlay so splat/shake play out first
        schedule(() => {
          setMonsterWarning(true);
          schedule(() => setMonsterWarning(false), MONSTER_DURATION_MS);
        }, 600);
      } else {
        // Mole hit — increment cumulative hits, check warnings/doom
        lastHitHoleRef.current = index;
        cumulativeHitsRef.current += 1;
        const hits = cumulativeHitsRef.current;

        if (hits >= 10) {
          // Trigger doomsday
          schedule(() => dispatch({ type: 'DOOM' }), HIT_CLEAR_MS + 100);
        } else {
          // Check for warnings
          const threshold = WARNING_THRESHOLDS.find((t) => t.hits === hits);
          if (threshold) {
            setWarning({
              message: threshold.message,
              color: threshold.color,
              flash: threshold.flash,
            });
            schedule(() => setWarning(null), WARNING_DURATION_MS);
          }
        }
      }

      schedule(() => {
        dispatch({ type: 'CLEAR_HOLE', index });
        hitPosRef.current.delete(index);
      }, HIT_CLEAR_MS);
    },
    [schedule],
  );

  // -- native mouse & click listeners (zero React overhead) -------------------

  useEffect(() => {
    const container = gameContainerRef.current;
    if (!container) return;

    const onEnter = (e: MouseEvent) => {
      gameRectRef.current = container.getBoundingClientRect();
      const hammer = hammerRef.current;
      if (hammer && gameRectRef.current) {
        const r = gameRectRef.current;
        hammer.style.transform = `translate3d(${e.clientX - r.left}px,${e.clientY - r.top}px,0)`;
        hammer.style.opacity = '1';
      }
    };

    const onLeave = () => {
      if (hammerRef.current) hammerRef.current.style.opacity = '0';
    };

    const onMove = (e: MouseEvent) => {
      const hammer = hammerRef.current;
      const r = gameRectRef.current;
      if (!hammer || !r) return;
      hammer.style.transform = `translate3d(${e.clientX - r.left}px,${e.clientY - r.top}px,0)`;
    };

    const onClick = (e: MouseEvent) => {
      if (stateRef.current.phase !== 'playing') return;
      const r = gameRectRef.current;
      const rc = ripplesContainerRef.current;
      if (r && rc) {
        const cx = e.clientX - r.left;
        const cy = e.clientY - r.top;
        // Expanding ring
        const ring = document.createElement('div');
        ring.className = 'absolute pointer-events-none wam-ripple';
        ring.style.cssText =
          `left:${cx}px;top:${cy}px;` +
          'width:64px;height:20px;margin-left:-32px;margin-top:-10px;' +
          'border-radius:50%;border:2px solid #f59e0b;';
        rc.appendChild(ring);
        ring.addEventListener('animationend', () => ring.remove(), { once: true });
        // Center dot — marks exact click point
        const dot = document.createElement('div');
        dot.className = 'absolute pointer-events-none';
        dot.style.cssText =
          `left:${cx}px;top:${cy}px;` +
          'width:6px;height:6px;margin-left:-3px;margin-top:-3px;' +
          'border-radius:50%;background:#f59e0b;';
        rc.appendChild(dot);
        setTimeout(() => dot.remove(), 600);
      }
      const scale = hammerScaleRef.current;
      const inner = hammerInnerRef.current;
      if (scale && inner) {
        scale.getAnimations().forEach((a) => a.cancel());
        inner.getAnimations().forEach((a) => a.cancel());
        scale.animate(
          [
            { transform: 'scale(0.01)', offset: 0 },
            { transform: 'scale(1.15)', offset: 0.15 },
            { transform: 'scale(1.05)', offset: 0.35 },
            { transform: 'scale(1.0)', offset: 0.7 },
            { transform: 'scale(0.01)', offset: 1 },
          ],
          { duration: 400, easing: 'ease-out', fill: 'forwards' },
        );
        inner.animate(
          [
            { transform: 'rotate(-45deg)', offset: 0 },
            { transform: 'rotate(-50deg)', offset: 0.15 },
            { transform: 'rotate(75deg)', offset: 0.35 },
            { transform: 'rotate(65deg)', offset: 0.5 },
            { transform: 'rotate(-15deg)', offset: 0.7 },
            { transform: 'rotate(-45deg)', offset: 1 },
          ],
          { duration: 400, easing: 'ease-out', fill: 'forwards' },
        );
      }
    };

    container.addEventListener('mouseenter', onEnter);
    container.addEventListener('mouseleave', onLeave);
    container.addEventListener('mousemove', onMove, { passive: true });
    container.addEventListener('click', onClick);
    return () => {
      container.removeEventListener('mouseenter', onEnter);
      container.removeEventListener('mouseleave', onLeave);
      container.removeEventListener('mousemove', onMove);
      container.removeEventListener('click', onClick);
    };
  }, []);

  // Hide hammer when leaving playing phase
  useEffect(() => {
    if (state.phase !== 'playing' && hammerRef.current) {
      hammerRef.current.style.opacity = '0';
    }
  }, [state.phase]);

  // -- keyboard input (a-l hole keys) ----------------------------------------

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      const holeIndex = HOLE_KEYS.indexOf(e.key.toLowerCase() as (typeof HOLE_KEYS)[number]);
      if (holeIndex !== -1) {
        e.preventDefault();
        handleWhack(holeIndex);
      }
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleWhack]);

  // -- derived --------------------------------------------------------------

  const playing = state.phase === 'playing';
  const isDoom = state.phase === 'doomsday';

  // Bottom bar content
  const bottomMessage = (() => {
    if (isDoom && doomStep >= 2) {
      return (
        <span className="font-mono uppercase tracking-widest text-red-500 font-bold wam-blink text-lg sm:text-xl">
          INITIATING SHUTDOWN...
        </span>
      );
    }
    if (monsterWarning) return null;
    if (warning) {
      return (
        <span
          className={`font-mono uppercase tracking-widest ${warning.color} font-bold ${warning.flash ? 'wam-blink' : ''} text-lg sm:text-2xl`}
        >
          {warning.message}
        </span>
      );
    }
    return (
      <div className="font-mono select-none" style={{ perspective: '200px' }}>
        <div
          className="relative border border-neutral-800/40 px-6 py-3 sm:py-4 mx-auto max-w-sm"
          style={{
            transform: 'rotateX(14deg)',
            transformOrigin: 'center top',
            backgroundImage:
              'linear-gradient(90deg, rgba(82,82,82,0.06) 1px, transparent 1px),' +
              'linear-gradient(0deg, rgba(82,82,82,0.04) 1px, transparent 1px)',
            backgroundSize: '40px 12px',
          }}
        >
          {/* Corner brackets */}
          <div
            className="absolute top-1.5 left-1.5 w-2 h-2 border-t border-l border-neutral-700/30"
            aria-hidden="true"
          />
          <div
            className="absolute top-1.5 right-1.5 w-2 h-2 border-t border-r border-neutral-700/30"
            aria-hidden="true"
          />
          <div
            className="absolute bottom-1.5 left-1.5 w-2 h-2 border-b border-l border-neutral-700/30"
            aria-hidden="true"
          />
          <div
            className="absolute bottom-1.5 right-1.5 w-2 h-2 border-b border-r border-neutral-700/30"
            aria-hidden="true"
          />

          {/* Brand */}
          <p className="text-center text-sm text-neutral-500 uppercase tracking-[0.2em] leading-none mb-2">
            WHAT COULD GO WRONG?
          </p>
          {/* Tagline + copyright */}
          <div className="flex items-center justify-center gap-2 text-neutral-600 leading-none">
            <span className="text-[10px] uppercase tracking-wider">TOOLS FOR THE AFTERMATH</span>
            <span className="text-neutral-700/40 text-[9px]">│</span>
            <span className="text-[10px] tracking-wider">© {new Date().getFullYear()}</span>
          </div>
        </div>
      </div>
    );
  })();

  // -- render ---------------------------------------------------------------

  return (
    <>
      <style>{WAM_STYLES}</style>
      <div
        ref={gameContainerRef}
        role="region"
        aria-label="Whack-a-mole arcade game"
        className={`relative overflow-hidden ${className}`}
        style={playing ? { cursor: 'none' } : undefined}
      >
        {/* ── Hits counter (minimal, right-aligned) ──────────────── */}
        <div className="flex justify-end mb-1 font-mono text-xs uppercase tracking-widest text-neutral-500 tabular-nums">
          <span aria-live="polite">
            HITS:{' '}
            <span key={state.score} className={`text-neutral-200 ${playing ? 'wam-score-bump' : ''}`}>
              {fmtScore(state.score)}
            </span>
          </span>
        </div>

        {/* ── Game surface + Holes ──────────────────────────────── */}
        <div
          className={`
            relative flex items-end justify-between w-full py-3 sm:py-4
            ${isDoom && doomStep === 3 ? 'wam-flicker border border-neutral-700' : ''}
          `}
        >
          {/* Vaporwave perspective grid — computed from hole positions */}
          {/* SVG is 200% container width. Container maps to viewBox 450–1350. */}
          {/* Vertical lines placed at exact hole boundaries, extended outward. */}
          {(() => {
            const VW = 1800;
            const VH = 300;
            const VPX = VW / 2; // vanishing point x = 900
            const VPY = -200; // vanishing point y (above viewport)
            const CL = VW / 4; // container left in viewBox = 450
            const CR = (3 * VW) / 4; // container right = 1350
            const CELL = (CR - CL) / holeCount; // cell width = 100
            const D = VH - VPY; // denominator = 500
            const R = (0 - VPY) / D; // convergence ratio = 0.4

            // Vertical lines: hole boundaries + 5 extra each side
            const vLines: Array<{ xTop: number; xBot: number; edge: boolean }> = [];
            for (let col = -5; col <= holeCount + 5; col++) {
              const xBot = CL + col * CELL;
              if (xBot < -50 || xBot > VW + 50) continue;
              const xTop = VPX + (xBot - VPX) * R;
              const edge = col < 0 || col > holeCount;
              vLines.push({ xTop, xBot, edge });
            }

            // Horizontal lines: perspective-spaced (power curve)
            const HCOUNT = 12;
            const hLines: Array<{ y: number; xL: number; xR: number; t: number }> = [];
            for (let i = 1; i <= HCOUNT; i++) {
              const t = i / HCOUNT;
              const y = VH * Math.pow(t, 1.8);
              const f = (y - VPY) / D;
              const xL = VPX + (0 - VPX) * f;
              const xR = VPX + (VW - VPX) * f;
              hLines.push({ y, xL, xR, t });
            }

            return (
              <svg
                className="absolute pointer-events-none"
                style={{ left: '-50%', width: '200%', top: '-8px', bottom: '-48px', zIndex: 0 }}
                viewBox={`0 0 ${VW} ${VH}`}
                preserveAspectRatio="none"
                aria-hidden="true"
              >
                <defs>
                  <linearGradient id="wam-grid-fade" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="white" stopOpacity="0.4" />
                    <stop offset="30%" stopColor="white" stopOpacity="1" />
                    <stop offset="75%" stopColor="white" stopOpacity="0.8" />
                    <stop offset="100%" stopColor="white" stopOpacity="0" />
                  </linearGradient>
                  <mask id="wam-grid-mask">
                    <rect x="0" y="0" width={VW} height={VH} fill="url(#wam-grid-fade)" />
                  </mask>
                </defs>
                <g mask="url(#wam-grid-mask)" stroke="#525252" fill="none">
                  {vLines.map((l, i) => (
                    <line
                      key={`v${i}`}
                      x1={l.xTop}
                      y1={0}
                      x2={l.xBot}
                      y2={VH}
                      strokeWidth="0.8"
                      opacity={l.edge ? '0.12' : '0.20'}
                    />
                  ))}
                  {hLines.map((l, i) => (
                    <line
                      key={`h${i}`}
                      x1={l.xL}
                      y1={l.y}
                      x2={l.xR}
                      y2={l.y}
                      strokeWidth={l.t < 0.35 ? '0.6' : '0.8'}
                      opacity={String((0.1 + 0.1 * l.t).toFixed(2))}
                    />
                  ))}
                </g>
              </svg>
            );
          })()}
          {state.holes.map((hole, i) => {
            const up = hole.status === 'up';
            const whacked = hole.status === 'whacked';
            const missed = hole.status === 'missed';
            const visible = up || whacked || missed;

            const animCls = up ? 'wam-pop-up' : missed ? 'wam-duck-down' : '';

            const hitPos = whacked ? hitPosRef.current.get(i) : undefined;

            // Doomsday intro: mascot in last hit hole (step 1+)
            const showDoomMascot = isDoom && doomStep >= 1 && i === lastHitHoleRef.current;

            return (
              <button
                key={i}
                type="button"
                onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  handleWhack(i, e.clientX - rect.left, e.clientY - rect.top);
                }}
                disabled={!playing}
                aria-label={`Hole ${i + 1}${up ? ', mole visible' : ''}`}
                style={{ cursor: 'inherit' }}
                className={`
                  relative flex flex-col items-center flex-1 min-w-0
                  bg-transparent border-0 outline-none
                  focus-visible:ring-2 focus-visible:ring-emerald-400
                  focus-visible:ring-offset-1 focus-visible:ring-offset-neutral-950
                  transition-colors
                `}
              >
                {/* Mole + hole container */}
                <div className={`relative w-14 h-16 sm:w-16 sm:h-20 ${whacked ? 'wam-impact-shake' : ''}`}>
                  {/* Mole area — overflow hidden clips the pop-up */}
                  <div className="absolute inset-x-0 top-0 bottom-[3px] overflow-hidden flex items-end justify-center">
                    {visible && (
                      <div className={`relative ${animCls}`} data-mole>
                        {hole.variant === 'mother' ? (
                          <MotherAndBaby hit={whacked} />
                        ) : (
                          <WcgwMole hit={whacked} />
                        )}
                      </div>
                    )}
                    {/* Doomsday: mascot slow rise, tilts at step 2 */}
                    {showDoomMascot && (
                      <div className={`wam-slow-rise ${doomStep >= 2 ? 'wam-tilt-left' : ''}`}>
                        <WcgwMole />
                      </div>
                    )}
                  </div>

                  {/* Impact flash — bright amber overlay on hit */}
                  {whacked && (
                    <div
                      className="absolute inset-0 pointer-events-none wam-impact-flash"
                      style={{
                        background: 'radial-gradient(circle, rgba(245,158,11,0.5) 0%, transparent 70%)',
                      }}
                    />
                  )}

                  {/* Miss indicator */}
                  {missed && (
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none wam-miss-flash">
                      <MissX />
                    </div>
                  )}

                  {/* Hole ellipse */}
                  <svg
                    className="absolute bottom-0 left-1/2 -translate-x-1/2"
                    width="56"
                    height="16"
                    viewBox="0 0 56 16"
                    aria-hidden="true"
                  >
                    <ellipse
                      cx="28"
                      cy="8"
                      rx="24"
                      ry="6.5"
                      stroke={whacked ? '#ef4444' : '#525252'}
                      strokeWidth="1.5"
                      strokeDasharray="4 3"
                      fill="none"
                      opacity={whacked ? '0.8' : '0.6'}
                    />
                  </svg>
                </div>

                {/* Hit splat — positioned at click point, relative to button */}
                {whacked && (
                  <div
                    className="absolute pointer-events-none wam-splat"
                    style={
                      hitPos
                        ? { left: hitPos.x, top: hitPos.y, transform: 'translate(-50%, -50%)' }
                        : { left: '50%', top: '35%', transform: 'translate(-50%, -50%)' }
                    }
                  >
                    <SplatEffect />
                  </div>
                )}

                {/* Floating +1 — rises and fades from mole center */}
                {whacked && hole.variant === 'mole' && (
                  <div
                    className="absolute left-1/2 pointer-events-none wam-hit-rise"
                    style={{ top: '4px', transform: 'translateX(-50%)' }}
                  >
                    <span
                      className="font-mono text-2xl sm:text-3xl font-bold text-amber-400"
                      style={{ textShadow: '0 0 10px rgba(245,158,11,0.7), 0 0 24px rgba(245,158,11,0.3)' }}
                    >
                      +1
                    </span>
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* ── Bottom bar ─────────────────────────────────────────── */}
        <div className="flex items-center justify-center mt-2">{bottomMessage}</div>

        {/* Ripple container — children created/removed via native DOM */}
        <div ref={ripplesContainerRef} className="absolute inset-0 pointer-events-none overflow-hidden" />

        {/* Following hammer — position/opacity driven by native listeners */}
        <div
          ref={hammerRef}
          className="absolute left-0 top-0 pointer-events-none"
          style={{ zIndex: 40, opacity: 0, contain: 'layout style' }}
        >
          {/* Crosshair at exact strike point */}
          <div className="absolute left-0 top-0" style={{ transform: 'translate(-50%, -50%)' }}>
            <CrosshairIcon />
          </div>
          {/* Hammer visual — two-layer: outer scales from crosshair origin, inner rotates from handle */}
          <div ref={hammerScaleRef} className="wam-hammer-idle">
            <div className="absolute left-0 top-0" style={{ transform: 'translate(-125%, -108%)' }}>
              <div ref={hammerInnerRef} className="wam-hammer-rest">
                <HammerIcon />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Full-screen YOU MONSTER overlay when mother is hit ── */}
      {monsterWarning && (
        <div
          className="fixed inset-0 flex flex-col items-center justify-center"
          style={{
            zIndex: 10049,
            backgroundColor: 'rgba(10, 10, 10, 0.94)',
          }}
        >
          {/* Top hazard stripe */}
          <div
            className="absolute top-0 left-0 right-0"
            aria-hidden="true"
            style={{
              height: '40px',
              backgroundImage:
                'repeating-linear-gradient(-45deg, #b91c1c 0, #b91c1c 16px, #1a1a1a 16px, #1a1a1a 32px)',
              opacity: 0.8,
            }}
          />
          {/* Bottom hazard stripe */}
          <div
            className="absolute bottom-0 left-0 right-0"
            aria-hidden="true"
            style={{
              height: '40px',
              backgroundImage:
                'repeating-linear-gradient(-45deg, #b91c1c 0, #b91c1c 16px, #1a1a1a 16px, #1a1a1a 32px)',
              opacity: 0.8,
            }}
          />
          {/* Thin red border glow on all edges */}
          <div
            className="absolute inset-0 pointer-events-none"
            aria-hidden="true"
            style={{ boxShadow: 'inset 0 0 80px rgba(185, 28, 28, 0.3)' }}
          />
          <span className="font-mono uppercase tracking-widest text-red-500 font-bold wam-blink text-5xl sm:text-7xl">
            YOU MONSTER!
          </span>
        </div>
      )}

      {/* ── Full-page doomsday overlay — permanent, semi-transparent ── */}
      {doomStep >= 4 && (
        <div
          aria-label="System offline"
          className="fixed inset-0 flex items-center justify-center wam-blackout"
          style={{
            zIndex: 2147483647,
            backgroundColor: 'rgba(0, 0, 0, 0.98)',
            background:
              'radial-gradient(ellipse 320px 400px at center, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.95) 40%, rgba(0,0,0,0.98) 100%)',
          }}
        >
          {/* Spotlight cone — soft light from above */}
          <div
            className="absolute pointer-events-none"
            style={{
              width: '300px',
              height: '500px',
              left: '50%',
              top: '0',
              transform: 'translateX(-50%)',
              background:
                'linear-gradient(180deg, rgba(245,158,11,0.08) 0%, rgba(245,158,11,0.03) 40%, transparent 80%)',
              clipPath: 'polygon(40% 0%, 60% 0%, 75% 100%, 25% 100%)',
            }}
          />
          {/* Soft glow around mascot */}
          <div
            className="absolute pointer-events-none"
            style={{
              width: '280px',
              height: '280px',
              left: '50%',
              top: '50%',
              transform: 'translate(-50%, -50%)',
              borderRadius: '50%',
              background:
                'radial-gradient(circle, rgba(52,211,153,0.06) 0%, rgba(52,211,153,0.02) 40%, transparent 70%)',
            }}
          />
          <div className="relative wam-sign-rise">
            <div className="wam-sign-wave">
              <DoomMascotWithSign />
            </div>
          </div>

          {/* Evasive restart button — dodges the cursor */}
          <EvasiveButton />
        </div>
      )}
    </>
  );
}
