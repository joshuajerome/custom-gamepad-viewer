/* UI behavior script.

Fetches configuration (/api/config), applies changes via POST (/api/config),
reacts to storage events, and refreshes the preview iframe using returned URLs.
Designed to be framework-agnostic and easily portable to NiceGUI/Streamlit later.
*/

console.log("LGV Phase 0 UI loaded");
