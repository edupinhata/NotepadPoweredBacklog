# Calendário anual em memória

## Escopo e aceite

- Exibir todos os dias do ano civil atual, em ordem, agrupados pela semana ISO e seu ano ISO; incluir 29 de fevereiro em anos bissextos.
- Expandir inicialmente apenas a semana de hoje e selecionar hoje.
- Mostrar hoje em negrito, datas futuras em cinza claro e datas passadas no estilo normal.
- Selecionar dias mantém documentos independentes em memória, sem I/O ou persistência.
- Ano e semana são agrupadores, não documentos. Trocar de agrupador não altera o editor.
- A data de referência é capturada ao abrir a janela; atualização à meia-noite e seleção de outro ano ficam fora desta fatia.

## Etapas

1. Testes primeiro para cobertura anual, ano bissexto, limites ISO e classificação temporal.
2. Modelo Java puro e integração à árvore JavaFX com células reutilizáveis.
3. Verificar build, testes, inicialização e revisão independente; atualizar documentação.

## Medição de IA

**Indisponível.** O usuário autorizou explicitamente esta implementação sem medição Hermes em 2026-11-16. Não há ID de sessão Hermes verificado nem snapshot inicial. Nenhum contador ou custo será estimado. O histórico JSONL/CSV existente permanece intacto, sem criar uma medição fictícia.

## Verificação realizada

- RED: testes focados falharam por ausência de `AnnualCalendar` e `DailyDocumentDrafts` antes das implementações.
- GREEN: `mvn -q -Dtest=AnnualCalendarTest,DailyDocumentDraftsTest test` com Java 21 passou.
- `mvn verify` com Java 21: 10 testes, nenhuma falha; compilação com `-Xlint:all -Werror` e empacotamento concluídos.
- Smoke gráfico temporário `CalendarSmoke` compilado com `javac` e executado com `java --add-modules javafx.controls`: confirmou quantidade de datas, expansão inicial, fonte de hoje em negrito, cor futura `#888888`, rascunhos independentes e agrupadores sem mudança do editor. Não substitui aceite visual pelo usuário.
- Revisão independente concluída sem achados bloqueantes; posição da documentação no README corrigida.
- `git diff --check` passou.

A persistência continua pendente: fechar a aplicação descarta todos os rascunhos.
