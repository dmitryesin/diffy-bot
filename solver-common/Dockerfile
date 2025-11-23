FROM gradle:8.14-jdk21 AS builder

WORKDIR /home/gradle/project

COPY --chown=gradle:gradle settings.gradle.kts settings.gradle.kts
COPY --chown=gradle:gradle build.gradle.kts build.gradle.kts
COPY --chown=gradle:gradle gradle gradle

COPY --chown=gradle:gradle . .

RUN gradle --no-daemon clean bootJar -x test

FROM openjdk:21-ea-jdk-slim

WORKDIR /solver-server

COPY --from=builder /home/gradle/project/build/libs/*.jar app.jar

EXPOSE 8080

CMD ["java", "-jar", "app.jar"]