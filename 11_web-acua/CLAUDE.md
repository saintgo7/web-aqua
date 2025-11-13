# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**TripFuture** is an AI-powered travel platform (Ruby on Rails 8.0) serving three user personas:
- Solo travelers seeking cultural experiences
- Families needing child-friendly recommendations
- Senior travelers preferring comfortable itineraries

The platform features personalized AI recommendations, intelligent search, collaborative itinerary planning, unified booking with Korean payment methods, and multilingual support (Korean/English).

**Current Status**: Feature specification and planning phase (branch: `002-ai-ai`)
**Tech Stack**: Ruby 3.2.0, Rails 8.0, PostgreSQL, Redis, Sidekiq, Tailwind CSS

## Essential Commands

### Development Setup
```bash
# Install dependencies
bundle install
bundle exec rails db:create db:migrate

# Start development server
bin/rails server

# Start Rails console
bin/rails console
```

### Testing
```bash
# Run all tests
bundle exec rspec

# Run specific test file
bundle exec rspec spec/features/auth_spec.rb

# Run with coverage
bundle exec rspec --format progress --require spec_helper

# Run integration tests only
bundle exec rspec spec/integration

# Run a single test by name
bundle exec rspec -e "test_name_pattern"
```

### Database
```bash
# Create and migrate
bundle exec rails db:create db:migrate

# Rollback latest migration
bundle exec rails db:rollback

# Reset database (development)
bundle exec rails db:reset

# Run specific migration
bundle exec rails db:migrate:up VERSION=20250913000000
```

### Code Quality
```bash
# RuboCop (linting)
bundle exec rubocop

# Auto-fix RuboCop violations
bundle exec rubocop -A

# Run tests in strict mode
RAILS_ENV=test bundle exec rspec --strict-warnings
```

### Background Jobs
```bash
# Run Sidekiq worker
bundle exec sidekiq

# Monitor jobs
bundle exec sidekiq-status
```

## Architecture Overview

### Project Structure

The application follows Rails conventions with modular organization:

```
app/
├── models/          # Active Record models (User, Destination, Booking, etc.)
├── controllers/     # Request handlers for each resource
├── views/          # ERB templates with Turbo/Stimulus
├── channels/       # ActionCable channels (ItineraryChannel for real-time collab)
├── jobs/           # Sidekiq background jobs (price updates, AI processing)
├── services/       # Business logic layer (PaymentService, AIRecommendationService)
└── helpers/        # View helpers

config/
├── database.yml    # PostgreSQL configuration
├── redis.yml       # Redis cache/session configuration
└── puma.rb         # Web server configuration

spec/
├── models/         # Unit tests for models
├── integration/    # Integration tests (API, workflows)
├── features/       # End-to-end tests (user flows, Capybara)
└── factories/      # FactoryBot model fixtures
```

### Core Design Decisions

#### Authentication
- **Rails 8.0 built-in authentication** (not Devise) for simpler customization and security defaults
- Supports email + social login (Kakao, Naver, Google, Apple)
- 2FA and password reset via email

#### AI Integration
- **ruby-openai gem** for GPT integration (recommendations, chatbot, explanations)
- **Sidekiq** for async AI processing to avoid blocking requests
- Python FastAPI service option for complex ML models (if needed later)

#### Real-time Collaboration
- **ActionCable with Redis pub/sub** for live itinerary updates
- **Turbo Streams** for optimistic UI updates
- Presence tracking for collaborative sessions

#### Payment Processing
- **Direct API integration** with Korean gateways (KakaoPay, NaverPay, TossPay)
- **ActiveMerchant gem** for payment abstraction
- **Tokenization** to minimize PCI-DSS scope (never store card details)
- Support for international methods (PayPal)

#### Internationalization
- **Rails I18n** with YAML locale files (Korean/English)
- Locale detection from Accept-Language headers
- Per-locale formatting for currency/dates

### Key Entities

The data model includes:
- **User**: Profile, preferences, travel history, social connections
- **Travel Profile**: Style, interests, companions, special needs
- **Destination**: Attractions, safety ratings, weather, AI insights
- **Flight/Accommodation/Activity**: Searchable travel products
- **Itinerary**: AI-generated or user-created travel plans with budget tracking
- **Booking**: Reservations with payment and modification history
- **AI Recommendation**: Suggestions with reasoning and confidence scores
- **Chat Session**: Support conversations with context
- **Community Group**: Themed travel planning groups

## Development Workflow

### Testing Requirements (NON-NEGOTIABLE)

This project enforces **RED-GREEN-REFACTOR**:

