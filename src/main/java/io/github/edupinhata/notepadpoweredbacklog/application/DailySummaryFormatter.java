package io.github.edupinhata.notepadpoweredbacklog.application;

import io.github.edupinhata.notepadpoweredbacklog.domain.DailySummary;
import java.util.Locale;
import java.util.Objects;

public final class DailySummaryFormatter {

    public String format(DailySummary summary) {
        Objects.requireNonNull(summary, "Summary cannot be null");
        long totalMinutes = summary.workedDuration().toMinutes();
        long hours = totalMinutes / 60;
        long minutes = totalMinutes % 60;
        return String.format(
                Locale.ROOT,
                "%d meetings | %d tasks | %02d:%02d worked",
                summary.meetingCount(),
                summary.taskCount(),
                hours,
                minutes);
    }
}
