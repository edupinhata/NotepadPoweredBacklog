# Como contribuir

O projeto está na fase de descoberta. Contribuições devem primeiro preservar a clareza do produto e evitar decisões técnicas prematuras.

## Antes de começar

1. Leia `ProductDefinition.md` e `docs/product/`.
2. Consulte as decisões em `docs/architecture/adr/`.
3. Confirme que a proposta pertence ao MVP ou registre por que o escopo deve mudar.
4. Para trabalho com IA, siga também `AGENTS.md`.

## Propondo uma mudança

Descreva:

- problema observado;
- usuário afetado;
- comportamento esperado;
- critérios de aceite verificáveis;
- itens explicitamente fora do escopo;
- riscos para dados e compatibilidade;
- alternativas consideradas.

Mudanças arquiteturais relevantes devem criar um ADR. Funcionalidades com múltiplas etapas devem possuir um plano em `docs/plans/`.

## Desenvolvimento orientado por testes

Para cada comportamento:

1. escreva um teste pequeno e focado;
2. execute-o e confirme uma falha pelo motivo esperado;
3. implemente somente o necessário;
4. execute o teste específico;
5. execute a suíte completa;
6. refatore apenas com os testes verdes.

## Qualidade e segurança

Antes de solicitar revisão, confirme:

- [ ] critérios de aceite atendidos;
- [ ] testes novos e existentes passando;
- [ ] lint, formatação e análise de tipos passando;
- [ ] nenhuma credencial ou dado pessoal incluído;
- [ ] entradas e caminhos não confiáveis validados;
- [ ] documentação afetada atualizada;
- [ ] nenhuma dependência desnecessária adicionada;
- [ ] diff revisado por um contexto independente quando aplicável.

## Idioma

Código e artefatos técnicos executáveis devem ser escritos em inglês, incluindo identificadores, testes, comentários, logs, exceções, configurações e textos mantidos diretamente na aplicação. A política completa e suas exceções estão em [`AGENTS.md`](AGENTS.md). A documentação do projeto pode permanecer em português.

## Pull requests

Prefira mudanças pequenas e uma finalidade por PR. A descrição deve incluir:

- o que mudou e por quê;
- como verificar;
- evidências dos testes executados;
- riscos, limitações e decisões associadas;
- capturas de tela somente quando ajudarem a avaliar comportamento visual.

## Comandos do projeto

Serão preenchidos quando a stack for aprovada:

```text
Instalação: TODO
Execução: TODO
Testes: TODO
Lint: TODO
Formatação: TODO
Build: TODO
```

## Commits

TODO: decidir a convenção de mensagens de commit antes do primeiro ciclo de implementação.
