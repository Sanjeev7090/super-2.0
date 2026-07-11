import React from 'react';

/**
 * Stock-market style Bull & Bear SVG icons.
 * Charging Bull (right-facing) + Standing Bear (left-facing) — classic Wall-Street silhouettes.
 * `size` accepts any CSS length. `className` allows external styling.
 * Colors are driven by `currentColor` on strokes and inline `fill` on shapes,
 * so callers can control tint via CSS `color` or the `fill` prop.
 */

const defaultBullFill = '#00E676';
const defaultBearFill = '#FF3B30';

// ── Bull (charging right) ────────────────────────────────────────────
export const BullIcon = ({ size = 64, fill = defaultBullFill, className = '', style = {}, ...rest }) => (
  <svg
    viewBox="0 0 240 200"
    width={size}
    height={size}
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    style={{ display: 'block', overflow: 'visible', ...style }}
    aria-label="Bull"
    role="img"
    {...rest}
  >
    <defs>
      <linearGradient id="bullBodyGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%"  stopColor={fill} stopOpacity="1"    />
        <stop offset="60%" stopColor={fill} stopOpacity="0.85" />
        <stop offset="100%" stopColor="#000" stopOpacity="0.7" />
      </linearGradient>
      <linearGradient id="bullHornGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%"  stopColor="#FFF7D6" />
        <stop offset="100%" stopColor="#E0C070" />
      </linearGradient>
    </defs>
    {/* Tail flicked up */}
    <path
      d="M20,90 C10,70 8,55 18,45 L24,50 C22,60 26,75 32,90 Z"
      fill="url(#bullBodyGrad)"
    />
    {/* Main body (torso) */}
    <path
      d="M28,90
         C28,72 40,60 60,58
         L140,58
         C160,58 178,66 190,80
         L200,102
         L188,108
         L182,120
         L172,120
         L170,108
         L156,108
         L154,140
         L142,140
         L140,108
         L96,108
         L94,140
         L82,140
         L84,108
         L58,108
         L48,132
         L38,132
         L44,108
         L30,102
         Z"
      fill="url(#bullBodyGrad)"
    />
    {/* Head — charging low, aggressive */}
    <path
      d="M180,64
         C202,60 224,66 232,84
         C238,98 232,116 218,122
         L200,124
         L192,110
         L188,96
         Z"
      fill="url(#bullBodyGrad)"
    />
    {/* Snout / nose */}
    <ellipse cx="228" cy="112" rx="8" ry="6" fill="#1a1a1a" opacity="0.85" />
    {/* Eye */}
    <circle cx="214" cy="86" r="2.5" fill="#000" />
    {/* Left horn — curves up and back */}
    <path
      d="M198,62
         C186,44 178,32 172,20
         L182,20
         L196,38
         L208,54
         Z"
      fill="url(#bullHornGrad)"
      stroke="#8B6914"
      strokeWidth="1"
    />
    {/* Right horn — curves up and forward */}
    <path
      d="M220,62
         C230,48 240,38 250,30
         L246,42
         L234,56
         L228,66
         Z"
      fill="url(#bullHornGrad)"
      stroke="#8B6914"
      strokeWidth="1"
    />
    {/* Ear (between horns) */}
    <ellipse cx="208" cy="64" rx="5" ry="8" fill={fill} opacity="0.7" />
    {/* Muscular shoulder highlight */}
    <path
      d="M148,60 C158,60 172,68 176,84 L162,90 L152,78 Z"
      fill="#fff" opacity="0.12"
    />
    {/* Ground shadow */}
    <ellipse cx="120" cy="152" rx="90" ry="6" fill="#000" opacity="0.15" />
  </svg>
);

