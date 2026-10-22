# KRAKEN MESH
## CLAUDE.md — Master Engineering Charter
### Distributed Agent Runtime · WAT Framework · Security · Infrastructure · Brand System · Asset Library · Dashboard · Reliability

**Project:** KRAKEN MESH  
**Tagline:** MANY DEVICES. ONE SWARM. YOUR RULES.  
**Document role:** Canonical project-level engineering charter  
**Primary environment:** Antigravity IDE, Claude Code, cooperating AI agents, local computers, Android/Termux devices and optional local servers  
**Architecture principle:** Local-first, modular, observable, resource-aware, secure by default  
**Operating principle:** Inspect → Understand → Plan → Implement → Test → Verify → Document

---

# 0. MISSION AND NON-NEGOTIABLE RULES

KRAKEN MESH is a local-first distributed computing and AI-agent platform that coordinates available personal devices, agent runtimes, tools and services through a coherent, user-controlled architecture.

The project combines:

1. A distributed node and execution runtime.
2. An agent orchestration and task-management system.
3. A resource-aware scheduler.
4. A provider-independent AI integration layer.
5. Secure communication between authorized nodes.
6. An operational terminal and command-line interface.
7. A professional, real-data dashboard.
8. A reusable visual identity and asset library.
9. Optional file services, game-server hosting and additional execution modules.
10. A deterministic WAT framework for reliable operations.
11. Testing, diagnostics, recovery, documentation and release engineering.

The goal is not to create a collection of disconnected scripts or a dashboard that merely looks impressive.

The goal is a maintainable system in which actual capabilities are implemented, discoverable, testable, observable and controlled by the owner.

## 0.1 Absolute rules

- Inspect the existing repository before modifying it.
- Preserve working functionality, user data, configuration and existing integrations.
- Do not replace an existing architecture without demonstrating why the replacement is necessary.
- Do not confuse a proposed feature with an implemented feature.
- Do not create fake data to make the dashboard look operational.
- Do not report tests as passed unless they were executed and their results inspected.
- Do not fabricate agent identities, session IDs, paths, API responses, benchmarks or successful integrations.
- Do not create duplicate systems when an existing implementation can be extended.
- Do not make destructive changes without explicit authorization.
- Do not expose secrets in code, logs, screenshots, documentation or generated artifacts.
- Do not bypass provider authentication, subscription requirements, quotas, licenses or security controls.
- Do not make paid API calls or consume paid credits without following the project's approval rules.
- Do not execute arbitrary shell commands produced by an LLM without a policy-controlled execution boundary.
- Do not silently enable telemetry, external access, public hosting or remote execution.
- Do not introduce unnecessary frameworks, dependencies or abstractions.
- Do not stop after producing a plan when authorized implementation work is possible.
- Do not claim that the system is production-ready without evidence appropriate to that claim.

**Priority order:** safety and data integrity → correctness → working core runtime → secure connectivity → scheduling and execution → real integrations → observability → user interface → optional modules → polish and release.

When requirements conflict, safety, existing project contracts and verified behavior take precedence over visual polish or implementation speed.

---

# 1. AGENT IDENTITY, SESSION AND WORKSPACE VERIFICATION

At the beginning of a new session, establish what can actually be verified.

Report:

- Your declared agent role.
- Your actual working directory.
- The verified repository root.
- The available read/write and execution capabilities.
- The relevant project instructions discovered.
- Whether other agents or sessions are accessible through a real supported mechanism.
- Whether the current conversation/session identifier is available through an authoritative source.

Never invent a conversation ID or claim to share another session's history without evidence.

If a user requests confirmation that another session's conversations are inaccessible, distinguish between observed environment facts and assumptions.

Do not waste the session asking questions already answered in this file or discoverable from the repository.

Ask the user only when a missing decision materially blocks safe or correct progress.

---

# 2. REPOSITORY AUDIT BEFORE IMPLEMENTATION

The repository is the source of truth for the current implementation.

Do not assume that a proposed directory structure, framework, dependency or script already exists.

## 2.1 Mandatory discovery

Inspect, as applicable:

- `CLAUDE.md`, `AGENTS.md` and other applicable instructions.
- Existing architecture and design documentation.
- Git status, current branch and uncommitted changes.
- Root directory and project manifests.
- Package managers and lockfiles.
- Existing workflows, agents and deterministic tools.
- Runtime entry points and command-line interfaces.
- API contracts and internal service boundaries.
- Dashboard framework and component system.
- Existing visual assets and design tokens.
- Databases, state stores and migration systems.
- Authentication, authorization and secret handling.
- Tests, fixtures, CI configuration and build scripts.
- Logging, monitoring, health checks and error handling.
- Deployment, installation, update and recovery mechanisms.
- Existing Android/Termux support and platform adapters.
- Existing file-serving, game-hosting or other service modules.
- Known defects, incomplete features and technical debt.

Use the project's established commands to inspect and test it.

Do not run destructive scripts, automatic migrations or broad cleanup operations simply to discover how the project works.

## 2.2 Establish a baseline

Record:

- What currently works.
- What is incomplete.
- What is broken before modifications.
- Which tests pass and fail.
- Which capabilities are mocked or simulated.
- Which integrations are real, configured, unavailable or unverified.
- Which files contain user changes that must be preserved.
- Which high-risk areas require special care.

Create a concise, evidence-based audit report in the project's existing documentation convention.

If a new report is needed, use an appropriate existing location or propose one without reorganizing the repository unnecessarily.

## 2.3 Change safety

Before modifying important files:

1. Inspect the current contents.
2. Understand callers and dependencies.
3. Identify behavior that must remain compatible.
4. Make the smallest coherent change.
5. Run relevant checks.
6. Inspect the diff.
7. Document any compatibility impact.

Never use broad file replacement as a substitute for understanding existing code.

---

# 3. WAT FRAMEWORK — CANONICAL OPERATING MODEL

KRAKEN MESH follows the WAT model: Workflows, Agents and Tools.

The framework separates probabilistic reasoning from deterministic execution.

## 3.1 Layer 1 — Workflows

Workflows define how work should be performed.

A workflow should describe:

- Objective.
- Required inputs.
- Preconditions.
- Required permissions.
- Ordered steps.
- Tools to invoke.
- Expected outputs.
- Validation criteria.
- Failure handling.
- Recovery behavior.
- Security considerations.
- Evidence to record.
- Completion conditions.

Use plain, operational language.

Workflows are procedural contracts, not collections of vague aspirations.

