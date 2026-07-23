# Aggregation Service

Aggregation service for combining and processing financial data.

## Run

```bash
mvn spring-boot:run
```

The unauthenticated `GET /accounts` endpoint returns seeded accounts with their transactions. Configure PostgreSQL credentials in `src/main/resources/application.properties` before starting the service.
