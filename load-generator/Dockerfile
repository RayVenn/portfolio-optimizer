# ── Stage 1: build fat JAR ────────────────────────────────────────────────────
FROM eclipse-temurin:25-jdk AS builder

WORKDIR /app

COPY gradlew .
COPY gradle/ gradle/
COPY settings.gradle build.gradle ./
COPY load-generator/build.gradle load-generator/build.gradle
COPY load-generator/src         load-generator/src
# Stubs for other subprojects so Gradle 9 doesn't reject missing dirs
RUN mkdir -p producer/src flink/jobs

RUN ./gradlew :load-generator:shadowJar --no-daemon

# ── Stage 2: minimal JRE runtime ──────────────────────────────────────────────
FROM eclipse-temurin:25-jre-jammy

WORKDIR /app

COPY --from=builder /app/load-generator/build/libs/load-generator-*.jar app.jar

CMD ["java", "-jar", "app.jar"]