### Workflow protection

Existing workflows are user-owned project instructions.

Do not create, overwrite, rename, move or delete workflows without explicit authorization, unless a more specific existing project policy explicitly permits the operation.

When a workflow improvement is necessary:

1. Identify the problem.
2. Prepare a proposed patch.
3. Explain the expected improvement.
4. Identify compatibility risks.
5. Request authorization before applying the change.

Never silently replace project instructions with a newly generated version.

## 3.2 Layer 2 — Agents

Agents interpret requests, select workflows, coordinate work, inspect results and decide what should happen next.

An agent should not pretend to be a deterministic execution engine.

Responsibilities include:

- Understanding the objective.
- Selecting an applicable workflow.
- Checking preconditions.
- Choosing authorized tools.
- Coordinating dependent tasks.
- Interpreting execution results.
- Handling exceptions.
- Requesting approval for restricted actions.
- Updating the task state.
- Reporting evidence and limitations.

Agent autonomy must operate within explicit capability, cost, security and permission boundaries.

## 3.3 Layer 3 — Tools

Tools perform concrete operations.

Examples include:

- File operations.
- Image conversion and optimization.
- SVG validation.
- Asset manifest generation.
- Database queries.
- Health checks.
- Process inspection.
- Resource measurements.
- Test execution.
- API integrations.
- Backup and restore.
- Service deployment.
- Log analysis.

Inspect `tools/` before creating a new utility.

Prefer deterministic scripts for repeatable operations. Avoid asking an LLM to repeatedly perform tasks that a reliable script can execute consistently.

Every important tool should define:

- Input contract.
- Output contract.
- Exit codes.
- Timeout behavior.
- Error handling.
- Permission requirements.
- Logging behavior.
- Idempotency where applicable.
- Tests or reproducible validation.
- Documentation.

## 3.4 WAT self-improvement loop

When a tool or workflow fails:

1. Capture the actual error.
2. Determine whether the cause is input, code, configuration, permissions, environment or external service behavior.
3. Reproduce the failure when safe.
4. Implement a targeted correction.
5. Retest.
6. Record the finding.
7. Propose workflow improvements when required.
8. Request approval for protected workflow changes.

Never hide a failure merely to make a run appear successful.

---

# 4. MULTI-AGENT ENGINEERING AND COORDINATION

Multiple agents may contribute to KRAKEN MESH through Antigravity, Claude Code or other supported environments.

Parallel work is allowed only when the actual tools and session arrangement support it.

Do not assume that naming several agents makes them available or that independent sessions share state.

## 4.1 Recommended responsibility boundaries

Use these logical roles when the environment supports them:

### Agent A — Lead Architect and Integrator
- Owns cross-module contracts.
- Maintains task sequencing.
- Resolves interface conflicts.
- Reviews integration changes.
- Tracks project-wide risks.
- Verifies the final system.

### Agent B — Brand System and Asset Library
- Owns visual identity implementation.
- Builds the asset pipeline.
- Maintains design tokens and asset metadata.
- Integrates branding into approved application entry points.
- Validates visual assets and exports.

### Agent C — Runtime and Distributed Systems
- Owns node lifecycle, task execution, scheduler and distributed-state contracts.
- Preserves correctness during network interruptions.
- Tests execution and recovery semantics.

### Agent D — Security and Reliability
- Reviews trust boundaries.
- Tests authentication, authorization, filesystem boundaries and execution policies.
- Conducts independent security and failure-mode reviews.

### Agent E — Platform and Infrastructure
- Handles platform adapters, Android/Termux compatibility, resource discovery, packaging and optional services.

### Agent F — AI Integrations
- Implements provider adapters, agent-runtime connectors and capability detection.
- Verifies actual integration behavior against supported documentation.

### Agent G — QA and Release
- Develops reproducible tests.
- Validates build, packaging, recovery and documentation.
- Produces evidence-based release reports.

These are role definitions, not claims that seven agents are currently running.

## 4.2 Ownership and shared files

Before parallel implementation, define:

- Task identifier.
- Agent owner.
- Files or modules owned.
- Interfaces expected.
- Files that must not be modified.
- Dependencies.
- Acceptance criteria.
- Test responsibilities.
- Integration owner.

Avoid concurrent editing of the same critical files.

Prefer interface-first integration and small, reviewable patches.

If two agents modify overlapping areas, inspect and reconcile the actual diffs. Never overwrite one agent's work blindly.

## 4.3 Agent task contract

Every delegated task should specify:

- Objective.
- Existing context.
- Scope.
- Out-of-scope work.
- Allowed tools and permissions.
- Expected files.
- Interfaces and dependencies.
- Acceptance criteria.
- Tests to execute.
- Evidence to return.
- Approval requirements.

Agent reports must distinguish implementation, tests, review and unresolved work.

## 4.4 Multi-agent verification

An independent reviewer should examine important security and architecture changes without relying solely on the implementing agent's claims.

A reviewer should inspect the actual diff, tests, assumptions and relevant execution traces.

Do not count duplicated AI opinions as independent verification if the reviewers merely repeat the same unverified assumptions.

---

# 5. PRODUCT VISION AND SYSTEM BOUNDARIES

KRAKEN MESH coordinates computing resources and agent capabilities across authorized personal devices.

Potential participants include:

- Windows and Linux computers.
- Local servers.
- Android devices running supported Termux environments.
- Authorized worker nodes.
- AI-agent runtimes.
- Local model servers.
- Approved external AI providers.
- Optional service modules.

The system must remain useful on a single device before depending on distributed functionality.

## 5.1 Architectural layers

Preserve or evolve the existing implementation toward clear boundaries:

1. **Interface layer:** CLI, terminal presentation and dashboard.
2. **Control plane:** configuration, identities, policy, node registry and orchestration.
3. **Execution plane:** workers, task runners, tool adapters and process isolation.
4. **Scheduling plane:** resource-aware placement, leases, deadlines and retries.
5. **Transport plane:** authenticated communication between authorized participants.
6. **Persistence plane:** configuration, task state, audit records and durable queues.
7. **Integration plane:** AI providers, agent runtimes and optional services.
8. **Platform plane:** Windows, Linux, Android/Termux and supported deployment environments.
9. **Observability plane:** structured logs, metrics, health, traces and diagnostics.
10. **Design system:** reusable branding, UI tokens, components and asset library.

These are logical boundaries, not an instruction to create ten separate services.

Do not introduce microservices where a modular process is sufficient.

Use separate processes or services only when isolation, lifecycle management, scalability or platform constraints justify them.

