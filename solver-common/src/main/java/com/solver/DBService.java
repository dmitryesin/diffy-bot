package com.solver;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataAccessException;
import org.springframework.dao.EmptyResultDataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.concurrent.CompletableFuture;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
public class DBService {
    private static final Logger logger = LoggerFactory.getLogger(DBService.class);

    private final JdbcTemplate jdbcTemplate;

    public DBService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Async
    @Transactional
    public CompletableFuture<Optional<String>> getUserSettings(Integer userId) {
        logger.debug("Fetching user settings for userId: {}", userId);
        return CompletableFuture.supplyAsync(() -> {
            String query = """
                SELECT method, rounding, language, hints
                FROM users
                WHERE id = ?
                """;
            
            try {
                return jdbcTemplate.queryForObject(query, (rs, rowNum) -> {
                    String method = rs.getString("method");
                    String rounding = rs.getString("rounding");
                    String language = rs.getString("language");
                    Boolean hints = rs.getBoolean("hints");
                    return Optional.of(
                        String.format(
                            "{\"method\": \"%s\", \"rounding\": \"%s\", \"language\": \"%s\", \"hints\": \"%s\"}",
                            method,
                            rounding,
                            language,
                            hints));
                }, userId);
            } catch (EmptyResultDataAccessException e) {
                logger.debug("No settings found for userId: {}", userId);
                return Optional.empty();
            } catch (DataAccessException e) {
                logger.error("Database error while fetching user settings for userId: {}", userId, e);
                throw new SolverException("Failed to fetch user settings", e);
            }
        });
    }

    @Async
    @Transactional
    public CompletableFuture<Optional<String>> setUserSettings(Integer userId, String method, String rounding, String language, Boolean hints) {
        logger.debug("Setting user settings for userId: {}, method: {}, rounding: {}, language: {}, hints: {}", 
            userId, method, rounding, language, hints);
        return CompletableFuture.supplyAsync(() -> {
            String query = """
                INSERT INTO users (id, method, rounding, language, hints)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (id) DO UPDATE
                SET method = EXCLUDED.method,
                    rounding = EXCLUDED.rounding,
                    language = EXCLUDED.language,
                    hints = EXCLUDED.hints
                """;
            
            try {
                int rowsAffected = jdbcTemplate.update(query, userId, method, rounding, language, hints);
                return rowsAffected > 0 
                    ? Optional.of("Settings saved successfully") 
                    : Optional.empty();
            } catch (DataAccessException e) {
                logger.error("Database error while setting user settings for userId: {}", userId, e);
                throw new SolverException("Failed to save user settings", e);
            }
        });
    }

    @Async
    @Transactional
    public CompletableFuture<Integer> createApplication(String parameters, String status, Integer userId) {
        logger.debug("Creating new application for userId: {} with status: {}", userId, status);
        return CompletableFuture.supplyAsync(() -> {
            String query = """
                INSERT INTO applications (user_id, parameters, status)
                VALUES (?, ?::jsonb, ?)
                RETURNING id
                """;
            try {
                return jdbcTemplate.queryForObject(
                    query,
                    (rs, rowNum) -> rs.getInt("id"),
                    userId,
                    parameters,
                    status
                );
            } catch (DataAccessException e) {
                logger.error("Database error while creating application for userId: {}", userId, e);
                throw new SolverException("Failed to create application", e);
            }
        });
    }

    @Async
    @Transactional
    public CompletableFuture<List<Map<String, Object>>> getApplications(Integer userId) {
        logger.debug("Fetching applications for userId: {}", userId);
        return CompletableFuture.supplyAsync(() -> {
            String query = """
                SELECT id, parameters, status, created_at, last_updated_at
                FROM applications
                WHERE user_id = ?
                ORDER BY created_at DESC
                """;
            try {
                return jdbcTemplate.query(query, (rs, rowNum) -> {
                    Map<String, Object> application = new HashMap<>();
                    application.put("id", rs.getInt("id"));
                    application.put("parameters", rs.getString("parameters"));
                    application.put("status", rs.getString("status"));
                    application.put("created_at", rs.getString("created_at"));
                    application.put("last_updated_at", rs.getString("last_updated_at"));
                    return application;
                }, userId);
            } catch (DataAccessException e) {
                logger.error("Database error while fetching applications for userId: {}", userId, e);
                throw new SolverException("Failed to fetch applications", e);
            }
        });
    }

    @Async
    @Transactional
    public CompletableFuture<Optional<List<Double>>> getXValues(int applicationId) {
        logger.debug("Fetching x values for applicationId: {}", applicationId);
        return CompletableFuture.supplyAsync(() -> {
            String query = """
                SELECT jsonb_array_elements_text(data->'xvalues')::double precision AS x_value
                FROM results
                WHERE application_id = ?
                """;
            try {
                List<Double> xValues = jdbcTemplate.queryForList(query, Double.class, applicationId);
                return xValues.isEmpty() ? Optional.empty() : Optional.of(xValues);
            } catch (DataAccessException e) {
                logger.error("Database error while fetching x values for applicationId: {}", applicationId, e);
                throw new SolverException("Failed to fetch x values", e);
            }
        });
    }

