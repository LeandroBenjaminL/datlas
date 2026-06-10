/**
 * Datlas — Frontend Configuration
 *
 * Detects the environment and sets the API base URL accordingly.
 * - Local dev: http://localhost:8000
 * - Production: https://datlas-api.onrender.com
 */

const API = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://datlas-api.onrender.com';

export default API;
