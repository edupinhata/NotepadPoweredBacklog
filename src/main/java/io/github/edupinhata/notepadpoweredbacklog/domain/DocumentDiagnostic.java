package io.github.edupinhata.notepadpoweredbacklog.domain;

import java.util.Objects;

public record DocumentDiagnostic(int lineNumber, String message) {

    public DocumentDiagnostic {
        if (lineNumber < 1) {
            throw new IllegalArgumentException("Line number must be positive");
        }
        Objects.requireNonNull(message, "Diagnostic message cannot be null");
        if (message.isBlank()) {
            throw new IllegalArgumentException("Diagnostic message cannot be blank");
        }
    }
}
