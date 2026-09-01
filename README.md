# Notepad Powered Backlog

Aplicação para organizar tarefas, reuniões e períodos trabalhados por meio de arquivos de texto simples, preservando uma experiência próxima à de um bloco de notas.

> **Estado:** primeira fatia vertical do MVP em desenvolvimento. Já existe uma prévia JavaFX executável que interpreta o documento canônico em memória e calcula o resumo diário; persistência e navegação anual ainda não foram implementadas.

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
- [Contabilidade de uso de IA](docs/engineering/ai-usage/README.md)

## Situação atual

### Definido

- experiência baseada em texto simples;
- controle de tarefas, reuniões e períodos trabalhados;
- estados textuais iniciais dos itens;
- aplicação inicialmente local e individual;
- evolução futura para múltiplos dispositivos.
- Java 21 e JavaFX para o MVP desktop local;
- primeira janela com navegação por semanas/dias, resumo diário e editor de texto.

### Implementado na primeira fatia

- projeto Maven compilável com Java 21 e JavaFX 21;
- parser em Java puro para as três seções canônicas;
- contagem de reuniões e tarefas com estados reconhecidos;
- soma de períodos válidos e diagnóstico de horários inválidos ou invertidos;
- preservação integral do texto analisado em memória;
- prévia JavaFX com semana e dia atuais, editor, resumo e diagnósticos.

### Pendente de decisão

- formato canônico dos documentos diários;
- regras exatas de movimentação entre dias;
- critérios e fórmulas das estatísticas;
- persistência, sincronização e estratégia offline;
- localização dos documentos e política de salvamento;
- estratégia da futura interface Android;
- requisitos não funcionais e modelo de distribuição.

## Desenvolvimento

### Pré-requisitos

- JDK 21;
- Maven 3.9 ou posterior.

Na raiz do repositório:

```bash
mvn test
mvn verify
mvn javafx:run
python -m unittest discover -s scripts/tests -v
python scripts/ai_usage.py report
```

`mvn javafx:run` abre a prévia local. O texto é mantido apenas em memória nesta fatia: fechar a janela descarta as alterações. Localização, nomes e política de salvamento dos documentos continuam pendentes de decisão e não devem ser inferidos da prévia.

## Licença

TODO: escolher e adicionar a licença do projeto.