## 5.2 Local-first operation

A single-node installation should be able to start and provide its supported local capabilities without requiring a remote server.

Remote services must be optional unless a specific feature inherently depends on them.

The platform must not silently transmit personal files, prompts, logs, credentials or device information to external services.

Document every necessary external communication.

## 5.3 Honest capability model

Every capability should have an explicit state, such as:

- `AVAILABLE`
- `UNAVAILABLE`
- `DISABLED`
- `CONFIGURATION_REQUIRED`
- `AUTHENTICATION_REQUIRED`
- `DEGRADED`
- `UNVERIFIED`
- `FAILED`

Use the existing project vocabulary if it already provides equivalent semantics.

A configured integration is not necessarily working. A discovered executable is not necessarily usable. A running process is not necessarily healthy.

Capability states must reflect evidence.

---

# 6. NODE IDENTITY AND LIFECYCLE

Every participating node must have a stable identity independent of its current network address.

A node record should contain, as appropriate:

- Stable node identifier.
- Human-readable display name.
- Platform and version.
- Advertised capabilities.
- Resource profile.
- Security and trust state.
- Connection state.
- Last successful heartbeat.
- Software version.
- Configuration revision.
- Supported protocol versions.
- Registration and revocation state.

Do not expose sensitive device identifiers unnecessarily.

## 6.1 Lifecycle

Implement or preserve explicit lifecycle transitions:

`DISCOVERED → PAIRING → AUTHORIZED → ONLINE → DEGRADED/OFFLINE`

Revocation and removal must be represented explicitly.

A node must not gain execution privileges merely because it is visible on the network.

## 6.2 Pairing and trust

Implement secure, explicit pairing.

Requirements:

- Strong authentication between participants.
- A clear approval step for new nodes.
- Cryptographic identity verification.
- Secure storage of private credentials.
- Explicit revocation.
- Replay protection.
- Protocol-version validation.
- Protection against unauthorized node impersonation.
- Auditable pairing and revocation events.

Use established, maintained cryptographic libraries and protocols.

Do not invent custom cryptographic primitives.

Never embed shared production secrets into a distributed application image.

## 6.3 Network partitions

The system must tolerate nodes disappearing and returning.

Do not assume that all nodes share an always-consistent view of state.

Define what happens when:

- A worker disconnects during execution.
- A coordinator restarts.
- A lease expires.
- Two nodes temporarily disagree about task state.
- A node returns with stale configuration.
- A task result arrives after cancellation.
- The same message is delivered twice.

Document consistency guarantees and limitations.

---

# 7. TASK EXECUTION AND DISTRIBUTED CORRECTNESS

Task execution is a core reliability boundary.

## 7.1 Task state

Use a durable state machine compatible with the current implementation. A suitable logical model is:

`CREATED → VALIDATED → QUEUED → SCHEDULED → RUNNING → SUCCEEDED`

Alternative terminal or intermediate states may include:

`FAILED`, `CANCELLED`, `RETRY_PENDING`, `BLOCKED`, `EXPIRED`.

Transitions must be validated and recorded.

Do not allow arbitrary state changes that bypass authorization or execution invariants.

## 7.2 Task contract

A task should define:

- Stable task identifier.
- Task type.
- Validated input.
- Required capabilities.
- Security classification.
- Resource requirements.
- Deadline and priority.
- Retry policy.
- Cancellation policy.
- Idempotency behavior.
- Execution owner or lease.
- Result format.
- Output limits.
- Audit information.

Do not store unnecessary sensitive data in task metadata.

## 7.3 Persistence and recovery

Important task state must survive process restarts.

Use the existing persistence mechanism where suitable.

Define and test:

- Durable queue behavior.
- Lease acquisition and expiration.
- Recovery of interrupted tasks.
- Duplicate delivery.
- Retry limits.
- Dead-letter handling where appropriate.
- Result persistence.
- Cancellation races.
- Disk-full behavior.
- Corrupt or incomplete state handling.

Do not promise exactly-once execution unless the implementation genuinely provides that guarantee under its stated failure model.

Prefer explicit at-least-once or at-most-once semantics with idempotency where appropriate.

## 7.4 Cancellation

Cancellation is a state transition, not merely a UI button.

Define whether cancellation:

- Prevents scheduling.
- Stops a running subprocess.
- Signals a cooperative worker.
- Terminates a process after a grace period.
- Preserves partial output.
- Releases resource reservations.
- Prevents late results from being committed.

Do not report a task as cancelled if the underlying operation is still running and cannot be safely stopped.

---

# 8. RESOURCE-AWARE SCHEDULER

The scheduler should allocate work based on actual capabilities, policy and available resources.

Consider:

- CPU architecture and utilization.
- Memory availability.
- GPU or accelerator availability.
- Storage capacity.
- Battery level.
- Charging state.
- Thermal state where available.
- Network quality.
- Connectivity and estimated transfer cost.
- Supported runtimes.
- Security classification.
- Data locality.
- User-defined priorities.
- Deadline.
- Provider cost.
- Device availability.
- Task duration and memory estimates.
- Resource reservations.

Not every platform exposes every metric. Represent unavailable measurements explicitly rather than inventing values.

## 8.1 Personal-device protection

Default behavior should be conservative.

- No heavy workload on a phone without explicit authorization.
- No automatic use of mobile data for expensive transfers.
- Respect battery and thermal constraints where measurable.
- Bound CPU, memory, storage and execution time.
- Avoid draining a device needed for normal use.
- Support user-configurable quiet periods and resource budgets where relevant.
- Do not override platform power-management protections to keep workers alive indefinitely.

A device should be able to advertise that it is available only for light tasks or only while charging.

## 8.2 Scheduling policy

Implement deterministic eligibility filtering before ranking candidates.

A worker must not receive a task unless it satisfies:

1. Required capability.
2. Platform compatibility.
3. Security policy.
4. Available resource requirements.
5. Authorization.
6. Network and data-transfer constraints.
7. Applicable cost and consent policies.

After eligibility filtering, rank workers using documented scheduling criteria.

Make scheduling decisions explainable through structured reasons.

Do not let an LLM arbitrarily override resource or security constraints.

## 8.3 Backpressure

When the system cannot safely accept more work:

- Apply bounded queues.
- Reject or defer work explicitly.
- Respect task priorities.
- Avoid unlimited memory growth.
- Surface queue saturation.
- Recover gradually after resource availability returns.

---

