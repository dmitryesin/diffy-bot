FROM openjdk:21-slim AS builder

WORKDIR /solver-server

RUN apt-get update && \
    apt-get install -y --no-install-recommends maven && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY solver-common/pom.xml .
RUN mvn dependency:go-offline

COPY solver-common .
RUN mvn clean package -DskipTests -B

FROM openjdk:21-slim

WORKDIR /solver-server

COPY --from=builder /solver-server/target/solver-0.1.2-alpha.jar /solver-server/solver-0.1.2-alpha.jar

CMD ["java", "-jar", "solver-0.1.2-alpha.jar"]