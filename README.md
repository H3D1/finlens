# FinLens — Project Brief

## Overview

FinLens is a personal fintech portfolio project that aggregates data from multiple mock financial accounts into a single unified view, surfaces proactive spending insights, and runs a background fraud/anomaly check on transaction activity.

The project is built to demonstrate three real, current fintech engineering themes in one coherent system: open banking-style data aggregation, AI-adjacent insight generation, and fraud detection — rather than three disconnected demos.

## Current status

- Backend service: Spring Boot 3.4.1
- Verified runtime: Java 17.0.19
- Verified build tool: Maven 3.9.16
- Validation command: `mvn clean test`
- Validation result: `BUILD SUCCESS`
- Active module: `aggregation-service`

## Why this project

Current fintech industry trends point to three specific gaps this project addresses directly:

- **Aggregation:** Open banking and API-first infrastructure are a core 2026 fintech theme — fintechs are increasingly built as modular platforms that unify data across sources rather than siloed apps.
- **Insight generation:** Consumer research shows most fintech app users want proactive financial guidance, not just raw data — and most apps currently fail to deliver this.
- **Fraud detection:** Fraud is becoming more sophisticated industry-wide, making anomaly detection a standard, expected layer in any transaction-handling system.

## Core features (v1 scope)

1. **Account aggregation**
   - 2-3 mock account types (e.g. checking, savings, credit card), each with seeded synthetic transaction data
   - Single unified API response normalizing all account types into one schema

2. **Proactive insights**
   - Rule-based observations generated from aggregated data, e.g.:
     - Spending increase by category, month over month
     - Recurring subscription detection
     - Balance trend projection (days until threshold at current rate)

3. **Fraud/anomaly check**
   - Runs as a background check on incoming transactions, not a separate module
   - Starts rule-based (velocity checks, per-user deviation from historical average) with room to extend to a statistical (z-score) or lightweight ML (Isolation Forest) approach later

## Architecture

- **Backend:** Spring Boot (Java) — REST API, JWT authentication
- **Frontend:** React — dashboard showing aggregated accounts, insights, and flagged activity
- **Database:** PostgreSQL
- **Containerization:** Docker + Docker Compose
- **Deployment:** AWS EC2 (t3.micro) + RDS (db.t3.micro)
- **CI/CD:** GitHub Actions — build and test on push

## Explicitly out of scope for v1

- Real bank/payment integration of any kind
- Kubernetes or multi-region deployment
- Mobile app
- Complex multi-user roles or permissions beyond basic auth

## Cost estimate

Estimated **€0/month** for the first 12 months using AWS free tier (EC2 + RDS), with a billing alert set at $5 as a safeguard. After the free tier period, estimated **€10-15/month** if kept running continuously — recommend stopping/terminating resources once the project has served its demonstration purpose.

## Success criteria

- Live, publicly accessible deployment with a real URL
- Clean, documented GitHub repository pinned under the primary account
- At least one blog post derived from the build (technical deep-dive, cloud/infra decisions, or the insight/fraud logic)
- Demonstrable in an interview: can explain the aggregation schema, the insight rules, and the anomaly detection approach without notes