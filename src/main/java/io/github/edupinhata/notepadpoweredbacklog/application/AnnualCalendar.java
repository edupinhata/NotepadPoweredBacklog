package io.github.edupinhata.notepadpoweredbacklog.application;

import java.time.LocalDate;
import java.time.temporal.WeekFields;
import java.util.ArrayList;
import java.util.List;

public final class AnnualCalendar {
    private AnnualCalendar() {}

    public record Week(int weekBasedYear, int weekNumber, List<LocalDate> days, boolean current) {
        public Week {
            days = List.copyOf(days);
        }
    }

    public enum DayStyle { PAST, TODAY, FUTURE }

    public static List<Week> weeks(LocalDate today) {
        List<Week> weeks = new ArrayList<>();
        LocalDate date = LocalDate.of(today.getYear(), 1, 1);
        while (date.getYear() == today.getYear()) {
            int weekYear = date.get(WeekFields.ISO.weekBasedYear());
            int weekNumber = date.get(WeekFields.ISO.weekOfWeekBasedYear());
            List<LocalDate> days = new ArrayList<>();
            do {
                days.add(date);
                date = date.plusDays(1);
            } while (date.getYear() == today.getYear()
                    && date.get(WeekFields.ISO.weekBasedYear()) == weekYear
                    && date.get(WeekFields.ISO.weekOfWeekBasedYear()) == weekNumber);
            weeks.add(new Week(weekYear, weekNumber, days, days.contains(today)));
        }
        return List.copyOf(weeks);
    }

    public static DayStyle style(LocalDate date, LocalDate today) {
        if (date.equals(today)) {
            return DayStyle.TODAY;
        }
        return date.isAfter(today) ? DayStyle.FUTURE : DayStyle.PAST;
    }
}
