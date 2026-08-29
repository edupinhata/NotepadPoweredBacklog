# Arquitetura

A arquitetura ainda não foi escolhida. Esta área registra contexto, opções e decisões sem apresentar hipóteses como fatos implementados.

## Direcionadores conhecidos

- aplicação inicialmente local e individual;
- edição e interpretação de texto simples;
- preservação integral dos dados do usuário;
- evolução futura possível para múltiplos dispositivos;
- ausência de colaboração entre usuários no escopo atual;
- necessidade de estatísticas e automações determinísticas.

## Decisões necessárias

1. plataforma e modelo de distribuição inicial;
2. texto como fonte de verdade ou como importação/exportação;
3. formato canônico do documento diário;
4. editor próprio ou integração com arquivos externos;
5. persistência de metadados e índices;
6. estratégia offline;
7. limites entre domínio, parser, armazenamento e interface;
8. backup, recuperação e compatibilidade;
9. estratégia futura de sincronização e conflitos;
10. observabilidade e telemetria, se houver.

## Princípios provisórios

- separar regras de domínio da interface e da persistência;
- manter parsing e serialização determinísticos;
- testar ida e volta do texto sem perda de informação;
- evitar dependência da futura sincronização no desenho do primeiro MVP;
- registrar decisões significativas como ADRs antes da implementação.

## Modelo inicial a avaliar

Uma arquitetura em camadas ou portas e adaptadores pode separar:

```text
Interface local
      ↓
Casos de uso
      ↓
Domínio puro
  ↙         ↘
Parser      Repositório de documentos
```

Isto é apenas uma hipótese para avaliação, não uma decisão aceita.

## Registros de decisão

Consulte [`adr/README.md`](adr/README.md) para o processo e o modelo de ADR.
