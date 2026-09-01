package io.github.edupinhata.notepadpoweredbacklog.domain;

import java.time.Duration;
import java.time.LocalTime;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class DailyDocumentParser {

    private static final Pattern ITEM_PATTERN = Pattern.compile("^\\[(?: |x|d|/|m)]\\s+.+$");
    private static final Pattern WORK_PERIOD_PATTERN =
            Pattern.compile("^(\\d{2}:\\d{2})\\s+-\\s+(\\d{2}:\\d{2})$");

    public DailyDocumentParseResult parse(String sourceText) {
        Objects.requireNonNull(sourceText, "Source text cannot be null");

        int meetingCount = 0;
        int taskCount = 0;
        Duration workedDuration = Duration.ZERO;
        List<DocumentDiagnostic> diagnostics = new ArrayList<>();
        Section section = Section.NONE;
        String[] lines = sourceText.split("\\R", -1);

        for (int index = 0; index < lines.length; index++) {
            String line = lines[index];
            section = sectionForHeading(line, section);

            boolean recognizedItem = ITEM_PATTERN.matcher(line).matches();
            if (recognizedItem && section == Section.MEETINGS) {
                meetingCount++;
                continue;
            }

            if (recognizedItem && section == Section.TO_DO) {
                taskCount++;
                continue;
            }

            if (section == Section.WORKED && !line.isBlank() && !line.startsWith("#")) {
                workedDuration = workedDuration.plus(parseWorkPeriod(line, index + 1, diagnostics));
            }
        }

        DailySummary summary = new DailySummary(meetingCount, taskCount, workedDuration);
        return new DailyDocumentParseResult(sourceText, summary, diagnostics);
    }

    private static Section sectionForHeading(String line, Section currentSection) {
        return switch (line) {
            case "# Meetings" -> Section.MEETINGS;
            case "# To Do" -> Section.TO_DO;
            case "# Worked" -> Section.WORKED;
            default -> line.startsWith("#") ? Section.NONE : currentSection;
        };
    }

    private static Duration parseWorkPeriod(
            String line, int lineNumber, List<DocumentDiagnostic> diagnostics) {
        Matcher matcher = WORK_PERIOD_PATTERN.matcher(line);
        if (!matcher.matches()) {
            diagnostics.add(new DocumentDiagnostic(lineNumber, "Invalid work period syntax"));
            return Duration.ZERO;
        }

        try {
            LocalTime start = LocalTime.parse(matcher.group(1));
            LocalTime end = LocalTime.parse(matcher.group(2));
            if (!end.isAfter(start)) {
                diagnostics.add(
                        new DocumentDiagnostic(lineNumber, "Work period end must be after start"));
                return Duration.ZERO;
            }
            return Duration.between(start, end);
        } catch (DateTimeParseException exception) {
            diagnostics.add(new DocumentDiagnostic(lineNumber, "Invalid work period time"));
            return Duration.ZERO;
        }
    }

    private enum Section {
        NONE,
        MEETINGS,
        TO_DO,
        WORKED
    }
}
