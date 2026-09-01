# Plano — coletor confiável de custo de desenvolvimento

> **Estado:** concluído.

## Objetivo

Tornar obrigatória e auditável a medição de uso de IA por unidade de trabalho, sem depender de cálculos manuais e sem persistir conteúdo de conversas.

## Critérios de aceite

- [x] capturar snapshot inicial exclusivo com campos permitidos;
- [x] calcular deltas do agente principal e descendentes vinculados;
- [x] rejeitar dados ausentes, regressivos, adulterados ou contraditórios;
- [x] impedir consumo duplicado sob finalização concorrente real;
- [x] persistir histórico canônico JSONL e gerar a tabela CSV;
- [x] preservar semântica de custos reais, estimados, incluídos e indisponíveis;
- [x] documentar invocação obrigatória em `AGENTS.md` e `CONTRIBUTING.md`;
- [x] executar gates finais e revisão independente do snapshot staged;
- [x] medir esta própria unidade de trabalho e atualizar o PR.

## Não objetivos

- capturar prompts, respostas ou raciocínio;
- estimar medições históricas sem snapshot inicial;
- adivinhar automaticamente qual sessão Hermes pertence ao trabalho;
- incluir espera de CI, commit, push ou mensagens finais na fronteira padrão.

## Verificação

```bash
python -m unittest discover -s scripts/tests -v
python scripts/ai_usage.py report
mvn verify
git diff --check
```

## Riscos e controles

- **Concorrência:** locks persistentes por snapshot e histórico, gravação atômica e teste multiprocesso.
- **Privacidade:** consultas SQLite selecionam somente colunas técnicas permitidas.
- **Atribuição incorreta:** o ID da sessão é obrigatório; nenhuma heurística de “sessão mais recente” é usada.
- **Histórico corrompido:** todo o JSONL é validado antes de append ou regeneração do CSV.
