package com.solver.persistence;

import com.solver.config.SolverProperties;
import com.solver.dto.ApplicationSummary;
import com.solver.exception.SolverException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;

@Repository
public class ApplicationRepository {
    private static final Logger logger = LoggerFactory.getLogger(ApplicationRepository.class);

    private final JdbcTemplate jdbcTemplate;
    private final SolverProperties properties;

    public ApplicationRepository(JdbcTemplate jdbcTemplate, SolverProperties properties) {
        this.jdbcTemplate = jdbcTemplate;
        this.properties = properties;
    }

    @Async
    @Transactional
    public CompletableFuture<Integer> createApplication(String parameters, String status, Long userId) {
        logger.debug("Creating new application for userId: {} with status: {}", userId, status);
        String query = """
            INSERT INTO applications (user_id, parameters, status)
            VALUES (?, ?::jsonb, ?)
            RETURNING id
            """;
        try {
            Integer id = jdbcTemplate.queryForObject(
                    query,
                    (rs, rowNum) -> rs.getInt("id"),
                    userId,
                    parameters,
                    status
            );
            return CompletableFuture.completedFuture(id);
        } catch (DataAccessException e) {
            logger.error("Database error while creating application for userId: {}", userId, e);
            throw new SolverException("Failed to create application", e);
        }
    }

    @Async
    @Transactional
    public CompletableFuture<List<ApplicationSummary>> getApplications(Long userId) {
        logger.debug("Fetching applications for userId: {}", userId);
        String query = """
            SELECT id, parameters, status, created_at, last_updated_at
            FROM applications
            WHERE user_id = ?
            AND status = 'completed'
            ORDER BY created_at DESC
            LIMIT ?
            """;
        try {
            List<ApplicationSummary> applications = jdbcTemplate.query(query, (rs, rowNum) -> new ApplicationSummary(
                    rs.getInt("id"),
                    rs.getString("parameters"),
                    rs.getString("status"),
                    rs.getString("created_at"),
                    rs.getString("last_updated_at")
            ), userId, properties.maxStoredApplicationsPerUser());
            return CompletableFuture.completedFuture(applications);
        } catch (DataAccessException e) {
            logger.error("Database error while fetching applications for userId: {}", userId, e);
            throw new SolverException("Failed to fetch applications", e);
        }
    }

    @Async
    @Transactional
    public CompletableFuture<Optional<String>> getApplicationStatus(int applicationId) {
        logger.debug("Fetching status for applicationId: {}", applicationId);
        String query = """
            SELECT status
            FROM applications
            WHERE id = ?
            """;
        try {
            List<String> statuses = jdbcTemplate.queryForList(query, String.class, applicationId);
            Optional<String> status = statuses.isEmpty() ? Optional.empty() : Optional.of(statuses.getFirst());
            return CompletableFuture.completedFuture(status);
        } catch (DataAccessException e) {
            logger.error("Database error while fetching status for applicationId: {}", applicationId, e);
            throw new SolverException("Failed to fetch application status", e);
        }
    }

    @Async
    @Transactional
    public CompletableFuture<Void> updateApplicationStatus(int applicationId, String status) {
        logger.debug("Updating status to {} for applicationId: {}", status, applicationId);
        String query = """
            UPDATE applications
            SET status = ?, last_updated_at = NOW()
            WHERE id = ?
            """;
        try {
            jdbcTemplate.update(query, status, applicationId);
            return CompletableFuture.completedFuture(null);
        } catch (DataAccessException e) {
            logger.error("Database error while updating status for applicationId: {}", applicationId, e);
            throw new SolverException("Failed to update application status", e);
        }
    }

    @Async
    @Scheduled(cron = "0 0 0,12 * * *")
    @Transactional
    public CompletableFuture<Void> cleanOldApplications() {
        logger.debug("Starting scheduled cleanup of old applications");
        String query = """
            WITH ranked_applications AS (
                SELECT id, user_id, created_at,
                    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS row_num
                FROM applications
            ),
            to_delete AS (
                SELECT id
                FROM ranked_applications
                WHERE row_num > ?
                AND created_at < NOW() - make_interval(days => ?)
            )
            DELETE FROM applications
            WHERE id IN (SELECT id FROM to_delete)
            """;

        try {
            int deletedCount = jdbcTemplate.update(
                    query,
                    properties.maxStoredApplicationsPerUser(),
                    properties.applicationRetentionDays());
            logger.debug("Cleaned up {} old applications", deletedCount);
            return CompletableFuture.completedFuture(null);
        } catch (DataAccessException e) {
            logger.error("Database error while cleaning old applications", e);
            throw new SolverException("Failed to clean old applications", e);
        }
    }
}
