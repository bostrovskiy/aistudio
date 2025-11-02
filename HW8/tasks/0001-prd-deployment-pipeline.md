## Introduction/Overview

Deploy the `HW6-project` student app to the public internet with a simple, low-cost setup that supports safe local development, testing, and promotion to production. The solution should use AWS Amplify Hosting (CloudFront-backed) for the static front end and a minimal AWS Lambda (via Amplify Function) to proxy sensitive API calls (e.g., OpenAI) so that secrets are never exposed in the browser.

## Goals

- Provide a public production URL with HTTPS and optional custom domain.
- Enable local development with near-parity to production (same API shape, separate secrets).
- Keep costs near free-tier and complexity low.
- Protect secrets (e.g., OpenAI API key) by moving them server-side.
- Simple CI/CD: commits to the main branch automatically deploy to production.

## User Stories

- As a developer, I can run the app locally and test changes without affecting production.
- As a developer, I can merge a PR to `main` and have production update automatically.
- As a developer, I can configure secrets per environment without committing them to git.
- As a user, I can access the app at a stable HTTPS URL (with a custom domain).

## Functional Requirements

1) Hosting and Environments
   - 1.1 The front end (static files from `HW6-project/`) is hosted by AWS Amplify Hosting (S3 + CloudFront under the hood).
   - 1.2 Environments: Local (developer machine) and Production (Amplify). No staging environment initially.
   - 1.3 Production deploys automatically on successful merges to `main`.

2) Backend API Proxy (Secrets Safety)
   - 2.1 Provide a minimal serverless API (AWS Lambda via Amplify Function + API Gateway) for sensitive operations (e.g., OpenAI calls), exposed under `/api/*`.
   - 2.2 The OpenAI API key must only exist in server-side environment variables (Amplify Function env), never shipped to the browser or committed to git.
   - 2.3 The client code (`openai-service.js` or equivalent) must call the serverless endpoint, not OpenAI directly.
   - 2.4 CORS must allow the production domain (and local dev origin) to call the API.

3) Local Development
   - 3.1 Running a single command (e.g., `npm run dev`) starts a local static server and a local API proxy with the same routes as production (`/api/*`).
   - 3.2 Local secrets are loaded from `.env.local` and are not committed (gitignored), using the same variable names as production.
   - 3.3 The front end must be configurable (e.g., via `config.js` or env-driven) to call `http://localhost:<port>/api/*` in dev and the Amplify API URL in production.

4) CI/CD and Branching
   - 4.1 Repository is connected to AWS Amplify Hosting for automatic builds and deploys of the static site and functions.
   - 4.2 Branching model: protected `main` with feature branches and PRs. Only merges to `main` deploy to production.
   - 4.3 Optional: Enable preview builds per-PR later (out of scope initially).

5) Custom Domain
   - 5.1 Support attaching a custom domain to Amplify (either managed via Route53 or external registrar DNS).
   - 5.2 Provide instructions to verify ownership and add required DNS records. Amplify must issue HTTPS certificates automatically.

6) Configuration and Environment Variables
   - 6.1 Local: `.env.local` (gitignored) holds secrets like `OPENAI_API_KEY` and any `API_BASE_URL` overrides.
   - 6.2 Production: Amplify environment variables for both Hosting (if needed) and Functions (required for secrets).
   - 6.3 No secrets may be present in the repository or bundled client artifacts.

7) Observability and Reliability (Minimal)
   - 7.1 Basic logs are available via CloudWatch for the Lambda function.
   - 7.2 If the serverless API returns an error, the client should show a friendly error message.

8) Documentation
   - 8.1 A short README section documents: local setup, how to set env vars, how to run dev, how deploys work, how to add a custom domain, and where to view logs.

## Non-Goals (Out of Scope)

- Database storage, authentication, or role-based access control.
- Complex multi-environment promotion (no dedicated staging environment initially).
- Advanced monitoring/alerting (beyond basic logs).
- Automated test suite or CI test gates (may be added later).
- Infrastructure-as-code beyond what Amplify configures by default.

## Design Considerations (Optional)

- Keep file structure in `HW6-project/` unchanged where possible. If needed, introduce a small `/api` folder for local dev proxy scripts without impacting existing front-end code.
- Ensure `openai-service.js` (or its replacement) reads the API base from a single source of truth so switching envs is trivial.
- Use sensible defaults: in dev, point to `http://localhost:<port>/api`; in prod, rely on relative `/api` so CloudFront domain works without hardcoding.

## Technical Considerations (Optional)

- Platform: AWS Amplify Hosting for static site; Amplify Function (Node.js 18+) + API Gateway for `/api/*`.
- Region: Default region (e.g., us-east-1) is acceptable.
- Security: Never expose secret keys in client bundles; validate and rate-limit requests server-side if needed.
- CORS: Allow only the dev origin and production domain.
- Performance/Cost: Prefer free-tier eligible services; keep function cold start impact minimal by using Node.js and small dependencies.

## Success Metrics

- Production site publicly accessible at an HTTPS URL, with custom domain configured.
- Local dev parity: same API routes and behavior locally and in production.
- Zero secrets present in client bundles or source control.
- Deploys occur automatically within a few minutes after merging to `main`.

## Open Questions

- What GitHub repository should Amplify connect to? (Private/public)
- Confirm custom domain name and registrar; do you prefer Route53 or external DNS?
- Is `openai-service.js` currently calling OpenAI directly in the browser? If so, we will refactor to use the serverless proxy.
- Any preferred Node.js version (default to 18 LTS on Lambda)?
- Do you want preview builds per PR later?


