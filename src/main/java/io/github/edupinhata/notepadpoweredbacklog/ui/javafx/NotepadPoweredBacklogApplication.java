package io.github.edupinhata.notepadpoweredbacklog.ui.javafx;

import io.github.edupinhata.notepadpoweredbacklog.application.AnnualCalendar;
import io.github.edupinhata.notepadpoweredbacklog.application.DailyDocumentDrafts;
import io.github.edupinhata.notepadpoweredbacklog.application.DailySummaryFormatter;
import io.github.edupinhata.notepadpoweredbacklog.domain.DailyDocumentParseResult;
import io.github.edupinhata.notepadpoweredbacklog.domain.DailyDocumentParser;
import io.github.edupinhata.notepadpoweredbacklog.domain.DocumentDiagnostic;
import java.time.LocalDate;
import java.util.Locale;
import java.util.stream.Collectors;
import javafx.application.Application;
import javafx.application.Platform;
import javafx.css.PseudoClass;
import javafx.geometry.Insets;
import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.SplitPane;
import javafx.scene.control.TextArea;
import javafx.scene.control.TreeItem;
import javafx.scene.control.TreeCell;
import javafx.scene.control.TreeView;
import javafx.scene.layout.Priority;
import javafx.scene.layout.VBox;
import javafx.stage.Stage;

public final class NotepadPoweredBacklogApplication extends Application {

    private static final String INITIAL_DOCUMENT = """
            # Meetings
            [ ] Daily planning

            # To Do
            [ ] Start the MVP

            # Worked
            09:00 - 12:00
            13:30 - 18:00
            """;

    private final DailyDocumentParser parser = new DailyDocumentParser();
    private final DailySummaryFormatter summaryFormatter = new DailySummaryFormatter();

    @Override
    public void start(Stage stage) {
        LocalDate selectedDate = LocalDate.now();
        TreeView<CalendarEntry> calendarTree = createCalendarTree(selectedDate);
        DailyDocumentDrafts drafts = new DailyDocumentDrafts(selectedDate, INITIAL_DOCUMENT);
        TextArea editor = new TextArea(INITIAL_DOCUMENT);
        Label summaryLabel = new Label();
        Label diagnosticLabel = new Label();
        Button analyzeButton = new Button("Analyze document");

        calendarTree.setAccessibleText("Daily document navigation");
        editor.setAccessibleText("Daily document editor");
        editor.setWrapText(false);
        summaryLabel.setAccessibleRoleDescription("Daily summary");
        diagnosticLabel.setAccessibleRoleDescription("Document diagnostics");
        diagnosticLabel.setWrapText(true);
        analyzeButton.setAccessibleText("Analyze daily document");
        analyzeButton.setDefaultButton(true);

        Runnable analyzeDocument =
                () -> updateAnalysis(editor.getText(), summaryLabel, diagnosticLabel);
        analyzeButton.setOnAction(event -> analyzeDocument.run());
        analyzeDocument.run();

        Label dateLabel = new Label("Selected day: " + selectedDate);
        editor.textProperty().addListener((observable, oldText, newText) -> drafts.update(newText));
        calendarTree.getSelectionModel().selectedItemProperty().addListener(
                (observable, previous, selected) -> {
                    if (selected == null || selected.getValue().date() == null) {
                        return;
                    }
                    LocalDate date = selected.getValue().date();
                    drafts.select(date);
                    editor.setText(drafts.text());
                    dateLabel.setText("Selected day: " + date);
                    analyzeDocument.run();
                });
        VBox editorPane =
                new VBox(10, dateLabel, editor, analyzeButton, summaryLabel, diagnosticLabel);
        editorPane.setPadding(new Insets(12));
        VBox.setVgrow(editor, Priority.ALWAYS);

        SplitPane splitPane = new SplitPane(calendarTree, editorPane);
        splitPane.setDividerPositions(0.30);

        Scene scene = new Scene(splitPane, 960, 640);
        scene.getStylesheets().add(NotepadPoweredBacklogApplication.class
                .getResource("calendar.css").toExternalForm());
        stage.setTitle("Notepad Powered Backlog - MVP Preview");
        stage.setMinWidth(720);
        stage.setMinHeight(480);
        stage.setScene(scene);
        stage.show();
    }

    private record CalendarEntry(String label, LocalDate date) {}

    private static TreeView<CalendarEntry> createCalendarTree(LocalDate today) {
        TreeItem<CalendarEntry> yearItem = new TreeItem<>(
                new CalendarEntry(Integer.toString(today.getYear()), null));
        TreeItem<CalendarEntry> todayItem = null;
        for (AnnualCalendar.Week week : AnnualCalendar.weeks(today)) {
            String label = String.format(Locale.ROOT, "Week %02d (%d)",
                    week.weekNumber(), week.weekBasedYear());
            TreeItem<CalendarEntry> weekItem = new TreeItem<>(new CalendarEntry(label, null));
            for (LocalDate date : week.days()) {
                TreeItem<CalendarEntry> dayItem = new TreeItem<>(
                        new CalendarEntry(date.toString(), date));
                weekItem.getChildren().add(dayItem);
                if (date.equals(today)) {
                    todayItem = dayItem;
                }
            }
            weekItem.setExpanded(week.current());
            yearItem.getChildren().add(weekItem);
        }
        yearItem.setExpanded(true);
        TreeView<CalendarEntry> tree = new TreeView<>(yearItem);
        tree.getStyleClass().add("annual-calendar");
        tree.setCellFactory(view -> new TreeCell<>() {
            private final PseudoClass todayClass = PseudoClass.getPseudoClass("today");
            private final PseudoClass futureClass = PseudoClass.getPseudoClass("future");

            @Override
            protected void updateItem(CalendarEntry entry, boolean empty) {
                super.updateItem(entry, empty);
                setText(empty || entry == null ? null : entry.label());
                setGraphic(null);
                AnnualCalendar.DayStyle style = empty || entry == null || entry.date() == null
                        ? null : AnnualCalendar.style(entry.date(), today);
                pseudoClassStateChanged(todayClass, style == AnnualCalendar.DayStyle.TODAY);
                pseudoClassStateChanged(futureClass, style == AnnualCalendar.DayStyle.FUTURE);
            }
        });
        tree.getSelectionModel().select(todayItem);
        TreeItem<CalendarEntry> selectedItem = todayItem;
        Platform.runLater(() -> tree.scrollTo(tree.getRow(selectedItem)));
        return tree;
    }

    private void updateAnalysis(String sourceText, Label summaryLabel, Label diagnosticLabel) {
        DailyDocumentParseResult result = parser.parse(sourceText);
        summaryLabel.setText(summaryFormatter.format(result.summary()));
        if (result.diagnostics().isEmpty()) {
            diagnosticLabel.setText("No syntax diagnostics");
            return;
        }

        String diagnostics =
                result.diagnostics().stream()
                        .map(NotepadPoweredBacklogApplication::formatDiagnostic)
                        .collect(Collectors.joining(System.lineSeparator()));
        diagnosticLabel.setText(diagnostics);
    }

    private static String formatDiagnostic(DocumentDiagnostic diagnostic) {
        return "Line " + diagnostic.lineNumber() + ": " + diagnostic.message();
    }

    public static void main(String[] args) {
        launch(args);
    }
}