// ── Bear (standing, roaring, left-facing) ────────────────────────────
export const BearIcon = ({ size = 64, fill = defaultBearFill, className = '', style = {}, ...rest }) => (
  <svg
    viewBox="0 0 240 200"
    width={size}
    height={size}
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    style={{ display: 'block', overflow: 'visible', ...style }}
    aria-label="Bear"
    role="img"
    {...rest}
  >
    <defs>
      <linearGradient id="bearBodyGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%"  stopColor={fill} stopOpacity="1"    />
        <stop offset="60%" stopColor={fill} stopOpacity="0.85" />
        <stop offset="100%" stopColor="#000" stopOpacity="0.75" />
      </linearGradient>
    </defs>

    {/* Standing torso — thick, wide, aggressive */}
    <path
      d="M92,80
         C82,78 74,88 72,102
         L68,140
         C68,156 76,168 92,170
         L156,170
         C172,168 180,156 180,140
         L176,102
         C174,88 166,78 156,80
         Z"
      fill="url(#bearBodyGrad)"
    />

    {/* Right arm raised (roaring pose) */}
    <path
      d="M170,90
         C186,84 200,74 208,58
         L216,68
         C210,84 198,102 184,110
         L172,106
         Z"
      fill="url(#bearBodyGrad)"
    />
    {/* Claws on right paw */}
    <path d="M212,54 L214,48 M216,58 L219,52 M220,62 L223,58"
          stroke="#F5F5F5" strokeWidth="2" strokeLinecap="round" fill="none" />

    {/* Left arm raised */}
    <path
      d="M78,90
         C62,84 48,74 40,58
         L32,68
         C38,84 50,102 64,110
         L76,106
         Z"
      fill="url(#bearBodyGrad)"
    />
    {/* Claws on left paw */}
    <path d="M36,54 L34,48 M32,58 L29,52 M28,62 L25,58"
          stroke="#F5F5F5" strokeWidth="2" strokeLinecap="round" fill="none" />

    {/* Feet */}
    <ellipse cx="96"  cy="176" rx="14" ry="8" fill="url(#bearBodyGrad)" />
    <ellipse cx="152" cy="176" rx="14" ry="8" fill="url(#bearBodyGrad)" />

    {/* Head — big rounded skull */}
    <ellipse cx="124" cy="60" rx="42" ry="36" fill="url(#bearBodyGrad)" />

    {/* Ears — rounded, prominent */}
    <circle cx="94"  cy="28" r="14" fill="url(#bearBodyGrad)" />
    <circle cx="154" cy="28" r="14" fill="url(#bearBodyGrad)" />
    {/* Inner ears */}
    <circle cx="94"  cy="30" r="6" fill="#3a1a1a" opacity="0.6" />
    <circle cx="154" cy="30" r="6" fill="#3a1a1a" opacity="0.6" />

    {/* Snout — pushed forward */}
    <ellipse cx="124" cy="78" rx="18" ry="12" fill={fill} opacity="0.75" />
    <ellipse cx="124" cy="72" rx="6" ry="4" fill="#1a1a1a" />

    {/* Eyes — small, mean */}
    <circle cx="110" cy="56" r="3.5" fill="#000" />
    <circle cx="138" cy="56" r="3.5" fill="#000" />
    <circle cx="111" cy="55" r="1"   fill="#FFF" />
    <circle cx="139" cy="55" r="1"   fill="#FFF" />

    {/* Mouth — snarling */}
    <path d="M114,86 Q124,94 134,86" stroke="#1a1a1a" strokeWidth="2" fill="none" strokeLinecap="round"/>
    <path d="M118,90 L118,94 M130,90 L130,94" stroke="#F5F5F5" strokeWidth="1.5" strokeLinecap="round"/>

    {/* Belly highlight */}
    <path
      d="M100,110 C104,140 140,146 148,110 L138,168 L110,168 Z"
      fill="#fff" opacity="0.08"
    />

    {/* Ground shadow */}
    <ellipse cx="120" cy="188" rx="70" ry="5" fill="#000" opacity="0.18" />
  </svg>
);

export default { BullIcon, BearIcon };
