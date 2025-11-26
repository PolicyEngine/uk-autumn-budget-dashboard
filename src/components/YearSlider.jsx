import { useState, useEffect, useRef } from "react";
import "./YearSlider.css";

const YEARS = [2026, 2027, 2028, 2029];

function YearSlider({ selectedYear, onYearChange }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (isPlaying) {
      intervalRef.current = setInterval(() => {
        onYearChange((prevYear) => {
          const currentIndex = YEARS.indexOf(prevYear);
          if (currentIndex >= YEARS.length - 1) {
            // Stop playing when reaching the end
            setIsPlaying(false);
            return prevYear;
          }
          return YEARS[currentIndex + 1];
        });
      }, 1500); // Change year every 1.5 seconds
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isPlaying, onYearChange]);

  const handleSliderChange = (e) => {
    const index = parseInt(e.target.value);
    onYearChange(YEARS[index]);
    setIsPlaying(false);
  };

  const handlePlayPause = () => {
    // If at the last year and clicking play, restart from beginning
    if (!isPlaying && currentIndex >= YEARS.length - 1) {
      onYearChange(YEARS[0]);
    }
    setIsPlaying(!isPlaying);
  };

  const currentIndex = YEARS.indexOf(selectedYear);

  return (
    <div className="year-slider">
      <button
        className="play-button"
        onClick={handlePlayPause}
        aria-label={isPlaying ? "Pause" : "Play"}
      >
        {isPlaying ? "⏸" : "▶"} {isPlaying ? "Pause" : "Play"}
      </button>
      <div className="slider-container">
        <input
          type="range"
          min="0"
          max={YEARS.length - 1}
          value={currentIndex}
          onChange={handleSliderChange}
          className="slider"
          step="1"
        />
        <div className="year-labels">
          {YEARS.map((year, index) => (
            <span
              key={year}
              className={`year-label ${index === currentIndex ? "active" : ""}`}
            >
              {year}-{(year + 1).toString().slice(-2)}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

export default YearSlider;
