# Escopo do MVP

## Objetivo

Validar que uma aplicação local baseada em texto simples consegue controlar tarefas, reuniões e períodos trabalhados, produzir estatísticas dos dias e movimentar itens conforme seus estados sem perder dados.

## Capacidades indispensáveis

### 1. Controle do documento diário

O documento diário contém três seções:

- reuniões;
- lista de afazeres;
- períodos trabalhados.

#### Critérios de aceite preliminares

- [ ] O usuário consegue criar, abrir, editar e salvar o documento de um dia.
- [ ] O aplicativo reconhece as três seções definidas.
- [ ] Texto não reconhecido é preservado, não descartado silenciosamente.
- [ ] Um erro de sintaxe é informado sem corromper o arquivo.
- [ ] TODO: definir nomes, ordem e sintaxe exata das seções.

### 2. Estados de tarefas e reuniões

Marcações inicialmente propostas:

| Marcação | Significado preliminar |
|---|---|
| `[ ]` | não iniciada |
| `[x]` | concluída |
| `[d]` | deprecada ou obsoleta |
| `[/]` | parcialmente concluída e realocada para outro dia |
| `[m]` | não iniciada e movida para outro dia |

#### Critérios de aceite preliminares

- [ ] O aplicativo interpreta a mesma marcação para tarefas e reuniões.
- [ ] Marcações desconhecidas não causam perda do item.
- [ ] O estado original continua identificável após salvar e reabrir.
- [ ] TODO: definir se maiúsculas, espaços e variações são permitidos.
- [ ] TODO: decidir se `[/]` representa estado atual, ação de movimentação ou ambos.
- [ ] TODO: decidir se `[m]` é aplicado pelo usuário ou automaticamente.

### 3. Registro de períodos trabalhados

Formato preliminar:

```text
09:00 - 12:00
13:30 - 18:45
```

#### Critérios de aceite preliminares

- [ ] O aplicativo interpreta início e fim de cada período.
- [ ] O total diário considera múltiplos períodos sem contar intervalos.
- [ ] Horários inválidos, invertidos ou sobrepostos produzem diagnóstico claro.
- [ ] TODO: definir fuso horário, virada de dia e arredondamento.
- [ ] TODO: definir se períodos em andamento são suportados.

### 4. Estatísticas dos dias trabalhados

#### Critérios de aceite preliminares

- [ ] O aplicativo calcula o total trabalhado em um dia a partir de períodos válidos.
- [ ] O usuário consegue consultar estatísticas de um intervalo de dias.
- [ ] Resultados indicam quais documentos e períodos foram considerados.
- [ ] Entradas inválidas não são incluídas silenciosamente no cálculo.
- [ ] TODO: definir exatamente quais estatísticas, agrupamentos e fórmulas pertencem ao MVP.

### 5. Gestão automatizada por estado

#### Critérios de aceite preliminares

- [ ] Itens elegíveis são movidos ou copiados segundo regras documentadas.
- [ ] A operação é idempotente: repeti-la não cria duplicatas.
- [ ] O vínculo entre item original e item realocado permanece rastreável.
- [ ] A automação não apaga texto desconhecido nem conteúdo do usuário.
- [ ] Falhas parciais não deixam documentos em estado inconsistente.
- [ ] TODO: definir momento de execução, arquivo de destino e regras para cada estado.
- [ ] TODO: definir mecanismo de pré-visualização, confirmação e desfazer.

## Fora do MVP

- Pomodoro.
- Estatísticas específicas de tarefas concluídas.
- Barras visuais de completude.
- Cores associadas aos estados.
- Colaboração entre usuários.
- Sincronização entre múltiplos dispositivos, até que seja explicitamente promovida ao escopo.

## Requisitos não funcionais

Preencher antes da implementação:

- **Plataformas suportadas:** TODO
- **Volume esperado de documentos:** TODO
- **Tempo máximo de abertura/processamento:** TODO
- **Requisitos de acessibilidade:** TODO
- **Estratégia de backup e recuperação:** TODO
- **Privacidade e telemetria:** TODO
- **Compatibilidade entre versões do formato:** TODO

## Definição de pronto do MVP

- [ ] Todos os critérios aprovados possuem testes automatizados.
- [ ] Os fluxos principais foram verificados com arquivos reais de exemplo, sem dados pessoais.
- [ ] Nenhum teste, lint ou verificação de segurança está falhando.
- [ ] Instalação e uso local estão documentados e reproduzíveis.
- [ ] Migrações ou mudanças de formato preservam documentos existentes.
- [ ] Limitações conhecidas e procedimentos de recuperação estão documentados.
- [ ] O responsável pelo produto validou os fluxos de aceite.

## Questões que bloqueiam a arquitetura

1. O texto é a fonte de verdade ou uma representação exportada?
2. Qual formato canônico identifica data e seções?
3. Qual plataforma local será atendida primeiro?
4. O MVP exige funcionamento offline?
5. O aplicativo deve observar arquivos externos ou fornecer seu próprio editor?
