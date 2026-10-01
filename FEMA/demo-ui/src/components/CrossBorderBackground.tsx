import React from 'react';

interface CrossBorderBackgroundProps {
  children?: React.ReactNode;
  className?: string;
}

/**
 * 24-spoke Ashoka Chakra vector SVG in authentic Navy Blue (#000080).
 * Centered in the middle white band of the Indian flag with all 24 spokes,
 * hub, and rim details clearly visible.
 */
const AshokaChakra: React.FC = () => (
  <svg
    viewBox="0 0 200 200"
    className="w-28 h-28 sm:w-36 sm:h-36 md:w-48 md:h-48 text-[#000080] drop-shadow-sm select-none"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    {/* Outer wheel rims */}
    <circle cx="100" cy="100" r="92" stroke="#000080" strokeWidth="5" />
    <circle cx="100" cy="100" r="85" stroke="#000080" strokeWidth="1.5" />

    {/* 24 decorative rim beads */}
    {Array.from({ length: 24 }).map((_, i) => {
      const angle = (i * 15 + 7.5) * (Math.PI / 180);
      const bx = 100 + 88.5 * Math.sin(angle);
      const by = 100 - 88.5 * Math.cos(angle);
      return <circle key={`dot-${i}`} cx={bx} cy={by} r="2" fill="#000080" />;
    })}

    {/* Inner hub ring & center point */}
    <circle cx="100" cy="100" r="22" stroke="#000080" strokeWidth="3" />
    <circle cx="100" cy="100" r="8" fill="#000080" />

    {/* 24 spokes radiating at 15 degree increments */}
    {Array.from({ length: 24 }).map((_, i) => (
      <g key={`spoke-${i}`} transform={`rotate(${i * 15} 100 100)`}>
        <line
          x1="100"
          y1="22"
          x2="100"
          y2="85"
          stroke="#000080"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
      </g>
    ))}
  </svg>
);

/**
 * 50-star canton vector SVG in authentic White (#FFFFFF).
 * 9 alternating rows (6, 5, 6, 5, 6, 5, 6, 5, 6 = 50 stars).
 */
const USStarCanton: React.FC = () => {
  const rows = [6, 5, 6, 5, 6, 5, 6, 5, 6];
  const starPolygon =
    '0,-4.5 1.3,-1.4 4.5,-1.4 1.9,0.5 2.9,3.5 0,1.6 -2.9,3.5 -1.9,0.5 -4.5,-1.4 -1.3,-1.4';

  return (
    <svg
      viewBox="0 0 280 180"
      className="w-full h-full select-none"
      fill="#FFFFFF"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      {rows.map((count, rowIndex) => {
        const y = 18 + (rowIndex * (180 - 36)) / 8;
        const xStep = (280 - 44) / 5;
        const xStart = count === 6 ? 22 : 22 + xStep / 2;
        return Array.from({ length: count }).map((_, starIndex) => {
          const x = xStart + starIndex * xStep;
          return (
            <polygon
              key={`${rowIndex}-${starIndex}`}
              points={starPolygon}
              transform={`translate(${x}, ${y})`}
            />
          );
        });
      })}
    </svg>
  );
};

/**
 * CrossBorderBackground
 * Reusable split background component with clearly recognizable national flag visuals:
 * - LEFT HALF: India 🇮🇳 (Saffron, White, Green bands with Navy Blue Ashoka Chakra)
 * - RIGHT HALF: USA 🇺🇸 (13 Red/White stripes with Blue canton and 50 White stars)
 * - CENTER: Soft gradual blend (no harsh vertical line)
 * - OVERLAY: Neutral dark overlay ensuring the UI remains dark and text/cards 100% readable.
 * - NO generic blue tint wash over the entire application.
 */
