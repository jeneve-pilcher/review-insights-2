// Optional analytics and advertising scripts. NOTHING here loads unless (a) the visitor clicked Accept in the cookie
// banner and (b) an ID is set below. With no IDs set, no third-party script is ever added to the page.
//
// To use one, set it where the frontend is BUILT (Render: frontend service -> Environment) and redeploy:
//   VITE_GA_MEASUREMENT_ID = G-XXXXXXXXXX   (Google Analytics 4)
//   VITE_META_PIXEL_ID     = 1234567890     (Meta / Facebook Pixel)
// Add any other tracker to loadTrackers() in ../utils/consent.js, behind the same consent check, never in index.html.
export const TRACKERS = {
  googleAnalyticsId: (import.meta.env.VITE_GA_MEASUREMENT_ID || '').trim(),
  metaPixelId: (import.meta.env.VITE_META_PIXEL_ID || '').trim(),
}
