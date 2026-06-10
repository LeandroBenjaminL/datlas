/**
 * Datlas — Frontend Configuration
 *
 * Detects the environment and sets the API base URL accordingly.
 * - Local dev: http://localhost:8000
 * - Production: https://datlas-api.onrender.com
 */

const API =
	window.location.hostname === "localhost"
		? "http://localhost:8000"
		: "https://datlas-api.onrender.com";

/** API Key for authenticated requests (visible in client-side JS). */
const API_KEY = "dtl4s_7kXp9mW2qR5vY8bN3jH6cL0fA1eD";

export { API, API_KEY };