# 9. AI PROVIDER AND AGENT-RUNTIME INTEGRATION

Use a provider-independent adapter architecture without pretending every provider offers identical capabilities.

Potential integrations include:

- Officially supported OpenAI APIs and tools.
- Official Anthropic APIs and supported Claude Code workflows.
- Hermes Agent and compatible documented interfaces.
- Supported local inference servers.
- Other explicitly approved agent runtimes.

Before implementing an adapter, verify current official documentation, licensing, platform support and available interfaces.

Do not assume that a consumer subscription includes unrestricted API access.

Do not bypass authentication, quotas, licensing, usage controls or product terms.

Do not assume that an IDE agent can be called programmatically simply because it is available in the IDE.

## 9.1 Provider adapter contract

A provider adapter should expose only the capabilities it actually supports.

Potential operations:

- Capability discovery.
- Configuration validation.
- Authentication status.
- Request submission.
- Streaming where supported.
- Cancellation where supported.
- Result normalization.
- Error normalization.
- Usage and cost reporting where available.
- Health checks where supported.

Represent unsupported features explicitly.

Do not pretend that every integration supports streaming, cancellation, tool calling or persistent sessions.

## 9.2 Provider configuration

The default configuration must not make paid external calls automatically.

Use an explicit provider configuration and clear user consent.

Support:

- Provider enable/disable state.
- Local or remote execution classification.
- Authentication validation.
- Request and output limits.
- Timeout policies.
- Rate-limit handling.
- Usage reporting when available.
- Cost ceilings where enforceable.
- No-cost operation mode.
- Explicit approval for paid fallbacks.

Never silently switch to a paid provider when a free or local provider fails.

Do not log API keys, authorization headers or sensitive prompts by default.

## 9.3 Agent execution safety

An AI model is not a trusted execution authority.

Every proposed tool call must pass deterministic validation.

The system must validate:

- Tool allowlist.
- Input schema.
- User authorization.
- Filesystem scope.
- Execution timeout.
- Resource limits.
- Network permissions.
- Secret access.
- Output size.
- Risk classification.

High-impact actions require an appropriate approval gate.

LLMs must not receive unrestricted shell access merely because a provider supports tool calling.

## 9.4 Integration verification

Use honest integration states:

- `DISCOVERED`
- `CONFIGURED`
- `AUTHENTICATED`
- `HEALTHY`
- `DEGRADED`
- `FAILED`
- `NOT_VERIFIED`

Only report a provider integration as verified after an actual test of the relevant interface succeeds.

Do not spend paid credits on verification without the required authorization.

---

# 10. SECURITY ARCHITECTURE

Security must be designed into the execution path rather than added as decorative settings.

## 10.1 Threat model

Explicitly consider:

- Malicious or compromised nodes.
- Prompt injection.
- Malicious task payloads.
- Unauthorized command execution.
- Path traversal.
- Symlink escapes.
- Secret leakage.
- Authentication bypass.
- Replay and spoofing.
- Malicious dependency updates.
- Supply-chain compromise.
- Resource exhaustion.
- Untrusted file uploads.
- Publicly exposed dashboards.
- Insecure default configurations.
- Unauthorized remote execution.
- Log injection.
- Unsafe archive extraction.
- Plugin or tool abuse.
- Cross-node privilege escalation.

Record mitigations, residual risks and tests.

## 10.2 Least privilege

Separate permissions for:

- Reading configuration.
- Reading files.
- Writing files.
- Running subprocesses.
- Accessing the network.
- Managing services.
- Installing dependencies.
- Changing security policy.
- Administering nodes.
- Accessing secrets.
- Deploying publicly accessible services.

Use the narrowest required permission.

Do not grant an agent administrative access merely to simplify implementation.

## 10.3 Filesystem safety

Every file operation must enforce approved root boundaries.

Consider:

- Absolute paths.
- Relative traversal.
- Symlinks.
- Case sensitivity.
- Unicode normalization.
- Windows drive and UNC paths.
- Race conditions.
- Archive extraction.
- Temporary file handling.
- Permission inheritance.

Validate paths at the point of use, not only in the UI.

## 10.4 Subprocess safety

Use argument arrays and safe process APIs rather than interpolating untrusted strings into shell commands.

Enforce timeouts, output limits, environment controls and process cleanup.

Do not allow arbitrary commands from an LLM to execute without deterministic policy validation and required approval.

## 10.5 Dashboard and API security

- Bind to loopback by default where appropriate.
- Require explicit configuration before remote exposure.
- Authenticate privileged operations.
- Authorize each sensitive operation.
- Protect session and authentication material.
- Apply request limits.
- Validate input schemas.
- Avoid leaking internal errors or secrets.
- Use secure transport for remote communication.
- Protect against CSRF, injection and browser-origin attacks where relevant.
- Audit administrative actions.

CORS configuration is not authentication.

A hidden button is not authorization.

## 10.6 Secrets and audit logs

Use the project's approved secret store or environment-based configuration.

Never commit secrets.

Logs should be structured, bounded and redacted.

Record security-relevant events without unnecessarily retaining personal content.

Avoid making logs an uncontrolled repository of prompts, files or credentials.

---

# 11. KRAKEN MESH VISUAL IDENTITY

The approved creative direction is an actual Kraken creature, not an abstract geometric substitute.

## 11.1 Brand concept

**KRAKEN MESH**

**MANY DEVICES. ONE SWARM. YOUR RULES.**

The Kraken represents coordinated intelligence, multiple autonomous capabilities and resilient execution.

The mesh represents cooperation between devices and agents.

The brand should feel like a sophisticated underground systems-engineering project: dark, powerful, technically credible and visually memorable.

Do not turn it into a generic SaaS brand, cryptocurrency logo, esports badge or stock AI illustration.

## 11.2 Creature requirements

The primary emblem features a custom Kraken creature.

Required visual qualities:

- Strong, sculptural head.
- Defined mantle.
- Eight coherent, deliberately arranged tentacles.
- Distinctive outer silhouette.
- Carefully controlled depth and overlap.
- Recognizable anatomy.
- Restrained industrial surface detailing.
- Dark, premium cyber-industrial character.
- Visual authority without cartoonish aggression.

The creature must remain the primary subject.

Do not replace it with a generic hexagon, letter K, circuit diagram or abstract shield.

Do not add unrelated network nodes or random electronic patterns merely to communicate that the project is technical.

## 11.3 Approved palette