    @Async
    @Transactional
    public CompletableFuture<Optional<List<double[]>>> getYValues(int applicationId) {
        logger.debug("Fetching y values for applicationId: {}", applicationId);
        return CompletableFuture.supplyAsync(() -> {
            String query = """
                SELECT jsonb_array_elements(data->'yvalues')::jsonb AS y_value
                FROM results
                WHERE application_id = ?
                """;
            try {
                List<String> yValuesJson = jdbcTemplate.queryForList(query, String.class, applicationId);
                if (yValuesJson.isEmpty()) {
                    return Optional.empty();
                }
                
                ObjectMapper objectMapper = new ObjectMapper();
                List<double[]> yValues = new ArrayList<>();
                for (String json : yValuesJson) {
                    yValues.add(objectMapper.readValue(json, double[].class));
                }
                return Optional.of(yValues);
            } catch (DataAccessException e) {
                logger.error("Database error while fetching y values for applicationId: {}", applicationId, e);
                throw new SolverException("Failed to fetch y values", e);
            } catch (JsonProcessingException e) {
                logger.error("JSON processing error while parsing y values for applicationId: {}", applicationId, e);
                throw new SolverException("Failed to parse y values", e);
            }
        });
    }

    @Async
    @Transactional
    public CompletableFuture<Optional<double[]>> getSolution(int applicationId) {
        logger.debug("Fetching solution for applicationId: {}", applicationId);
        return CompletableFuture.supplyAsync(() -> {
            String query = """
                SELECT data->>'solution' AS solution
                FROM results
                WHERE application_id = ?
                """;
            try {
                List<String> solutions = jdbcTemplate.queryForList(query, String.class, applicationId);
                if (solutions.isEmpty()) {
                    return Optional.empty();
                }
                
                ObjectMapper objectMapper = new ObjectMapper();
                return Optional.of(objectMapper.readValue(solutions.getFirst(), double[].class));
            } catch (DataAccessException e) {
                logger.error("Database error while fetching solution for applicationId: {}", applicationId, e);
                throw new SolverException("Failed to fetch solution", e);
            } catch (JsonProcessingException e) {
                logger.error("JSON processing error while parsing solution for applicationId: {}", applicationId, e);
                throw new SolverException("Failed to parse solution", e);
            }
        });
    }

    @Async
    @Transactional
    public CompletableFuture<Optional<String>> getApplicationStatus(int applicationId) {
        logger.debug("Fetching status for applicationId: {}", applicationId);
        return CompletableFuture.supplyAsync(() -> {
            String query = """
                SELECT status
                FROM applications
                WHERE id = ?
                """;
            try {
                List<String> statuses = jdbcTemplate.queryForList(query, String.class, applicationId);
                return statuses.isEmpty() ? Optional.empty() : Optional.of(statuses.getFirst());
            } catch (DataAccessException e) {
                logger.error("Database error while fetching status for applicationId: {}", applicationId, e);
                throw new SolverException("Failed to fetch application status", e);
            }
        });
    }

    @Async
    @Transactional
    public CompletableFuture<Void> updateApplicationStatus(int applicationId, String status) {
        logger.debug("Updating status to {} for applicationId: {}", status, applicationId);
        return CompletableFuture.runAsync(() -> {
            String query = """
                UPDATE applications
                SET status = ?, last_updated_at = NOW()
                WHERE id = ?
                """;
            try {
                jdbcTemplate.update(query, status, applicationId);
            } catch (DataAccessException e) {
                logger.error("Database error while updating status for applicationId: {}", applicationId, e);
                throw new SolverException("Failed to update application status", e);
            }
        });
    }

    @Async
    @Transactional
    public CompletableFuture<Void> saveResults(int applicationId, String results) {
        logger.debug("Saving results for applicationId: {}", applicationId);
        return CompletableFuture.runAsync(() -> {
            String query = """
                INSERT INTO results (application_id, data)
                VALUES (?, ?::jsonb)
                """;
            try {
                jdbcTemplate.update(query, applicationId, results);
            } catch (DataAccessException e) {
                logger.error("Database error while saving results for applicationId: {}", applicationId, e);
                throw new SolverException("Failed to save results", e);
            }
        });
    }

    @Async
    @Scheduled(cron = "0 */15 * * * *") // Every 15 minutes
    @Transactional
    public CompletableFuture<Void> cleanOldApplications() {
        logger.debug("Starting scheduled cleanup of old applications");
        return CompletableFuture.runAsync(() -> {
            String query = """
                WITH ranked_applications AS (
                    SELECT id, user_id, created_at,
                        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS row_num
                    FROM applications
                ),
                to_delete AS (
                    SELECT id
                    FROM ranked_applications
                    WHERE row_num > 5
                    AND created_at < NOW() - INTERVAL '14 days'
                )
                DELETE FROM applications
                WHERE id IN (SELECT id FROM to_delete)
                """;
            
            try {
                int deletedCount = jdbcTemplate.update(query);
                logger.debug("Cleaned up {} old applications", deletedCount);
            } catch (DataAccessException e) {
                logger.error("Database error while cleaning old applications", e);
                throw new SolverException("Failed to clean old applications", e);
            }
        });
    }
}