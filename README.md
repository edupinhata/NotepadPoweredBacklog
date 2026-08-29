# Notepad Powered Backlog

Aplicação para organizar tarefas, reuniões e períodos trabalhados por meio de arquivos de texto simples, preservando uma experiência próxima à de um bloco de notas.

> **Estado:** descoberta e definição do MVP. Java 21, JavaFX e Maven foram escolhidos para a primeira aplicação desktop; ainda não há aplicação executável.

## Visão geral

O usuário trabalha em um documento diário dividido em três seções:

1. reuniões;
2. lista de afazeres;
3. períodos trabalhados.

O produto interpreta marcações textuais para acompanhar estados, mover itens entre dias e produzir estatísticas de trabalho.

## Documentação

- [Definição original do produto](ProductDefinition.md)
- [Visão do produto](docs/product/vision.md)
- [Escopo do MVP](docs/product/mvp.md)
- [Glossário do domínio](docs/product/glossary.md)
- [Arquitetura](docs/architecture/README.md)
- [Registros de decisão arquitetural](docs/architecture/adr/README.md)
- [Planos de implementação](docs/plans/README.md)
- [Como contribuir](CONTRIBUTING.md)
- [Instruções para agentes de IA](AGENTS.md)

## Situação atual

### Definido

- experiência baseada em texto simples;
- controle de tarefas, reuniões e períodos trabalhados;
- estados textuais iniciais dos itens;
- aplicação inicialmente local e individual;
- evolução futura para múltiplos dispositivos.
- Java 21 e JavaFX para o MVP desktop local;
- primeira janela com navegação por semanas/dias, resumo diário e editor de texto.

### Pendente de decisão

- formato canônico dos documentos diários;
- regras exatas de movimentação entre dias;
- critérios e fórmulas das estatísticas;
- persistência, sincronização e estratégia offline;
- localização dos documentos e política de salvamento;
- estratégia da futura interface Android;
- requisitos não funcionais e modelo de distribuição.

## Desenvolvimento

Os comandos de instalação, execução, testes, lint e build serão adicionados quando a stack for decidida e o esqueleto executável existir. Não presuma comandos ainda não documentados.

## Licença

TODO: escolher e adicionar a licença do projeto.
