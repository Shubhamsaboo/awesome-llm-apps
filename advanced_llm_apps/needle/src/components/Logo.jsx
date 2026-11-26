import React from "react";
export default function Logo({ small = false }) {
  return (
    <span className={`logo ${small ? "small" : ""}`}>
      <svg viewBox="0 0 32 32" aria-hidden="true">
        <path
          d="m9 25 12-17 3 2-12 17Zm9-13 3 2"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.4"
          strokeLinecap="round"
        />
      </svg>
      {!small && (
        <span>
          needle<span className="logo-period">.</span>
        </span>
      )}
    </span>
  );
}
