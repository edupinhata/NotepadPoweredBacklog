package io.github.edupinhata.notepadpoweredbacklog.application;

import static org.junit.jupiter.api.Assertions.*;

import java.time.LocalDate;
import java.time.temporal.WeekFields;
import org.junit.jupiter.api.Test;

class AnnualCalendarTest {
    @Test
    void includesEveryDayExactlyOnceInChronologicalOrder() {
        for (int year : new int[] {2024, 2026, 2028}) {
            var weeks = AnnualCalendar.weeks(LocalDate.of(year, 6, 15));
            var dates = weeks.stream().flatMap(week -> week.days().stream()).toList();
            var first = LocalDate.of(year, 1, 1);
            assertEquals(first.datesUntil(first.plusYears(1)).toList(), dates);
            for (var week : weeks) {
                assertTrue(week.days().size() <= 7);
                for (var date : week.days()) {
                    assertEquals(date.get(WeekFields.ISO.weekBasedYear()), week.weekBasedYear());
                    assertEquals(date.get(WeekFields.ISO.weekOfWeekBasedYear()), week.weekNumber());
                }
            }
        }
    }

    @Test
    void distinguishesWeeksAtBothYearBoundaries() {
        var weeks = AnnualCalendar.weeks(LocalDate.of(2012, 1, 1));
        assertEquals(2011, weeks.getFirst().weekBasedYear());
        assertEquals(52, weeks.getFirst().weekNumber());
        assertEquals(2013, weeks.getLast().weekBasedYear());
        assertEquals(1, weeks.getLast().weekNumber());
        assertEquals(1, weeks.stream().filter(AnnualCalendar.Week::current).count());
        assertTrue(weeks.getFirst().current());
    }

    @Test
    void marksOnlyTheWeekContainingTodayAsCurrent() {
        var today = LocalDate.of(2026, 11, 16);
        var weeks = AnnualCalendar.weeks(today);
        assertEquals(1, weeks.stream().filter(AnnualCalendar.Week::current).count());
        assertTrue(weeks.stream().filter(AnnualCalendar.Week::current).findFirst().orElseThrow()
                .days().contains(today));
    }

    @Test
    void classifiesPastTodayAndFutureIndependentlyOfSelection() {
        var today = LocalDate.of(2026, 11, 16);
        assertEquals(AnnualCalendar.DayStyle.PAST, AnnualCalendar.style(today.minusDays(1), today));
        assertEquals(AnnualCalendar.DayStyle.TODAY, AnnualCalendar.style(today, today));
        assertEquals(AnnualCalendar.DayStyle.FUTURE, AnnualCalendar.style(today.plusDays(1), today));
    }
}