export const CrossBorderBackground: React.FC<CrossBorderBackgroundProps> = ({
  children,
  className = '',
}) => {
  return (
    <div
      className={`relative w-full h-full flex-1 flex flex-col min-h-0 overflow-hidden bg-[#08090c] ${className}`}
    >
      {/* Visual Identity Layer — Fixed behind all content */}
      <div
        className="absolute inset-0 pointer-events-none select-none overflow-hidden z-0"
        aria-hidden="true"
      >
        {/* ============================================================== */}
        {/* RECOGNIZABLE FLAG VISUALS (Left: India 🇮🇳 | Right: USA 🇺🇸)     */}
        {/* ============================================================== */}
        <div className="absolute inset-0 flex flex-row overflow-hidden opacity-40 sm:opacity-45">
          {/* ------------------------------------------------------------ */}
          {/* LEFT 50%: INDIAN NATIONAL FLAG                               */}
          {/* Saffron (#FF9933) | White (#FFFFFF) | Green (#138808)        */}
          {/* ------------------------------------------------------------ */}
          <div className="w-1/2 h-full relative overflow-hidden flex flex-col">
            {/* Top Band: Saffron */}
            <div className="w-full h-1/3 bg-[#FF9933]" />

            {/* Middle Band: White with Ashoka Chakra */}
            <div className="w-full h-1/3 bg-[#FFFFFF] relative flex items-center justify-center">
              <AshokaChakra />
            </div>

            {/* Bottom Band: India Green */}
            <div className="w-full h-1/3 bg-[#138808]" />

            {/* Soft fade-out towards the center split */}
            <div className="absolute right-0 top-0 bottom-0 w-28 sm:w-44 bg-gradient-to-r from-transparent to-[#08090c]" />

            {/* Subtle corridor identifier */}
            <div className="absolute top-2.5 left-4 sm:left-6 flex items-center gap-1.5 font-mono text-[9px] sm:text-[10px] uppercase tracking-widest text-slate-200/50 font-bold bg-[#08090c]/70 px-2 py-0.5 rounded-sm border border-slate-700/30">
              <span>🇮🇳 INDIA</span>
            </div>
          </div>

          {/* ------------------------------------------------------------ */}
          {/* RIGHT 50%: UNITED STATES FLAG                                */}
          {/* 13 Red/White Stripes + Blue Canton with 50 White Stars        */}
          {/* ------------------------------------------------------------ */}
          <div className="w-1/2 h-full relative overflow-hidden flex flex-col">
            {/* 13 Alternating Stripes (7 Red, 6 White) */}
            {Array.from({ length: 13 }).map((_, i) => (
              <div
                key={i}
                className="w-full flex-1"
                style={{
                  backgroundColor: i % 2 === 0 ? '#B22234' : '#FFFFFF',
                }}
              />
            ))}

            {/* Blue Canton (#002868) with 50 White Stars */}
            <div className="absolute top-0 left-0 w-[46%] sm:w-[40%] h-[53.846%] bg-[#002868] flex items-center justify-center p-2 sm:p-3.5 shadow-sm">
              <USStarCanton />
            </div>

            {/* Soft fade-out towards the center split */}
            <div className="absolute left-0 top-0 bottom-0 w-28 sm:w-44 bg-gradient-to-l from-transparent to-[#08090c]" />

            {/* Subtle corridor identifier */}
            <div className="absolute top-2.5 right-4 sm:right-6 flex items-center gap-1.5 font-mono text-[9px] sm:text-[10px] uppercase tracking-widest text-slate-200/50 font-bold bg-[#08090c]/70 px-2 py-0.5 rounded-sm border border-slate-700/30">
              <span>USA 🇺🇸</span>
            </div>
          </div>
        </div>

        {/* ============================================================== */}
        {/* CENTER SOFT BLEND (Organic merge between the two flags)        */}
        {/* ============================================================== */}
        <div className="absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-36 sm:w-56 bg-gradient-to-r from-transparent via-[#08090c]/90 to-transparent pointer-events-none z-1" />

        {/* ============================================================== */}
        {/* DARK NEUTRAL READABILITY OVERLAY (No blue tint wash!)         */}
        {/* ============================================================== */}
        {/* Dark neutral veil ensuring all panels and text remain crisp */}
        <div className="absolute inset-0 bg-[#08090c]/55 pointer-events-none z-2" />

        {/* Subtle neutral radial vignette */}
        <div
          className="absolute inset-0 pointer-events-none z-2"
          style={{
            background:
              'radial-gradient(ellipse at 50% 50%, transparent 30%, rgba(8, 9, 12, 0.40) 70%, rgba(8, 9, 12, 0.85) 100%)',
          }}
        />
      </div>

      {/* Actual page content rendered cleanly above the visual identity */}
      <div className="relative z-10 flex-1 flex flex-col min-h-0 w-full h-full">
        {children}
      </div>
    </div>
  );
};
