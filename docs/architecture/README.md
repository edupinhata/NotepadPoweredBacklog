# Arquitetura

O MVP será uma aplicação desktop local em Java 21 com JavaFX. A decisão e seus trade-offs estão registrados no [ADR 0001](adr/0001-java-javafx-mvp.md). Esta área descreve as fronteiras aprovadas sem apresentar funcionalidades planejadas como implementadas.

## Direcionadores conhecidos

- aplicação inicialmente local e individual;
- edição e interpretação de texto simples;
- preservação integral dos dados do usuário;
- evolução futura possível para múltiplos dispositivos;
- ausência de colaboração entre usuários no escopo atual;
- necessidade de estatísticas e automações determinísticas.
- desenvolvimento inicial em Java, com interface desktop JavaFX;
- reutilização futura do núcleo em outras interfaces, inclusive Android.
- código, testes e artefatos técnicos executáveis escritos em inglês.

## Decisões necessárias

1. sistemas operacionais desktop atendidos na primeira distribuição;
2. texto como fonte de verdade ou como importação/exportação;
3. localização e convenção de nomes dos documentos diários;
4. salvamento explícito, automático ou ambos;
5. persistência de metadados e índices;
6. estratégia offline;
7. backup, recuperação e compatibilidade;
8. estratégia futura de sincronização e conflitos;
9. abordagem da futura interface Android após experimento técnico;
10. observabilidade e telemetria, se houver.

## Princípios provisórios

- separar regras de domínio da interface e da persistência;
- manter parsing e serialização determinísticos;
- testar ida e volta do texto sem perda de informação;
- evitar dependência da futura sincronização no desenho do primeiro MVP;
- registrar decisões significativas como ADRs antes da implementação.

## Modelo inicial

Um monólito modular com dependências apontando para o domínio separará:

```text
Interface JavaFX
      ↓
Casos de uso
      ↓
Domínio puro
  ↙         ↘
Parser      Repositório de documentos
```

### Responsabilidades

- **Interface JavaFX:** janela, navegação por semanas e dias, editor e apresentação de diagnósticos.
- **Casos de uso:** abrir, editar, salvar e resumir um documento diário.
- **Domínio:** tarefas, reuniões, períodos trabalhados, estados e cálculos.
- **Parser/serializador:** transformação determinística entre texto e domínio, preservando conteúdo desconhecido.
- **Repositório de documentos:** acesso seguro e substituível aos arquivos, sem vazar detalhes de I/O para o domínio.

### Organização inicial do código

O primeiro esqueleto usará um único módulo Maven, organizado por responsabilidade:

```text
src/main/java/<pacote-base>/
├── domain/          # modelos, estados, períodos e cálculos puros
├── application/     # casos de uso e portas
├── infrastructure/
│   └── file/        # leitura e gravação segura dos documentos
└── ui/
    └── javafx/      # janela, árvore, editor e células visuais

src/test/java/<pacote-base>/
├── domain/
├── application/
├── infrastructure/
└── ui/
```

O pacote-base inicial é `io.github.edupinhata.notepadpoweredbacklog`. Módulos Maven separados somente serão introduzidos se testes de fronteira, distribuição ou crescimento real justificarem o custo.

Todos os nomes representados em português neste documento são descrições arquiteturais. Os pacotes, tipos, métodos, testes, comentários, mensagens técnicas e recursos implementados usarão inglês, conforme a política canônica do `AGENTS.md`.

### Primeira fatia vertical

```text
selecionar dia
  → carregar documento diário
  → editar texto
  → interpretar reuniões, tarefas e períodos
  → salvar sem perda
  → atualizar resumo do dia
```

A janela terá um `SplitPane`: à esquerda, um `TreeView` com semanas e dias; à direita, um `TextArea` para o documento diário. O resumo junto ao dia exibirá `reuniões | tarefas | horas trabalhadas` e será sempre derivado do conteúdo interpretado, nunca mantido como uma segunda fonte de verdade.

A primeira entrega implementa o parser, o resumo e uma prévia em memória com a semana e o dia atuais. O carregamento e salvamento sem perda, a árvore anual completa e a atualização do resumo junto a cada nó permanecem nas próximas fatias, após as decisões de persistência e política de salvamento.

## Registros de decisão

Consulte [`adr/README.md`](adr/README.md) para o processo e o modelo de ADR.
