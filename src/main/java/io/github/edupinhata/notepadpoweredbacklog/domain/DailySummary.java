package io.github.edupinhata.notepadpoweredbacklog.domain;

import java.time.Duration;
import java.util.Objects;

public record DailySummary(int meetingCount, int taskCount, Duration workedDuration) {

    public DailySummary {
        if (meetingCount < 0) {
            throw new IllegalArgumentException("Meeting count cannot be negative");
        }
        if (taskCount < 0) {
            throw new IllegalArgumentException("Task count cannot be negative");
        }
        Objects.requireNonNull(workedDuration, "Worked duration cannot be null");
        if (workedDuration.isNegative()) {
            throw new IllegalArgumentException("Worked duration cannot be negative");
        }
    }
}