| Token | Hex | Purpose |
|---|---|---|
| Obsidian | `#080D0B` | Primary background and deepest shadows |
| Abyss | `#164D42` | Dark green anatomy and shadowed surfaces |
| Emerald | `#087F5B` | Midtones and anatomical separation |
| Acid | `#9CFF45` | Selective signature accents and focal details |
| Cyan | `#52D9D2` | Restrained cold rim light and technical highlights |
| Ice | `#E8F0E9` | Precise highlights and readable text |
| Amber | `#FFB454` | Application warning state |
| Critical | `#FF5C68` | Application error or critical state |

The creature should have substantial dark surfaces, layered emerald tones and selective acid-green accents.

Cyan is a secondary contrast color, not an equal competing palette.

Amber and critical red belong primarily to operational status communication.

Avoid excessive neon, uncontrolled bloom, rainbow gradients and uniform green color washes.

## 11.4 Master artwork versus production logo

Maintain a distinction between:

1. Master creature illustration.
2. Primary logo composition.
3. Standalone creature emblem.
4. Simplified small-size emblem.
5. Monochrome emblem.
6. Wordmark.
7. Application icon.
8. Favicon.
9. Terminal identity.
10. Documentation and social preview assets.

The detailed illustration may contain shading and dimensionality.

The simplified emblem must preserve recognition with fewer details.

Do not automatically treat the master raster illustration as a production-ready vector logo.

## 11.5 Typography

The exact brand name is `KRAKEN MESH`.

The exact tagline is `MANY DEVICES. ONE SWARM. YOUR RULES.`

Use confident, legible typography with careful kerning and a technical industrial character.

Do not use excessively futuristic lettering or distort every character.

The emblem and wordmark must be separable.

Verify all text before exporting assets.

---

# 12. REUSABLE BRAND ASSET LIBRARY

Build a coherent asset library using the actual project conventions.

Suggested logical organization:

```text
branding/
├── source/
│   └── approved-master-reference
├── logos/
│   ├── primary/
│   ├── emblem/
│   ├── wordmark/
│   └── monochrome/
├── icons/
│   ├── application/
│   ├── favicon/
│   ├── terminal/
│   └── nodes/
├── tokens/
│   ├── colors
│   └── design-tokens
├── manifests/
├── tools/
├── previews/
├── tests/
└── docs/
    └── BRAND_GUIDE.md
```

This is a target organizational model, not permission to duplicate or reorganize an existing working directory unnecessarily.

Use appropriate real file extensions and formats.

Do not create empty placeholder assets to make the folder tree look complete.

## 12.1 Asset manifest

Maintain a machine-readable manifest appropriate to the project's stack.

Each asset entry should describe, where applicable:

- Stable asset identifier.
- Human-readable name.
- Actual path.
- Format.
- Variant.
- Dimensions.
- Transparency.
- Intended background.
- Minimum recommended size.
- Source asset.
- Generation method.
- Version.
- Validation status.
- Licensing or provenance information when relevant.

The manifest must describe files that actually exist.

Validation should detect missing files, invalid formats, duplicate identifiers and broken references.

## 12.2 Image pipeline

Build deterministic image-processing utilities where they provide real value.

Potential operations:

- Validate source image.
- Preserve the original.
- Inspect dimensions and color mode.
- Generate optimized raster exports.
- Generate appropriate icon sizes.
- Produce previews.
- Validate transparency and safe margins.
- Verify image metadata.
- Produce reproducible output.
- Report conversion errors.

Do not destroy the source artwork.

Do not silently overwrite an approved asset.

## 12.3 Vector pipeline

Create SVG assets only when actual vector geometry is available or deliberately reconstructed.

Validate:

- XML/SVG syntax.
- `viewBox`.
- Dimensions.
- Fill and stroke behavior.
- Scaling.
- Transparency.
- Clipping.
- External resource references.
- Excessive complexity.
- Small-size legibility.

Do not claim that a PNG embedded in an SVG is a vector reconstruction.

Do not accept automatic tracing as high-quality vector artwork without review.

Where the master illustration is too detailed for a clean SVG, keep the raster illustration and build a separately simplified vector emblem.

## 12.4 Reproducibility

Asset generation should be repeatable.

Use deterministic tools and documented commands.

If a required image-processing library is missing, check the project's dependency and approval policy before adding it.

Do not use a remote API or paid image-processing service without authorization.

## 12.5 Visual verification

Inspect generated previews where supported.

Verify the emblem at:

- 16 × 16.
- 24 × 24.
- 32 × 32.
- 64 × 64.
- Standard dashboard sizes.
- Documentation and large-format sizes.

Check monochrome readability, contrast, cropping and distortion.

A successful file conversion does not prove visual quality.

---

# 13. DESIGN TOKENS AND COMPONENT SYSTEM

Implement centralized design tokens using the existing styling architecture.

The token system should cover, as applicable:

- Brand colors.
- Semantic colors.
- Typography.
- Spacing.
- Border radii.
- Border colors.
- Shadows.
- Focus rings.
- Z-index layers.
- Motion durations.
- Responsive breakpoints.
- Icon sizing.
- Component states.

Use semantic references instead of copying hex values into multiple components.

For example:

- `background.primary`
- `surface.primary`
- `surface.elevated`
- `text.primary`
- `text.secondary`
- `brand.primary`
- `brand.accent`
- `border.subtle`
- `focus.ring`
- `status.success`
- `status.warning`
- `status.danger`

Preserve the existing framework and component conventions.

Do not introduce a second design system without a demonstrated need.

## 13.1 UI quality

All new UI must have meaningful states:

- Loading.
- Empty.
- Error.
- Success.
- Disabled.
- Permission denied.
- Offline.
- Degraded.
- Unavailable.

Use real application data.

Never present hardcoded sample metrics as live infrastructure statistics.

Avoid gratuitous animation, excessive glow, fake terminal output and ornamental charts.

Support responsive layouts, keyboard navigation and appropriate accessibility semantics.

Honor reduced-motion preferences when animations are implemented.

---

# 14. TERMINAL AND CLI

The terminal is an operational interface, not merely a branding surface.

Preserve existing commands and compatibility unless a documented change is authorized.

## 14.1 Command design

Use consistent command naming and help output.

Commands should support:

- Clear arguments.
- Input validation.
- Meaningful exit codes.
- Useful error messages.
- Safe defaults.
- Explicit destructive-action confirmation.
- Structured output where appropriate.
- Machine-readable modes where useful.

Discover the existing CLI before adding commands.

Do not create two commands that perform the same operation with different names.

## 14.2 Suggested capability areas

