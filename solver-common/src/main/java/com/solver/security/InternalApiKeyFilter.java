package com.solver.security;

import com.solver.config.SolverProperties;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpFilter;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

@Component
@Order(1)
public class InternalApiKeyFilter extends HttpFilter {

    private static final Logger logger = LoggerFactory.getLogger(InternalApiKeyFilter.class);
    private static final String API_KEY_HEADER = "X-Internal-Api-Key";
    private static final String PROTECTED_PREFIX = "/api/solver/";

    private final SolverProperties properties;

    public InternalApiKeyFilter(SolverProperties properties) {
        this.properties = properties;
    }

    @Override
    protected void doFilter(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        String path = request.getRequestURI();

        if (!path.startsWith(PROTECTED_PREFIX)) {
            chain.doFilter(request, response);
            return;
        }

        String expectedKey = properties.internalApiKey();
        if (expectedKey == null || expectedKey.isBlank()) {
            logger.error("SOLVER_INTERNAL_API_KEY is not configured; refusing request to {}", path);
            response.sendError(HttpServletResponse.SC_SERVICE_UNAVAILABLE, "Server misconfigured");
            return;
        }

        String providedKey = request.getHeader(API_KEY_HEADER);
        if (providedKey == null || !constantTimeEquals(providedKey, expectedKey)) {
            logger.warn("Rejected request to {} from {} due to missing/invalid API key",
                    path, request.getRemoteAddr());
            response.sendError(HttpServletResponse.SC_UNAUTHORIZED, "Missing or invalid API key");
            return;
        }

        chain.doFilter(request, response);
    }

    private static boolean constantTimeEquals(String a, String b) {
        return MessageDigest.isEqual(
                a.getBytes(StandardCharsets.UTF_8),
                b.getBytes(StandardCharsets.UTF_8)
        );
    }
}
