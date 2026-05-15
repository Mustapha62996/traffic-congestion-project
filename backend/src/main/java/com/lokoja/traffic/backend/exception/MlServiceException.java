package com.lokoja.traffic.backend.exception;

import org.springframework.http.HttpStatus;

public class MlServiceException extends RuntimeException {

    private final HttpStatus status;

    public MlServiceException(HttpStatus status, String message) {
        super(message);
        this.status = status;
    }

    public HttpStatus getStatus() {
        return status;
    }
}
