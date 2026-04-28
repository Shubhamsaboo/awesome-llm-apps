import { memo } from "react";
import { Squircle } from "./squircle";

function SunIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className="h-14 w-14 text-[--sunshine-yellow]"
    >
      <circle cx="12" cy="12" r="5" />
      <path
        d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"
        strokeWidth="2"
        stroke="currentColor"
      />
    </svg>
  );
}

export const WeatherCard = memo(function WeatherCard({
  location,
  themeColor,
  temperature,
  humidity,
  windSpeed,
  feelsLike,
}: {
  location: string;
  themeColor: string;
  temperature: number;
  humidity: number;
  windSpeed: number;
  feelsLike: number;
}) {
  return (
    <Squircle
      squircle="30"
      style={{ backgroundColor: themeColor, overflow: "hidden" }}
      borderWidth={2}
      borderColor="var(--surface-elevated)"
      className="weather-card-enter mb-4 mt-6 w-full max-w-md shadow-[0_16px_35px_-20px_rgba(94,92,90,0.45)]"
    >
      <div className="w-full bg-white/72 p-5 text-[var(--gray-dark)] backdrop-blur-md">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold capitalize text-[var(--gray-dark)]">{location}</h3>
            <p className="text-[var(--gray-dark)]/75">Current Weather</p>
          </div>
          <SunIcon />
        </div>

        <div className="mt-4 flex items-end justify-between">
          <div className="text-3xl font-bold text-[var(--gray-dark)]">{temperature}°</div>
          <div className="text-sm text-[var(--gray-dark)]/80">Clear skies</div>
        </div>

        <div className="mt-4 border-t border-[var(--gray-dark)]/14 pt-4">
          <div className="grid grid-cols-3 gap-2 text-center">
            <div>
              <p className="text-xs text-[var(--gray-dark)]/70">Humidity</p>
              <p className="font-semibold text-[var(--gray-dark)]">{humidity}%</p>
            </div>
            <div>
              <p className="text-xs text-[var(--gray-dark)]/70">Wind</p>
              <p className="font-semibold text-[var(--gray-dark)]">{windSpeed} mph</p>
            </div>
            <div>
              <p className="text-xs text-[var(--gray-dark)]/70">Feels Like</p>
              <p className="font-semibold text-[var(--gray-dark)]">{feelsLike}°</p>
            </div>
          </div>
        </div>
      </div>
    </Squircle>
  );
});
