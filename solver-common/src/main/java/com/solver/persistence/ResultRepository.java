package com.solver.persistence;

import com.solver.dto.ResultEntry;
import com.solver.exception.SolverException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.concurrent.CompletableFuture;

@Repository
public class ResultRepository {
    private static final Logger logger = LoggerFactory.getLogger(ResultRepository.class);

    private final JdbcTemplate jdbcTemplate;

    public ResultRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Async
    @Transactional
    public CompletableFuture<Void> saveResults(int applicationId, String results) {
        logger.debug("Saving results for applicationId: {}", applicationId);
        String query = """
            INSERT INTO results (application_id, data)
            VALUES (?, ?::jsonb)
            """;
        try {
            jdbcTemplate.update(query, applicationId, results);
            return CompletableFuture.completedFuture(null);
        } catch (DataAccessException e) {
            logger.error("Database error while saving results for applicationId: {}", applicationId, e);
            throw new SolverException("Failed to save results", e);
        }
    }

    @Async
    @Transactional
    public CompletableFuture<List<ResultEntry>> getResults(int applicationId) {
        logger.debug("Fetching results for applicationId: {}", applicationId);
        String query = """
            SELECT id, data, created_at
            FROM results
            WHERE application_id = ?
            """;
        try {
            List<ResultEntry> results = jdbcTemplate.query(query, (rs, rowNum) -> new ResultEntry(
                    rs.getInt("id"),
                    rs.getString("data"),
                    rs.getString("created_at")
            ), applicationId);
            return CompletableFuture.completedFuture(results);
        } catch (DataAccessException e) {
            logger.error("Database error while fetching results for applicationId: {}", applicationId, e);
            throw new SolverException("Failed to fetch results", e);
        }
    }
}
