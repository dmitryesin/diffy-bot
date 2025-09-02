FROM gradle:8.14-jdk21 AS builder

WORKDIR /solver-server

COPY solver-common/build.gradle.kts solver-common/settings.gradle.kts solver-common/gradlew ./
COPY solver-common/gradle ./gradle

RUN chmod +x ./gradlew

RUN ./gradlew dependencies --no-daemon || true

COPY solver-common ./

RUN ./gradlew bootJar -x test --no-daemon

FROM openjdk:21-slim

WORKDIR /solver-server

COPY --from=builder /solver-server/build/libs/*.jar app.jar

CMD ["java", "-jar", "app.jar"]