Adapt to the real implementation:

- System status.
- Node list and inspection.
- Pairing and revocation.
- Task submission and inspection.
- Queue inspection.
- Worker health.
- Provider configuration.
- Service management.
- Asset validation.
- Diagnostic collection.
- Backup and restore.
- Configuration validation.
- Logs and audit events.

These are capability targets, not claims that the commands already exist.

## 14.3 Terminal branding

Use compact, readable Kraken branding.

Avoid giant ASCII art on every invocation.

The output must remain legible in narrow terminals, Windows shells, Termux and non-color environments.

Support a plain or reduced-color mode where appropriate.

---

# 15. PROFESSIONAL OPERATIONAL DASHBOARD

The dashboard must be a real control surface for the underlying system.

Do not build a static mockup and present it as an operational product.

## 15.1 System overview

Display verified information, such as:

- Local runtime health.
- Authorized node count.
- Online, offline and degraded nodes.
- Active tasks.
- Queue depth.
- Failed tasks.
- Worker availability.
- Resource measurements.
- Provider integration state.
- Service health.
- Recent security-relevant events.
- Recent operational errors.

If a measurement is unavailable, show that it is unavailable.

Do not substitute random values.

## 15.2 Node management

Provide the supported operations for:

- Listing nodes.
- Inspecting node capabilities.
- Viewing connection and health state.
- Reviewing resource measurements.
- Pairing or authorizing nodes.
- Revoking nodes.
- Inspecting compatibility issues.

Sensitive actions must use appropriate authorization and confirmation.

## 15.3 Task management

Display task lifecycle and execution information.

Support the operations actually implemented by the runtime:

- Inspecting tasks.
- Viewing status transitions.
- Viewing results.
- Viewing error details.
- Cancelling tasks where supported.
- Retrying only under a valid retry policy.
- Inspecting task ownership and execution history.

Do not create controls that appear functional but do nothing.

## 15.4 Service and provider views

Show the actual status of:

- AI providers.
- Worker runtimes.
- File services.
- Game-hosting services.
- Background processes.
- Optional integrations.

Distinguish configured, authenticated, healthy, disabled, degraded and unverified states.

## 15.5 Dashboard architecture

Use the existing frontend stack.

Separate:

- Presentation.
- API or service client.
- Data models.
- Validation.
- State management.
- Error handling.
- Authentication and authorization.

Do not place privileged business logic exclusively in browser code.

Every sensitive action must be validated by the backend or trusted execution boundary.

---

# 16. FILE SERVICES, GAME HOSTING AND OPTIONAL MODULES

KRAKEN MESH may include optional services beyond AI-agent orchestration.

These features must be modular and disabled until explicitly configured.

## 16.1 File services

If supported by the existing project, provide secure file-management capabilities:

- Authorized uploads and downloads.
- Storage quotas.
- File metadata.
- Access control.
- Integrity checks.
- Safe filenames.
- Path-boundary enforcement.
- Upload size limits.
- Download authorization.
- Cleanup policies.
- Audit records.
- Backup and restore.

Do not expose arbitrary filesystem paths through an HTTP endpoint.

Do not extract untrusted archives without traversal and resource-exhaustion protections.

## 16.2 Game hosting

Where implemented and supported, game hosting should use explicit service definitions.

Consider:

- Server templates or documented configurations.
- Resource limits.
- Ports and network exposure.
- Process lifecycle.
- Log inspection.
- Restart policies.
- Storage persistence.
- Backup and restore.
- Update and rollback.
- User authorization.
- Health checks.
- Safe shutdown.

Never expose a game server publicly by default.

Never assume a mobile device can sustain a particular game server workload without measuring actual constraints.

## 16.3 Optional modules

Optional modules must declare:

- Identifier and version.
- Capabilities.
- Dependencies.
- Permissions.
- Resource requirements.
- Network requirements.
- Configuration schema.
- Lifecycle operations.
- Health checks.
- Failure behavior.
- Upgrade and rollback behavior.

A module must not acquire new privileges silently during an update.

Avoid an unrestricted plugin system in which arbitrary code can execute with full system privileges.

---

# 17. ANDROID AND TERMUX PLATFORM SUPPORT

Android devices may act as resource-constrained workers or local service hosts.

Platform support must be based on actual device and environment capabilities.

Do not assume desktop Linux behavior is identical to Termux.

Inspect:

- Android version.
- CPU architecture.
- Available memory and storage.
- Termux version and package environment.
- Supported runtimes.
- Battery and thermal constraints.
- Background execution limitations.
- Network behavior.
- Available permissions.
- Process lifecycle.
- Available local inference runtimes.

## 17.1 Mobile worker profile

Use conservative resource defaults.

- Avoid heavy workloads without explicit approval.
- Respect Android background-execution limitations.
- Do not promise indefinite background operation.
- Do not silently change system settings.
- Do not require root unless a feature genuinely needs it and the user explicitly approves.
- Do not disable security protections to make a feature work.
- Explain unsupported capabilities clearly.
- Use graceful shutdown and task recovery where feasible.

## 17.2 Platform adapters

Keep platform-specific code behind explicit interfaces.

Do not scatter Android-specific assumptions throughout the core scheduler.

Test platform detection, capability discovery and fallback behavior independently.

---

# 18. OBSERVABILITY AND DIAGNOSTICS

A reliable distributed system must explain what it is doing.

## 18.1 Structured logging

Use consistent structured fields where appropriate:

- Timestamp.
- Severity.
- Component.
- Event identifier.
- Task or node identifier.
- Correlation identifier.
- Result.
- Duration.
- Error category.

Redact secrets and sensitive content.

Avoid unlimited log growth.

## 18.2 Health checks

Separate:

- Process liveness.
- Component readiness.
- Dependency health.
- Worker availability.
- Provider health.
- End-to-end task execution.

A process being alive does not prove that its dependencies or functions work.

## 18.3 Metrics

Collect only useful, authorized measurements.

Examples:

- Task latency.
- Queue wait time.
- Success and failure rates.
- Resource utilization.
- Worker availability.
- Retry counts.
- Provider errors.
- Service uptime.

Document metric definitions.

Do not invent historical data.

## 18.4 Diagnostics

A diagnostic command should gather relevant information without unnecessarily collecting secrets or personal files.

Include environment and version information only where appropriate.

Support redaction before sharing a report externally.

Do not enable external telemetry by default.

---

# 19. INSTALLATION, UPDATES AND RECOVERY

Installation and lifecycle operations must be repeatable and safe.

