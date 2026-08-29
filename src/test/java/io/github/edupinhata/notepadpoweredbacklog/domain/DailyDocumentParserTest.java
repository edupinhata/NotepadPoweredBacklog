package io.github.edupinhata.notepadpoweredbacklog.domain;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.Duration;
import org.junit.jupiter.api.Test;

class DailyDocumentParserTest {

    private final DailyDocumentParser parser = new DailyDocumentParser();

    @Test
    void summarizesRecognizedItemsAndValidWorkPeriods() {
        String source = """
                # Meetings
                [ ] Planning
                [x] Review

                # To Do
                [d] Remove obsolete task
                [/] Continue implementation

                # Worked
                09:00 - 12:30
                14:00 - 20:00
                """;

        DailyDocumentParseResult result = parser.parse(source);

        assertEquals(2, result.summary().meetingCount());
        assertEquals(2, result.summary().taskCount());
        assertEquals(Duration.ofHours(9).plusMinutes(30), result.summary().workedDuration());
        assertEquals(source, result.sourceText());
        assertTrue(result.diagnostics().isEmpty());
    }

    @Test
    void reportsInvalidWorkPeriodsWithoutIncludingThemInTheTotal() {
        String source = """
                # Meetings

                # To Do

                # Worked
                09:00 - 10:00
                not a period
                12:00 - 11:00
                25:00 - 26:00
                """;

        DailyDocumentParseResult result = parser.parse(source);

        assertEquals(Duration.ofHours(1), result.summary().workedDuration());
        assertEquals(3, result.diagnostics().size());
        assertEquals(7, result.diagnostics().get(0).lineNumber());
        assertEquals("Invalid work period syntax", result.diagnostics().get(0).message());
        assertEquals(8, result.diagnostics().get(1).lineNumber());
        assertEquals("Work period end must be after start", result.diagnostics().get(1).message());
        assertEquals(9, result.diagnostics().get(2).lineNumber());
        assertEquals("Invalid work period time", result.diagnostics().get(2).message());
        assertEquals(source, result.sourceText());
    }

    @Test
    void preservesUnknownSectionsWithoutTreatingTheirTextAsWorkPeriods() {
        String source = """
                # Meetings

                # To Do

                # Worked
                09:00 - 10:00

                # Notes
                Keep this unrecognized text exactly as written.
                """;

        DailyDocumentParseResult result = parser.parse(source);

        assertEquals(Duration.ofHours(1), result.summary().workedDuration());
        assertTrue(result.diagnostics().isEmpty());
        assertEquals(source, result.sourceText());
    }

    @Test
    void reportsItemShapedContentAsInvalidInsideWorkedSection() {
        String source = """
                # Meetings

                # To Do

                # Worked
                [ ] Misplaced task
                """;

        DailyDocumentParseResult result = parser.parse(source);

        assertEquals(Duration.ZERO, result.summary().workedDuration());
        assertEquals(1, result.diagnostics().size());
        assertEquals(6, result.diagnostics().getFirst().lineNumber());
        assertEquals("Invalid work period syntax", result.diagnostics().getFirst().message());
        assertEquals(source, result.sourceText());
    }
}
