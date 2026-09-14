FROM eclipse-temurin:21-jdk AS builder

WORKDIR /home/gradle/project

COPY gradlew gradlew
COPY gradle gradle
COPY settings.gradle.kts build.gradle.kts ./

RUN sed -i 's/\r$//' gradlew && chmod +x gradlew

RUN --mount=type=cache,target=/home/gradle/.gradle \
    ./gradlew --no-daemon dependencies

COPY src src

RUN --mount=type=cache,target=/home/gradle/.gradle \
    ./gradlew --no-daemon clean bootJar -x test


FROM eclipse-temurin:21-jre

RUN useradd --create-home --uid 10001 solver-server

WORKDIR /solver-server

RUN mkdir -p logs && chown -R 10001:10001 logs

COPY --from=builder --chown=10001:10001 /home/gradle/project/build/libs/app.jar app.jar

USER solver-server

EXPOSE 8080

CMD ["java", "-jar", "app.jar"]