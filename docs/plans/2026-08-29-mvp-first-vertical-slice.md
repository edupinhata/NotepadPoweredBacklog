# Primeira fatia vertical do MVP — plano de implementação

**Objetivo:** iniciar o MVP com um projeto Java 21/JavaFX executável e uma fatia vertical que interprete o documento canônico e apresente o resumo diário derivado do texto.

**Arquitetura:** monólito modular conforme o ADR 0001. O parser e o cálculo permanecem em Java puro; a interface JavaFX apenas fornece o texto e apresenta o resultado. Persistência em arquivos, calendário anual e automação de movimentação permanecem fora desta primeira entrega porque suas decisões de armazenamento e salvamento ainda estão abertas.

**Tecnologias:** Java 21, JavaFX 21, Maven, JUnit Jupiter 5.

## Critérios de aceite da fatia

- [ ] `mvn test` compila o projeto e executa os testes.
- [ ] Um documento com as três seções canônicas produz contagens de reuniões e tarefas independentemente dos estados reconhecidos.
- [ ] Múltiplos períodos válidos são somados sem incluir os intervalos entre eles.
- [ ] O texto de origem permanece disponível sem transformação.
- [ ] A aplicação JavaFX inicia com `SplitPane`, editor, resumo e diagnóstico visível.
- [ ] Alterar o texto e solicitar a análise atualiza o resumo sem salvar ou reescrever o documento.
- [ ] `mvn verify` passa sem avisos de compilação introduzidos pela fatia.
- [ ] README e guia de contribuição contêm comandos realmente verificados.

## Fatias TDD

### 1. Fundação executável

- Criar `pom.xml` com versões fixadas, Java 21, JavaFX, JUnit e plugins de compilação/teste/execução.
- Criar `.gitignore` para artefatos Maven, IDE e snapshots locais de telemetria.
- Verificar a resolução de dependências com `mvn test`.

### 2. Resumo de documento válido

- Criar primeiro `src/test/java/io/github/edupinhata/notepadpoweredbacklog/domain/DailyDocumentParserTest.java`.
- Confirmar RED por ausência do parser.
- Implementar os tipos mínimos em `domain`: `DailyDocumentParser`, `DailyDocumentParseResult` e `DailySummary`.
- Reconhecer somente os títulos canônicos e itens com estados `[ ]`, `[x]`, `[d]`, `[/]` e `[m]`.
- Somar períodos `HH:mm - HH:mm` válidos no mesmo dia.
- Confirmar GREEN no teste focado e na suíte.

### 3. Preservação e diagnósticos básicos

- Adicionar teste de preservação exata do texto e de linha inválida na seção `# Worked`.
- Confirmar RED.
- Adicionar `DocumentDiagnostic` e manter entradas inválidas fora do total com diagnóstico explícito, sem transformar o texto.
- Confirmar GREEN.

### 4. Interface JavaFX

- Criar teste do formatador/apresentador em Java puro antes da implementação.
- Implementar `DailySummaryFormatter` e confirmar GREEN.
- Criar `NotepadPoweredBacklogApplication` com `SplitPane`, `TreeView`, `TextArea`, botão de análise, resumo e área de diagnósticos.
- Usar somente a data atual como nó inicial; calendário anual e I/O ficam explicitamente pendentes.
- Executar um smoke test real de inicialização.

### 5. Fechamento

- Atualizar `README.md`, `CONTRIBUTING.md` e estado do projeto sem declarar recursos futuros como prontos.
- Executar `mvn test`, `mvn verify`, `git diff --check` e inspeção de segurança do diff.
- Submeter o snapshot completo a revisão independente.
- Capturar o contador final da sessão e registrar a diferença no CSV de uso de IA; cache e reasoning permanecem categorias separadas.

## Riscos e limites

- JavaFX requer ambiente gráfico para o smoke visual; testes de domínio não dependem dele.
- A primeira fatia não decide localização, nome, observação nem política de salvamento dos arquivos.
- Sobreposição, horários invertidos, virada de dia e estatísticas por intervalo serão ciclos posteriores.
- O snapshot de tokens começou depois da inspeção inicial; essa parte será declarada como não medida, nunca estimada.
