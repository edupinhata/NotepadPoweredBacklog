package io.github.edupinhata.notepadpoweredbacklog.application;

import static org.junit.jupiter.api.Assertions.assertEquals;

import io.github.edupinhata.notepadpoweredbacklog.domain.DailySummary;
import java.time.Duration;
import org.junit.jupiter.api.Test;

class DailySummaryFormatterTest {

    @Test
    void formatsCountsAndWorkedDurationForTheInterface() {
        DailySummary summary = new DailySummary(2, 3, Duration.ofHours(9).plusMinutes(30));

        String formatted = new DailySummaryFormatter().format(summary);

        assertEquals("2 meetings | 3 tasks | 09:30 worked", formatted);
    }
}
