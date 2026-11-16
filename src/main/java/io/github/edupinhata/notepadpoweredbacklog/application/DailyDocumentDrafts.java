package io.github.edupinhata.notepadpoweredbacklog.application;

import java.time.LocalDate;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

public final class DailyDocumentDrafts {
    private static final String EMPTY_DOCUMENT = "# Meetings\n\n# To Do\n\n# Worked\n";
    private final Map<LocalDate, String> documents = new HashMap<>();
    private LocalDate selectedDate;

    public DailyDocumentDrafts(LocalDate initialDate, String initialText) {
        select(initialDate);
        update(initialText);
    }

    public void select(LocalDate date) {
        selectedDate = Objects.requireNonNull(date, "Selected date cannot be null");
    }

    public String text() {
        return documents.getOrDefault(selectedDate, EMPTY_DOCUMENT);
    }

    public void update(String text) {
        documents.put(selectedDate, Objects.requireNonNull(text, "Document text cannot be null"));
    }
}
