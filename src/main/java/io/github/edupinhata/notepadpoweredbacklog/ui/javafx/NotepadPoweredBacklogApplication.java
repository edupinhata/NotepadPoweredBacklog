package io.github.edupinhata.notepadpoweredbacklog.ui.javafx;

import io.github.edupinhata.notepadpoweredbacklog.application.DailySummaryFormatter;
import io.github.edupinhata.notepadpoweredbacklog.domain.DailyDocumentParseResult;
import io.github.edupinhata.notepadpoweredbacklog.domain.DailyDocumentParser;
import io.github.edupinhata.notepadpoweredbacklog.domain.DocumentDiagnostic;
import java.time.LocalDate;
import java.time.temporal.WeekFields;
import java.util.Locale;
import java.util.stream.Collectors;
import javafx.application.Application;
import javafx.geometry.Insets;
import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.SplitPane;
import javafx.scene.control.TextArea;
import javafx.scene.control.TreeItem;
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
        TreeView<String> calendarTree = createCalendarTree(selectedDate);
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
        VBox editorPane =
                new VBox(10, dateLabel, editor, analyzeButton, summaryLabel, diagnosticLabel);
        editorPane.setPadding(new Insets(12));
        VBox.setVgrow(editor, Priority.ALWAYS);

        SplitPane splitPane = new SplitPane(calendarTree, editorPane);
        splitPane.setDividerPositions(0.30);

        Scene scene = new Scene(splitPane, 960, 640);
        stage.setTitle("Notepad Powered Backlog - MVP Preview");
        stage.setMinWidth(720);
        stage.setMinHeight(480);
        stage.setScene(scene);
        stage.show();
    }

    private static TreeView<String> createCalendarTree(LocalDate selectedDate) {
        WeekFields weekFields = WeekFields.ISO;
        int weekBasedYear = selectedDate.get(weekFields.weekBasedYear());
        int weekNumber = selectedDate.get(weekFields.weekOfWeekBasedYear());

        TreeItem<String> yearItem = new TreeItem<>(Integer.toString(weekBasedYear));
        TreeItem<String> weekItem = new TreeItem<>(String.format(Locale.ROOT, "Week %02d", weekNumber));
        TreeItem<String> dayItem = new TreeItem<>(selectedDate.toString());
        weekItem.getChildren().add(dayItem);
        weekItem.setExpanded(true);
        yearItem.getChildren().add(weekItem);
        yearItem.setExpanded(true);

        TreeView<String> tree = new TreeView<>(yearItem);
        tree.getSelectionModel().select(dayItem);
        tree.setShowRoot(true);
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
