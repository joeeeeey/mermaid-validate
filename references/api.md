# Official API and runtime notes

Reviewed 2026-10-08. Public documentation is authoritative for the target account/version.

## [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli)

Pinned CLI 12.0.0; documented SVG output and Puppeteer configuration.

## Boundaries

No credentials. Python 3.10+, Node.js 22.20+ and npm. First rendering downloads pinned Mermaid CLI and a Puppeteer browser; a compatible Chrome runtime and OS libraries are required. Use `--mmdc /path/to/mmdc` for a preinstalled renderer.

Renderer version may differ from GitHub's Mermaid version. Nested lists and blockquoted Markdown fences are not parsed. `--timeout` applies per diagram. JSON errors can include diagram text; review before sharing.

HTTP helpers do not follow redirects or automatically retry writes. A timeout can mean an unknown outcome; inspect the target before retrying. Secret-field redaction is defense in depth, not a guarantee that arbitrary free text is safe to publish.
