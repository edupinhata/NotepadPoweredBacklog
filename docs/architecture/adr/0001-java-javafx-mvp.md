# ADR 0001: Java e JavaFX para o MVP local

- **Estado:** Aceito
- **Data:** 2026-08-28

## Contexto

O MVP será uma aplicação local, individual e baseada em documentos de texto simples. A primeira interface precisa apresentar um calendário navegável por semanas e dias, um resumo diário e um editor do documento selecionado.

O responsável pelo produto domina Java e deseja acelerar a primeira implementação sem impedir uma evolução futura para Android. A interface deve permanecer separada do domínio para que regras, parser e casos de uso possam ser reutilizados em outras plataformas.

## Decisão

O MVP utilizará:

- Java 21 como linguagem e runtime de desenvolvimento;
- JavaFX como toolkit da interface desktop;
- Maven para dependências, testes e build;
- CSS do JavaFX para apresentação visual;
- `jlink` e `jpackage`, por meio do build, para produzir runtime e instalador autocontidos quando a distribuição for implementada.

Kotlin e Compose Multiplatform não farão parte do MVP. Uma eventual interface Android será uma decisão posterior; a preferência inicial será uma camada móvel fina que reutilize o núcleo Java, sem antecipar essa complexidade no desktop.

A aplicação começará como um monólito modular local, com dependências apontando para dentro:

```text
JavaFX UI → casos de uso → domínio
               ↑           ↑
        persistência    parser/serializador
```

A interface JavaFX não conterá regras de parsing, cálculo de resumos, movimentação de itens ou acesso direto a arquivos. Essas responsabilidades ficarão em componentes Java sem dependência de JavaFX.

A primeira janela utilizará conceitualmente:

- `SplitPane` para separar navegação e edição;
- `TreeView` para semanas e respectivos dias;
- células customizadas para o resumo do dia;
- `TextArea` para editar o documento diário em texto simples.

O formato inicial visível no editor será:

```text
# Meetings
[ ] Meeting 1
[ ] Meeting 2

# To Do
[ ] Task 1
[ ] Task 2

# Worked
09:00 - 12:30
14:00 - 20:00
```

Os identificadores internos usarão `LocalDate`. O agrupamento semanal deverá tratar explicitamente o ano baseado em semana, inclusive dias próximos à virada do ano; não deverá depender apenas do número isolado da semana.

## Portabilidade para Android

Domínio, parser, serializador, cálculos e casos de uso serão mantidos independentes da interface e do sistema de arquivos desktop. Isso permite reutilizar a maior parte da lógica em um aplicativo Android futuro.

JavaFX não será tratado como garantia de reutilização integral da interface no Android. Antes dessa etapa, será realizado um experimento para comparar:

1. JavaFX/Gluon Mobile, buscando reaproveitamento de UI;
2. uma interface Android própria e fina, reutilizando o núcleo Java — alternativa inicialmente preferida;
3. Compose Multiplatform, caso seja aceita a adoção de Kotlin para a camada de interface.

Até esse experimento, a arquitetura garante portabilidade do núcleo, não identidade da UI entre desktop e Android.

## Alternativas consideradas

- **Swing:** estável e amplamente conhecido, mas menos adequado como primeira escolha para uma interface desktop moderna e para estilização consistente.
- **SWT:** oferece widgets nativos, porém aumenta a complexidade de distribuição e o acoplamento por plataforma sem benefício necessário ao MVP.
- **Compose Multiplatform:** oferece uma UI declarativa e forte alcance entre desktop e Android, mas é orientado a Kotlin; contraria o objetivo inicial de construir a interface em Java.
- **Vaadin:** permite escrever uma aplicação web em Java, mas introduz navegador/servidor e não preserva a simplicidade de uma aplicação local baseada diretamente em arquivos.
- **JavaFX com Gluon Mobile desde o início:** pode alcançar Android, mas adicionaria antecipadamente toolchain e restrições móveis ainda não necessárias para validar o MVP.

## Consequências

- O desenvolvimento inicial aproveita o domínio existente do responsável em Java.
- A aplicação terá uma interface desktop moderna sem exigir frontend web.
- O núcleo permanecerá testável sem inicializar o toolkit gráfico.
- A distribuição desktop exigirá artefatos específicos por sistema operacional.
- Um porte Android poderá reutilizar o núcleo, mas talvez exija uma nova camada de interface.
- Kotlin não será requisito para desenvolver ou manter o MVP desktop.
- Bibliotecas visuais adicionais, como ControlsFX ou temas de terceiros, não entram automaticamente; cada dependência deverá justificar uma necessidade real.

## Referências

- [JavaFX](https://openjfx.io/)
- [Introdução ao JavaFX](https://openjfx.io/openjfx-docs/)
- [Documentação Gluon](https://docs.gluonhq.com/)
- [Compose Multiplatform](https://kotlinlang.org/compose-multiplatform/)
