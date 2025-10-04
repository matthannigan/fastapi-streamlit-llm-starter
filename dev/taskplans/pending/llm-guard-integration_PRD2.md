# PRD: `llm-guard` Integration with Flexible Deployment (Local & SaaS)

## Overview

This document outlines the plan to integrate the `llm-guard` library into the FastAPI starter template, replacing the existing custom, regex-based security modules. This initiative will now offer a **flexible deployment model**, allowing template users to either run `llm-guard`'s ML models locally or connect to a SaaS provider (like ProtectAI Guardian) via an API.

This integration solves two key problems: it replaces a high-maintenance, custom security system with an industry-standard tool, and it gives developers a choice to offload the significant resource costs (RAM, Docker image size) associated with running security ML models. It's for developers who need production-grade AI security but have varying infrastructure capabilities and budgets. The value is in providing a starter template that is **secure by default and adaptable by design**.

-----

## Core Features

The integration will introduce the following core features.

### 1\. Flexible Security Deployment (Local vs. SaaS) 🆕

  - **What it does**: Allows developers to choose their security backend via a single environment variable (`LLM_GUARD_MODE=local|saas`). The `local` mode runs the `llm-guard` library directly, while the `saas` mode makes API calls to an external security provider.
  - **Why it's important**: This is the primary mitigation for the high resource utilization of `llm-guard`. Users on resource-constrained systems can offload the performance impact, while others can maintain a fully self-hosted environment.
  - **How it works**: An abstract `LLMGuardBaseService` will define the security contract. Two concrete implementations (`LocalLLMGuardService`, `SaaSLLMGuardService`) will be created. A factory in `dependencies.py` will provide the correct implementation based on the `LLM_GUARD_MODE` setting.

### 2\. Advanced Input Sanitization & Threat Detection

  - **What it does**: Replaces the regex sanitizer with `llm-guard`'s input scanners (e.g., `PromptInjection`, `Toxicity`, `Secrets`). This functionality will be available in both `local` and `saas` modes.
  - **Why it's important**: It provides superior, ML-powered protection against a wider range of threats than the previous regex-based system.
  - **How it works**: The active `LLMGuardService` implementation will be used by the `TextProcessorService` to scan all incoming user text.

### 3\. Robust Output Validation

  - **What it does**: Implements a new security layer to validate LLM-generated responses using `llm-guard`'s output scanners (e.g., `NoRefusal`, `Sensitive`, `Relevance`).
  - **Why it's important**: Protects against model misbehavior and data leakage, a critical security step identified as a "future enhancement" in the current codebase.
  - **How it works**: The `TextProcessorService` will use the active `LLMGuardService` to scan all LLM responses before they are returned to the user.

### 4\. Preset-Based Security Configuration

  - **What it does**: For `local` mode, introduces `LLM_GUARD_PRESET` to easily select a security level (`development`, `production`). For `saas` mode, configuration will be managed by the provider.
  - **Why it's important**: Simplifies security configuration and aligns with the template's existing preset patterns (`CACHE_PRESET`, `RESILIENCE_PRESET`).
  - **How it works**: The `LocalLLMGuardService` will load scanners based on the selected preset.

-----

## User Experience

The "user" is the **application developer** using the starter template.

  - **User Persona**: A developer who values security but needs to balance it with performance, cost, and infrastructure constraints.
  - **Key User Flows**:
    1.  **Self-Hosted Flow**: A developer with sufficient server resources sets `LLM_GUARD_MODE=local` and `LLM_GUARD_PRESET=production`. They accept the higher resource usage for a fully self-contained application.
    2.  **SaaS Flow**: A developer on a smaller server or with a preference for managed services sets `LLM_GUARD_MODE=saas`, provides their `PROTECTAI_API_KEY`, and offloads all security processing, keeping their application lightweight.
    3.  **Seamless Integration**: In both flows, the developer's interaction with the `TextProcessorService` remains identical. The security backend is an abstracted detail.
  - **UI/UX Considerations**: The primary goal is to empower developers with a clear choice. The configuration should be simple and well-documented. The abstraction should ensure that switching between `local` and `saas` modes is trivial and does not require code changes in the domain logic.

-----

## Technical Architecture

### System Components

