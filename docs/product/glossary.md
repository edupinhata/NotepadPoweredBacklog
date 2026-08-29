# Glossário do domínio

Use os conceitos abaixo de maneira consistente nos requisitos. No código e nos testes, use exclusivamente o nome canônico em inglês indicado na tabela. Termos ainda não aprovados permanecem marcados como TODO.

| Termo em português | Nome canônico no código | Definição atual | Observações |
|---|---|---|---|
| Backlog | `Backlog` | Conjunto de itens que representam trabalho ou compromissos a acompanhar. | TODO: decidir se inclui reuniões formalmente. |
| Documento diário | `DailyDocument` | Documento de texto associado a um dia e dividido em reuniões, tarefas e períodos trabalhados. | Convenção de armazenamento ainda não definida. |
| Afazer | `Task` | Item de trabalho registrado na lista de tarefas do dia. | “Afazer” e “tarefa” não geram tipos diferentes no código. |
| Tarefa | `Task` | Trabalho que pode possuir um dos estados textuais definidos. | Nome preferido para o conceito de afazer. |
| Reunião | `Meeting` | Compromisso registrado na seção de reuniões e sujeito aos estados textuais. | TODO: definir atributos de horário e duração. |
| Período trabalhado | `WorkPeriod` | Intervalo entre um horário inicial e final considerado no total de trabalho. | Regras para sobreposição e virada de dia estão pendentes. |
| Estado do item | `ItemStatus` | Situação interpretada a partir da marcação textual de uma tarefa ou reunião. | Não confundir estado com ação de movimentação. |
| Não iniciada | `NOT_STARTED` | Situação indicada preliminarmente por `[ ]`. | Valor candidato de `ItemStatus`. |
| Concluída | `COMPLETED` | Situação indicada preliminarmente por `[x]`. | Valor candidato de `ItemStatus`. |
| Deprecada | `DEPRECATED` | Item que deixou de ser relevante ou foi considerado obsoleto, indicado por `[d]`. | TODO: decidir o termo de interface: deprecada, descartada, cancelada ou obsoleta. |
| Parcialmente concluída | `PARTIALLY_COMPLETED` | Item iniciado, mas não concluído integralmente, indicado por `[/]`. | A definição original também associa realocação. |
| Movida | `MOVED` | Item transferido para outro documento diário, indicado por `[m]`. | TODO: definir rastreabilidade e destino. |
| Realocação | `Rescheduling` | Processo de levar um item de um dia para outro. | TODO: distinguir mover, copiar e manter referência. |
| Automação | `Automation` | Regra executada pelo aplicativo para interpretar ou reorganizar conteúdo. | Deve ser previsível, idempotente e preservar dados. |
| Resumo diário | `DailySummary` | Número de reuniões, número de tarefas e total de horas derivado de um documento diário. | Não é uma segunda fonte de verdade. |
| Estatística diária | `DailyStatistics` | Informação calculada a partir de um ou mais documentos e períodos válidos. | Fórmulas além do resumo diário ainda não foram definidas. |
| Fonte de verdade | `SourceOfTruth` | Representação considerada autoritativa quando texto e dados internos divergem. | Decisão arquitetural pendente. |

## Títulos canônicos do documento

| Conceito | Título textual |
|---|---|
| Reuniões | `# Meetings` |
| Tarefas | `# To Do` |
| Períodos trabalhados | `# Worked` |

Esses títulos pertencem ao formato inicial do documento e não devem ser traduzidos silenciosamente. Uma futura internacionalização deverá preservar compatibilidade com documentos existentes.

## Regras para evolução do glossário

- Adicione um termo quando ele possuir significado específico no domínio.
- Defina ou revise seu nome canônico em inglês antes de introduzi-lo no código.
- Não misture português e inglês em identificadores.
- Evite sinônimos no código sem uma decisão explícita.
- Atualize critérios de aceite e ADRs afetados quando uma definição mudar.
- Não transforme uma interpretação provisória em regra de negócio sem aprovação.
