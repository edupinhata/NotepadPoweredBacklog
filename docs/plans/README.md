# Planos de implementação

Planos são artefatos sob demanda para trabalhos em que uma sequência explícita reduz risco ou incerteza. A issue é a unidade principal de planejamento; o PR registra a entrega.

## Quando criar

Crie um plano separado quando o trabalho:

- provavelmente ultrapassar um dia;
- envolver várias camadas, componentes ou agentes;
- alterar formato de dados, compatibilidade ou migrações;
- possuir riscos relevantes de segurança ou integridade;
- depender de uma ordem de execução que não seja óbvia.

Para correções pequenas e funcionalidades comuns, mantenha objetivo, escopo e critérios de aceite na issue. Não crie um plano apenas para cumprir processo.

## Convenção

- Nome: `AAAA-MM-DD-titulo-curto.md`.
- Use [`plan-template.md`](plan-template.md) como ponto de partida, removendo seções sem utilidade.
- Referencie a issue e ADRs aplicáveis em vez de duplicar seu conteúdo.
- Prefira checklists curtos e fatias verticais.
- Inclua somente comandos existentes e verificáveis.

## Fluxo padrão

```text
issue → teste → implementação → verificação → PR
```

## Índice

| Plano | Objetivo | Estado |
|---|---|---|
| [Primeira fatia vertical do MVP](2026-08-29-mvp-first-vertical-slice.md) | Criar fundação executável, parser, resumo e prévia JavaFX em memória | Em execução |
