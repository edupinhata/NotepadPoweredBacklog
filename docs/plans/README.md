# Planos de implementação

Planos transformam requisitos aprovados em tarefas pequenas, ordenadas e verificáveis. Eles não substituem visão, critérios de aceite ou ADRs.

## Quando criar um plano

Crie um plano antes de:

- implementar uma funcionalidade com múltiplas etapas;
- alterar formato de dados ou compatibilidade;
- coordenar mudanças em várias camadas;
- delegar trabalho para agentes de IA;
- executar migrações ou mudanças de segurança relevantes.

## Convenção

- Nome: `AAAA-MM-DD-titulo-curto.md`.
- Use [`plan-template.md`](plan-template.md).
- Referencie requisitos, critérios de aceite e ADRs aplicáveis.
- Divida o trabalho em fatias verticais pequenas.
- Inclua testes e comandos de verificação reais.
- Não invente comandos antes de a stack ser definida.

## Ciclo de execução

```text
critério de aceite
  → teste falhando pelo motivo esperado
  → implementação mínima
  → teste específico passando
  → suíte completa e verificações
  → revisão independente
```

## Índice

| Plano | Objetivo | Estado |
|---|---|---|
| — | Nenhum plano registrado ainda | — |
