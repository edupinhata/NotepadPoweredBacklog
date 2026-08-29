# Registros de decisão arquitetural (ADRs)

ADRs registram decisões técnicas importantes, seu contexto e suas consequências. Eles evitam que agentes e colaboradores rediscutam ou contradigam decisões sem perceber.

## Convenção

- Nome: `NNNN-titulo-curto.md`.
- Numeração sequencial com quatro dígitos.
- Uma decisão principal por arquivo.
- Estados permitidos: `Proposto`, `Aceito`, `Rejeitado`, `Substituído` e `Obsoleto`.
- Um ADR aceito não é reescrito para esconder a história; uma nova decisão o substitui.

## Processo

1. copie [`0000-template.md`](0000-template.md);
2. descreva contexto, forças e alternativas reais;
3. registre riscos e consequências;
4. submeta a decisão para aprovação;
5. somente após o estado `Aceito`, trate a escolha como restrição do projeto;
6. vincule implementação, plano ou ADR substituto quando aplicável.

## Primeiros ADRs sugeridos

- plataforma e modelo de distribuição do MVP;
- texto como fonte de verdade;
- formato canônico do documento diário;
- estratégia de persistência e recuperação;
- limites arquiteturais entre editor, domínio e infraestrutura;
- linguagem e stack de desenvolvimento;
- estratégia de testes;
- estratégia futura de sincronização, apenas quando entrar no escopo.

## Índice

| ADR | Título | Estado |
|---|---|---|
| — | Nenhuma decisão registrada ainda | — |
