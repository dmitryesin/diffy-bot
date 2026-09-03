package com.solver.persistence;

import com.solver.dto.UserSettings;
import com.solver.exception.SolverException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataAccessException;
import org.springframework.dao.EmptyResultDataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;
import java.util.concurrent.CompletableFuture;

@Repository
public class UserSettingsRepository {
    private static final Logger logger = LoggerFactory.getLogger(UserSettingsRepository.class);

    private final JdbcTemplate jdbcTemplate;

    public UserSettingsRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Async
    @Transactional
    public CompletableFuture<Optional<UserSettings>> getUserSettings(Long userId) {
        logger.debug("Fetching user settings for userId: {}", userId);
        String query = """
            SELECT method, rounding, language, hints
            FROM users
            WHERE id = ?
            """;

        try {
            UserSettings settings = jdbcTemplate.queryForObject(query, (rs, rowNum) -> new UserSettings(
                    rs.getString("method"),
                    String.valueOf(rs.getInt("rounding")),
                    rs.getString("language"),
                    String.valueOf(rs.getBoolean("hints"))
            ), userId);
            return CompletableFuture.completedFuture(Optional.ofNullable(settings));
        } catch (EmptyResultDataAccessException e) {
            logger.debug("No settings found for userId: {}", userId);
            return CompletableFuture.completedFuture(Optional.empty());
        } catch (DataAccessException e) {
            logger.error("Database error while fetching user settings for userId: {}", userId, e);
            throw new SolverException("Failed to fetch user settings", e);
        }
    }

    @Async
    @Transactional
    public CompletableFuture<Boolean> setUserSettings(Long userId, UserSettings settings) {
        logger.debug("Setting user settings for userId: {}, settings: {}", userId, settings);
        String query = """
            INSERT INTO users (id, method, rounding, language, hints)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE
            SET method = EXCLUDED.method,
                rounding = EXCLUDED.rounding,
                language = EXCLUDED.language,
                hints = EXCLUDED.hints
            """;

        int rounding = parseRounding(settings.rounding());
        boolean hints = Boolean.parseBoolean(settings.hints());

        try {
            int rowsAffected = jdbcTemplate.update(
                    query,
                    userId,
                    settings.method(),
                    rounding,
                    settings.language(),
                    hints);
            return CompletableFuture.completedFuture(rowsAffected > 0);
        } catch (DataAccessException e) {
            logger.error("Database error while setting user settings for userId: {}", userId, e);
            throw new SolverException("Failed to save user settings", e);
        }
    }

    private static int parseRounding(String rawValue) {
        try {
            return Integer.parseInt(rawValue);
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("rounding must be an integer, got: " + rawValue, e);
        }
    }
}