1.  **New Abstract Service (`app/infrastructure/ai/llm_guard_base_service.py`)**: An abstract base class defining the `scan_input` and `scan_output` methods.
2.  **New Local Implementation (`app/infrastructure/ai/llm_guard_local_service.py`)**: The implementation that uses the `llm-guard` Python library. It will initialize scanners based on the `LLM_GUARD_PRESET`.
3.  **New SaaS Implementation (`app/infrastructure/ai/llm_guard_saas_service.py`)**: The implementation that uses `httpx` to make API calls to the SaaS provider's endpoint.
4.  **Configuration (`app/core/config.py`)**: The `Settings` class will be updated with:
      * `LLM_GUARD_MODE: str`
      * `LLM_GUARD_PRESET: str` (for local mode)
      * `PROTECTAI_API_KEY: str` (for saas mode)
      * `PROTECTAI_API_URL: str` (for saas mode)
5.  **Dependency Injection (`app/dependencies.py`)**: The `get_llm_guard_service()` dependency will be updated to a factory that returns an instance of either the local or SaaS service based on `LLM_GUARD_MODE`.
6.  **Service Refactoring (`app/services/text_processor.py`)**: This service will inject `LLMGuardBaseService` and use it for all input and output scanning.
7.  **Module Deletion**: `input_sanitizer.py` and `response_validator.py` will be deleted.

-----

## Development Roadmap

### Phase 1: Abstract Service and Local Implementation

  - **Scope**:
      - Add `llm-guard` as a dependency.
      - Create the `LLMGuardBaseService` abstract class.
      - Build the `LocalLLMGuardService` implementation.
      - Implement the preset configuration system (`LLM_GUARD_MODE` and `LLM_GUARD_PRESET`).
      - Update `dependencies.py` with the factory logic (initially just for `local` mode).
      - Refactor `TextProcessorService` to use the new service for both input and output scanning.
      - Delete all old security modules.
  - **Goal**: Achieve a fully functional, self-hosted security system based on `llm-guard`.

### Phase 2: SaaS Implementation and Documentation

  - **Scope**:
      - Build the `SaaSLLMGuardService` implementation that connects to the ProtectAI Guardian API.
      - Update the dependency factory to support the new `saas` mode.
      - Add the new SaaS-related environment variables to the configuration.
      - Thoroughly update all documentation to explain the two deployment modes, their trade-offs, and how to configure them.
  - **Goal**: Provide users with a production-ready alternative that offloads resource consumption.

-----

## Logical Dependency Chain

1.  **Foundation First**: The abstract base class (`LLMGuardBaseService`) and the factory pattern in `dependencies.py` are the essential first steps.
2.  **Local Implementation**: Build the `LocalLLMGuardService`. This makes the feature usable for self-hosting users and completes the replacement of the old code.
3.  **SaaS Implementation**: With the abstraction in place, the `SaaSLLMGuardService` can be built as a separate, parallel effort.
4.  **Documentation**: Finalize documentation after both implementations are complete to ensure all configuration paths are covered.

-----

## Risks and Mitigations

  - **Risk**: (For `local` mode) `llm-guard` and its dependencies will significantly increase resource utilization.
      - **Mitigation**: **This is now the primary reason for offering the `saas` mode.** The PRD explicitly provides an offloading path. For users of `local` mode, the `development` preset will use lightweight scanners to keep the DX smooth.
  - **Risk**: The SaaS provider could have downtime or add latency.
      - **Mitigation**: The `SaaSLLMGuardService` must be wrapped with the application's existing resilience infrastructure (circuit breakers and retries), just like any other external API call. This is a core strength of the template's architecture.
  - **Risk**: Maintaining two separate implementations (`local` and `saas`) adds complexity to the template.
      - **Mitigation**: A clean abstraction (`LLMGuardBaseService`) is key. As long as both implementations adhere to the same simple interface, the complexity will be well-contained within the infrastructure layer, leaving the domain logic untouched.

-----

## Appendix

### Example `.env` Configuration

```ini
# .env file

# --- OPTION 1: Self-Hosted Security (Resource Intensive) ---
LLM_GUARD_MODE=local
# Choose a preset for local mode: development | production | strict
LLM_GUARD_PRESET=production


# --- OPTION 2: SaaS-Based Security (Lightweight) ---
# LLM_GUARD_MODE=saas
# PROTECTAI_API_KEY="sk-xxxxxxxxxxxxxxxx"
# PROTECTAI_API_URL="https://api.protectai.com/guardian"
```