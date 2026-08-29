# Glossário do domínio

Use estes termos de maneira consistente em requisitos, código, testes e interface. Termos ainda não aprovados permanecem marcados como TODO.

| Termo | Definição atual | Observações |
|---|---|---|
| Backlog | Conjunto de itens que representam trabalho ou compromissos a acompanhar. | TODO: decidir se inclui reuniões formalmente. |
| Documento diário | Documento de texto associado a um dia e dividido em reuniões, afazeres e períodos trabalhados. | Formato canônico ainda não definido. |
| Afazer | Item de trabalho registrado na lista de tarefas do dia. | Avaliar se o termo de domínio final será “tarefa”. |
| Tarefa | Trabalho que pode possuir um dos estados textuais definidos. | Usado como sinônimo preliminar de afazer. |
| Reunião | Compromisso registrado na seção de reuniões e sujeito aos estados textuais. | TODO: definir atributos de horário e duração. |
| Período trabalhado | Intervalo entre um horário inicial e final considerado no total de trabalho. | Regras para sobreposição e virada de dia estão pendentes. |
| Estado | Situação interpretada a partir da marcação textual de uma tarefa ou reunião. | Não confundir estado com ação de movimentação. |
| Não iniciada | Situação indicada preliminarmente por `[ ]`. |  |
| Concluída | Situação indicada preliminarmente por `[x]`. |  |
| Deprecada | Item que deixou de ser relevante ou foi considerado obsoleto, indicado por `[d]`. | TODO: decidir o termo de interface: deprecada, descartada, cancelada ou obsoleta. |
| Parcialmente concluída | Item iniciado, mas não concluído integralmente, indicado por `[/]`. | A definição original também associa realocação. |
| Movida | Item transferido para outro documento diário, indicado por `[m]`. | TODO: definir rastreabilidade e destino. |
| Realocação | Processo de levar um item de um dia para outro. | TODO: distinguir mover, copiar e manter referência. |
| Automação | Regra executada pelo aplicativo para interpretar ou reorganizar conteúdo. | Deve ser previsível, idempotente e preservar dados. |
| Estatística diária | Informação calculada a partir de um ou mais documentos e períodos válidos. | Fórmulas ainda não definidas. |
| Fonte de verdade | Representação considerada autoritativa quando texto e dados internos divergem. | Decisão arquitetural pendente. |

## Regras para evolução do glossário

- Adicione um termo quando ele possuir significado específico no domínio.
- Evite sinônimos no código sem uma decisão explícita.
- Atualize critérios de aceite e ADRs afetados quando uma definição mudar.
- Não transforme uma interpretação provisória em regra de negócio sem aprovação.
