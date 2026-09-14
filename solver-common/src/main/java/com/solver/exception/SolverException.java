package com.solver.exception;

public class SolverException extends RuntimeException {
    public SolverException(String message) {
        super(message);
    }

    public SolverException(String message, Throwable cause) {
        super(message, cause);
    }
} 