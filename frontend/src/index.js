import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

// Suppress lightweight-charts "Object is disposed" errors from internal RAF paint callbacks.
// When chart.remove() is called, lightweight-charts may have a pending requestAnimationFrame
// that fires after disposal and throws internally. This is a known lw-charts v4 limitation —
// the error is cosmetic (chart is already removed) and should not show the dev error overlay.
window.addEventListener('error', (event) => {
  if (event.message && event.message.includes('Object is disposed')) {
    event.stopImmediatePropagation();
    event.preventDefault();
  }
}, true); // useCapture=true so this fires before React overlay's handler

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
