package io.github.edupinhata.notepadpoweredbacklog.application;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.time.LocalDate;
import org.junit.jupiter.api.Test;

class DailyDocumentDraftsTest {
    @Test
    void keepsExactIndependentDraftsWhenSwitchingDays() {
        var today = LocalDate.of(2026, 11, 16);
        var drafts = new DailyDocumentDrafts(today, "Initial text");
        assertEquals("Initial text", drafts.text());
        drafts.update("# Notes\r\nKeep my text\r\n");
        drafts.select(today.plusDays(1));
        assertEquals("# Meetings\n\n# To Do\n\n# Worked\n", drafts.text());
        drafts.update("");
        drafts.select(today);
        assertEquals("# Notes\r\nKeep my text\r\n", drafts.text());
        drafts.select(today.plusDays(1));
        assertEquals("", drafts.text());
    }
}
