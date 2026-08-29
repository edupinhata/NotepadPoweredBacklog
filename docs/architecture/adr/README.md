# Registros de decisão arquitetural (ADRs)

ADRs explicam decisões técnicas importantes e duradouras. Devem reduzir dúvidas futuras, não criar burocracia.

## Quando criar

Use um ADR somente quando a decisão for:

- cara ou difícil de reverter;
- transversal a várias partes do sistema;
- relevante para segurança, privacidade ou integridade de dados;
- uma escolha entre alternativas legítimas que futuros colaboradores precisarão compreender.

Não crie ADR para detalhes locais, nomes, pequenas refatorações ou escolhas facilmente reversíveis. Nesses casos, a issue ou o PR é suficiente.

## Convenção

- Nome: `NNNN-titulo-curto.md`.
- Uma decisão por arquivo.
- Estados: `Proposto`, `Aceito`, `Rejeitado`, `Substituído` ou `Obsoleto`.
- Não reescreva um ADR aceito para esconder o histórico; crie outro que o substitua.

## Processo enxuto

1. copie [`0000-template.md`](0000-template.md);
2. registre contexto, decisão, alternativas e consequências;
3. obtenha aprovação e marque como `Aceito`;
4. vincule o ADR à implementação quando isso ajudar a rastreabilidade.

## Índice

| ADR | Título | Estado |
|---|---|---|
| — | Nenhuma decisão registrada ainda | — |
