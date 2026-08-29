package io.github.edupinhata.notepadpoweredbacklog.domain;

import java.util.List;
import java.util.Objects;

public record DailyDocumentParseResult(
        String sourceText, DailySummary summary, List<DocumentDiagnostic> diagnostics) {

    public DailyDocumentParseResult {
        Objects.requireNonNull(sourceText, "Source text cannot be null");
        Objects.requireNonNull(summary, "Summary cannot be null");
        diagnostics = List.copyOf(Objects.requireNonNull(diagnostics, "Diagnostics cannot be null"));
    }
}
