/**
 * Shared API configuration.
 *
 * In production (Railway etc.), browser requests go through the Next.js
 * proxy route at /api/backend/* which forwards to the backend service.
 *
 * NEXT_PUBLIC_API_URL can override this for direct-access setups (e.g. ngrok).
 */
export const API_BASE =
    process.env.NEXT_PUBLIC_API_URL || "/api/backend";

export const API_KEY =
    process.env.NEXT_PUBLIC_API_KEY || "psak117-dev-secret-key-ganti-di-production";

/**
 * Default headers for all API calls.
 * Includes ngrok-skip-browser-warning to bypass ngrok free tier interstitial.
 */
export const API_HEADERS: Record<string, string> = {
    "X-API-Key": API_KEY,
    "ngrok-skip-browser-warning": "true",
};