## 19.1 Installation

Inspect existing packaging before implementing a new installer.

Provide clear prerequisites and capability detection.

Validate configuration before starting services.

Do not silently install unrelated packages or modify system-wide settings.

## 19.2 Updates

Updates should:

- Verify source and integrity where supported.
- Check compatibility.
- Preserve user configuration.
- Back up important state when appropriate.
- Apply migrations safely.
- Verify post-update health.
- Support rollback where feasible.

Do not claim rollback support if irreversible migrations or data transformations make rollback impossible.

## 19.3 Recovery

Test:

- Interrupted installation.
- Failed configuration.
- Process crash.
- Host restart.
- Storage exhaustion.
- Database or state corruption.
- Network interruption.
- Failed update.
- Worker disappearance.

Recovery procedures must preserve user data and explain what cannot be recovered.

## 19.4 Uninstallation

Separate application removal from user-data deletion.

Never delete user data by default during uninstall.

Require explicit authorization for destructive cleanup.

---

# 20. CONFIGURATION AND DATA CONTRACTS

Configuration should be explicit, validated and versioned where necessary.

Use the existing format and schema system.

A configuration contract should define:

- Required fields.
- Optional fields.
- Defaults.
- Allowed values.
- Validation.
- Secret references.
- Compatibility rules.
- Migration behavior.
- Failure messages.

Do not silently ignore invalid security settings.

Do not embed environment-specific absolute paths in portable code.

Do not hardcode machine-specific credentials, network addresses or local assumptions.

Use documented configuration precedence.

Keep configuration, runtime state, logs, caches, generated assets and source files logically separated.

---

# 21. TESTING AND QUALITY ENGINEERING

Tests are required for every significant new behavior.

Use the project's existing test infrastructure first.

Do not add a second test framework unnecessarily.

## 21.1 Test levels

### Unit tests
Validate pure logic, state transitions, parsing, schemas and policy rules.

### Integration tests
Validate module interfaces, persistence, service boundaries and actual tool invocation.

### End-to-end tests
Validate realistic user workflows through supported entry points.

### Security tests
Validate authorization, input handling, filesystem boundaries, execution restrictions and secret redaction.

### Failure-injection tests
Validate timeouts, process crashes, network loss, disk errors and dependency failures.

### Regression tests
Verify existing functionality remains intact.

### Visual tests
Validate branding, asset dimensions, responsive behavior and important UI states where supported.

### Platform tests
Verify actual behavior on supported operating systems and device environments.

## 21.2 Required correctness cases

Where applicable, test:

- Duplicate task submission.
- Worker disconnection.
- Coordinator restart.
- Expired lease.
- Task cancellation.
- Late task result.
- Malformed input.
- Unauthorized operation.
- Missing asset.
- Invalid SVG.
- Failed provider authentication.
- Provider rate limiting.
- Timeout.
- Storage exhaustion.
- Interrupted update.
- Configuration migration.
- Backup restoration.
- Resource constraint enforcement.

## 21.3 Test reporting

Use explicit result labels:

- `PASS`
- `FAIL`
- `WARN`
- `BLOCKED`
- `NOT RUN`
- `NOT VERIFIED`

Record the command, environment and relevant output.

A test that cannot run because a dependency is missing is not a pass.

A mock test does not prove a real external integration works.

A successful build does not prove the application behaves correctly.

---

# 22. PERFORMANCE AND RESOURCE BUDGETS

Performance improvements must be measured rather than asserted.

Before optimization:

1. Identify the bottleneck.
2. Establish a baseline.
3. Measure under a representative workload.
4. Change one coherent area.
5. Repeat the measurement.
6. Compare results.
7. Check regressions.

Track relevant costs:

- CPU.
- Memory.
- Disk usage.
- Network transfer.
- Startup time.
- Task latency.
- Queue latency.
- Provider usage and cost where measurable.

Do not optimize for a benchmark that does not reflect actual usage.

Do not claim performance gains without comparative evidence.

Protect constrained devices through bounded concurrency, bounded queues and explicit resource limits.

---

# 23. DEPENDENCY AND SUPPLY-CHAIN POLICY

Before adding a dependency:

- Check whether an existing dependency already provides the capability.
- Verify compatibility with the project's runtime.
- Review maintenance and security considerations.
- Inspect licensing.
- Assess installation and resource costs.
- Consider offline operation.
- Add the dependency through the correct package manager.
- Update the lockfile when appropriate.
- Run relevant tests.
- Document why it is needed.

Do not install packages globally when project-local installation is appropriate.

Do not execute downloaded scripts without inspecting their source and verifying their origin.

Do not weaken security settings to bypass installation problems.

---

# 24. DOCUMENTATION AND KNOWLEDGE MAINTENANCE

Documentation must describe the actual implementation.

Maintain or update the appropriate existing documentation for:

- Architecture.
- Installation.
- Configuration.
- Security model.
- Node pairing.
- Task execution.
- Provider integrations.
- CLI commands.
- Dashboard functionality.
- Asset library.
- Workflows.
- Tools.
- Troubleshooting.
- Testing.
- Backup and recovery.
- Release procedures.

Do not silently overwrite protected workflows.

If documentation conflicts with code, identify the discrepancy and correct the authorized source of truth.

Avoid duplicating entire documents across multiple files.

Prefer a single authoritative reference with links from related documentation.

---

# 25. IMPLEMENTATION ROADMAP

The roadmap is a prioritization model. It must be reconciled with the actual repository before work begins.

Do not rebuild components that already exist and pass verification.

## Phase 0 — Audit and protection

- Verify workspace and project root.
- Read instructions.
- Inspect the architecture.
- Establish the baseline.
- Identify existing working capabilities.
- Identify protected files and user changes.
- Create a dependency-aware task plan.

**Exit criteria:** a verified audit and safe implementation plan.

## Phase 1 — Core runtime and contracts

- Validate startup and configuration.
- Confirm node and task models.
- Verify persistence and error handling.
- Define capability states.
- Ensure the single-node experience works.

**Exit criteria:** core behavior can be tested without requiring a remote node or paid provider.

## Phase 2 — Secure node communication

- Validate pairing and identity.
- Validate authentication and authorization.
- Test node revocation.
- Test network interruption.
- Test worker recovery.

**Exit criteria:** two authorized nodes can communicate securely under documented constraints.

## Phase 3 — Task lifecycle and scheduler

- Validate state transitions.
- Implement durable execution behavior.
- Enforce resource-aware eligibility.
- Apply retries, leases and cancellation policies.
- Test recovery and duplicate delivery.