1. **Write failing test first** (RED phase) - test must fail
2. **Implement minimum code** (GREEN phase) - make test pass
3. **Refactor** (REFACTOR phase) - clean up while tests pass

**Test Order**:
- Contract tests → Integration tests → E2E tests → Unit tests
- Git commits should show test addition before implementation
- Real dependencies: PostgreSQL test DB, Redis test instance

**Test Types**:
- **Integration**: API endpoints, database queries, external services
- **Feature**: Full user workflows (Capybara)
- **Unit**: Model methods, helpers, services

**Forbidden**:
- Implementing before writing tests
- Skipping RED phase
- Using stubs/mocks for integrations (use real DB/Redis)

### Common Patterns

#### Service Objects (Business Logic)
```ruby
# app/services/ai_recommendation_service.rb
class AIRecommendationService
  def call(user)
    # Complex AI logic delegated to OpenAI
  end
end
```

Services handle business logic separate from controllers. Tests call services directly.

#### Background Jobs
```ruby
# app/jobs/update_flight_prices_job.rb
class UpdateFlightPricesJob
  include Sidekiq::Job

  def perform
    # Async price fetching
  end
end
```

Use Sidekiq for long-running operations (AI processing, price updates, email sending).

#### Real-time Collaboration
```ruby
# app/channels/itinerary_channel.rb
class ItineraryChannel < ApplicationCable::Channel
  def subscribed
    stream_for @itinerary  # Live updates via ActionCable
  end
end
```

Turbo Streams automatically update UI when other users modify shared itineraries.

## Important Configuration

### Security & Compliance

- **PCI-DSS L1**: Tokenization prevents card storage; quarterly QSA audits required
- **GDPR/PIPA**: User data export/deletion, consent tracking, minimal retention
- **WCAG 2.1 AA**: All UI must be accessible (color contrast, keyboard nav, screen readers)
- **Encryption**: AES-256 at rest, TLS 1.2+ in transit
- **Rate Limiting**: 1000 req/hr per user, 10,000 req/hr per IP (Rack::Attack gem)

### Performance Targets

- Page load < 3s on 3G networks
- API response time < 200ms
- Support 1,000 concurrent users
- Cache with Redis for frequently accessed data (destinations, recommendations)

### Compliance Checklist

Before deployment:
- [ ] PCI-DSS requirements met (payment tokenization, SSL)
- [ ] GDPR/PIPA policies implemented (retention, deletion)
- [ ] WCAG 2.1 AA accessibility audit passed
- [ ] Rate limiting configured
- [ ] Error logging includes request ID, user context
- [ ] No PII in logs or git history

## Specification & Documentation

### Key Files

The feature specification is maintained in `/specs/002-ai-ai/`:

- **spec.md**: Detailed functional/non-functional requirements (50 FR + 33 NFR)
- **plan.md**: Implementation architecture and technical decisions
- **research.md**: Technology choices and rationale
- **tasks.md**: Incremental implementation tasks (created by `/tasks` command)
- **data-model.md**: Database schema and relationships (Phase 1)
- **quickstart.md**: Getting started guide (Phase 1)
- **contracts/**: API contract specifications (Phase 1)

### When Referencing the Spec

The spec includes clarifications on:
- Three user personas with specific needs
- Multi-stage booking flow (search → plan → book)
- AI explanation requirements (reasoning, factors, confidence score)
- Payment method support (Korean + international)
- Real-time collaboration features
- Community content moderation (24-hour SLA)

## Common Issues & Solutions

### Payment Testing
- Use [payment gateway sandbox credentials](./specs/002-ai-ai/spec.md#fr-027) for testing
- Never commit real API keys; use environment variables
- Test tokenization flow without storing card details

### AI Response Time
- Long AI requests should be async jobs via Sidekiq
- Cache common recommendations in Redis
- Implement streaming responses for chat where appropriate

### Real-time Sync Issues
- Redis must be running for ActionCable and Sidekiq
- Test with multiple browser tabs to verify live updates
- Check Rails logs for WebSocket connection issues

### Database Migrations
- Always write both `up` and `down` methods
- Test rollbacks locally before deploying
- Use `change` method for reversible migrations only

## Continuous Improvement

When adding features:
1. **Update spec first** if requirements clarify
2. **Add integration tests** demonstrating the feature
3. **Document new services** with YARD comments
4. **Update this CLAUDE.md** if architecture changes
5. **Check compliance** against GDPR/PIPA/WCAG requirements

This repository uses semantic versioning; increment BUILD on every change in CI/CD pipeline.