**Exit criteria:** scheduling and execution behave according to explicit, tested guarantees.

## Phase 4 — AI integrations

- Establish provider contracts.
- Inspect official documentation.
- Implement appropriate adapters.
- Validate configuration and authentication.
- Add cost controls and failure handling.
- Verify actual integration behavior.

**Exit criteria:** each supported integration has evidence of its real tested capabilities.

## Phase 5 — Visual identity and asset library

- Locate the approved Kraken artwork.
- Audit existing assets.
- Implement centralized design tokens.
- Build the asset manifest.
- Create reproducible image-processing tools.
- Create or refine vector assets where appropriate.
- Validate sizes, contrast and references.
- Integrate into existing entry points.

**Exit criteria:** the library contains real validated assets and is used by the application.

If the source artwork is missing, complete the independent infrastructure work and explicitly record the blocked artwork-dependent tasks.

## Phase 6 — Dashboard and terminal

- Integrate the real runtime state.
- Implement useful node and task views.
- Display provider and service health.
- Improve CLI consistency.
- Add meaningful loading, empty and error states.
- Test accessibility and responsiveness.

**Exit criteria:** controls operate on real backend capabilities and the interface accurately reflects system state.

## Phase 7 — Optional services and platform hardening

- Audit file services.
- Audit game hosting.
- Validate Android/Termux behavior.
- Harden installation and update paths.
- Verify service permissions.
- Test resource limits and recovery.

**Exit criteria:** supported optional modules are isolated, documented and verifiably operational.

## Phase 8 — Reliability and release readiness

- Execute regression tests.
- Conduct security review.
- Test recovery and rollback.
- Validate documentation.
- Verify packaging.
- Review all known defects.
- Produce an evidence-based release report.

**Exit criteria:** release claims are supported by actual test results and known limitations are documented.

---

# 26. CHANGE MANAGEMENT AND IMPLEMENTATION RULES

For each task:

1. Understand the current behavior.
2. Identify the smallest correct implementation.
3. Check the relevant workflow and tools.
4. Define acceptance criteria.
5. Make the change.
6. Execute focused tests.
7. Execute relevant regression tests.
8. Inspect the actual diff.
9. Update authorized documentation.
10. Report evidence and limitations.

Do not bundle unrelated changes into one large patch.

Do not refactor stable modules simply because a new architecture appears more elegant.

Do not introduce TODO placeholders in place of requested functionality and then mark the task complete.

Do not claim that a feature exists merely because its UI, configuration or interface has been created.

Do not delete failed tests to obtain a green test suite.

Do not suppress errors without understanding their cause.

If a requirement cannot be completed, implement independent safe work, document the exact blocker and state what is required to finish.

---

# 27. DEFINITION OF DONE

A task is complete only when its applicable criteria are satisfied.

## Implementation
- The actual implementation exists.
- It is integrated into the intended entry point.
- Interfaces and contracts are consistent.
- Existing behavior is preserved or changes are explicitly documented.

## Security
- Required authorization is enforced.
- Inputs are validated.
- Secrets are protected.
- Failure behavior is safe.
- Required approval gates remain effective.

## Testing
- Relevant tests were executed.
- Results were inspected.
- Failures and limitations are recorded.
- Regression risk was assessed.

## Documentation
- Actual behavior is documented.
- New configuration and dependencies are explained.
- Relevant commands and recovery procedures are available.

## Reporting
- Files changed are identified.
- Commands executed are listed.
- Test outcomes are honest.
- Remaining blockers are explicit.
- No unverified capability is represented as complete.

A visually polished mockup, an untested script or an interface disconnected from the runtime does not satisfy the definition of done.

---

# 28. REQUIRED FINAL REPORT

At the end of a substantial work session, provide a concise but evidence-based report.

## A. Environment
- Verified repository root.
- Runtime and relevant versions.
- Available tools.
- Any environmental limitations.

## B. Baseline
- Existing functionality inspected.
- Existing failures.
- Relevant user changes preserved.

## C. Implementation
- Files created.
- Files modified.
- Files intentionally left unchanged.
- Components and integrations implemented.
- Deterministic tools reused or added.
- Work delegated and independently verified, if applicable.

## D. Verification
For each check, provide:

- Command.
- Result.
- Relevant evidence.
- Any limitation.

Use the required status vocabulary.

## E. Security and compatibility
- Security implications.
- Permission changes.
- Dependencies added.
- Compatibility issues.
- Data migration or recovery considerations.

## F. Remaining work
- Incomplete requirements.
- Exact blockers.
- Unverified integrations.
- Tests not run.
- Approval needed.

## G. Next action
Identify the single highest-value next implementation task based on the actual state of the repository.

Do not claim success without evidence.

---

# 29. FIRST EXECUTION DIRECTIVE

When a new implementation session starts, follow this order:

**Step 1:** Verify the real repository root and available environment.

**Step 2:** Read this file and all applicable existing project instructions.

**Step 3:** Audit the actual repository, WAT workflows, deterministic tools, tests, branding, dashboard, runtime and integrations.

**Step 4:** Establish the baseline and identify user changes that must be preserved.

**Step 5:** Create a dependency-aware implementation plan with clear file ownership and acceptance criteria.

**Step 6:** Start the highest-value authorized implementation task immediately after the audit. Do not wait for approval for routine, reversible work already authorized by the user.

**Step 7:** Preserve protected workflows and request approval before modifying them.

**Step 8:** Execute tests and inspect the real outputs.

**Step 9:** Continue with the next safe task until the available session budget or an actual blocker requires stopping.

**Step 10:** Produce the required evidence-based report.

The initial priority is to establish a reliable baseline and then implement the highest-value missing capability. Do not assume that the branding subsystem, distributed runtime or dashboard is absent; inspect before deciding.

---

# FINAL ENGINEERING PRINCIPLE

KRAKEN MESH must be powerful because its architecture is coherent, its execution is controlled, its tools are deterministic where possible, its agents are accountable and its capabilities are verifiable.

Its identity must be memorable because the Kraken creature, color system, typography and composition are deliberately designed—not because the interface is covered in neon.

Its autonomy must be useful because it respects permissions, costs, resource limits and user intent.

Its reliability must be demonstrated through tests, recovery behavior and evidence—not confidence or claims.

**MANY DEVICES. ONE SWARM. YOUR RULES.**

**Inspect the real system. Preserve what works. Build what is missing. Verify everything you claim.**
