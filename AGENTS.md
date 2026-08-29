# AGENTS.md

Este arquivo define as regras de trabalho para agentes de IA e demais colaboradores automatizados neste repositório.

## 1. Fontes de verdade

Leia, nesta ordem, antes de propor ou alterar código:

1. `ProductDefinition.md` — definição original do produto;
2. `docs/product/vision.md` — objetivos, público e limites;
3. `docs/product/mvp.md` — escopo e critérios de aceite;
4. `docs/product/glossary.md` — linguagem do domínio;
5. `docs/architecture/adr/` — decisões arquiteturais aceitas;
6. o plano aplicável em `docs/plans/`.

Em caso de conflito, não escolha silenciosamente. Registre a divergência e peça uma decisão.

## 2. Estado atual

O projeto possui uma primeira fatia vertical executável em Java 21, JavaFX e Maven. O parser, o resumo em memória e a prévia JavaFX estão implementados; persistência, navegação anual completa, estatísticas por intervalo e automação de movimentação continuam planejadas. Não invente decisões ausentes nem apresente funcionalidades planejadas como implementadas.

## 3. Fluxo obrigatório para mudanças

1. confirmar o requisito e os critérios de aceite;
2. inspecionar arquivos e decisões existentes;
3. criar ou atualizar um plano quando a mudança envolver múltiplas etapas;
4. implementar uma pequena fatia vertical por vez;
5. para comportamento de produção, escrever primeiro um teste que falhe pelo motivo esperado;
6. escrever a implementação mínima que faça o teste passar;
7. executar o teste específico e depois todas as verificações aplicáveis;
8. revisar o diff quanto a escopo, segurança, simplicidade e documentação;
9. obter revisão independente para mudanças de código não triviais;
10. relatar comandos realmente executados e seus resultados.

## 4. Regras de engenharia

- Preferir soluções simples, explícitas e testáveis: YAGNI, DRY e baixo acoplamento.
- Preservar arquivos de texto do usuário; qualquer transformação deve ser determinística e testada.
- Não alterar silenciosamente o formato canônico de dados.
- Toda correção de bug deve incluir um teste de regressão.
- Não desabilitar testes, lint, análise de tipos ou controles de segurança para obter sucesso artificial.
- Não adicionar dependências sem justificar necessidade, manutenção, licença e riscos.
- Não introduzir abstrações para necessidades hipotéticas.
- Não deixar código comentado, depuração temporária ou TODOs sem contexto.
- Atualizar documentação quando comportamento, comandos ou decisões mudarem.

### 4.1. Idioma do código

Todo conteúdo que faça parte do código ou de artefatos técnicos executáveis deve estar em inglês. Isso inclui:

- nomes de pacotes, módulos, classes, interfaces, métodos, variáveis, constantes e arquivos de código;
- nomes e descrições de testes, fixtures e dados de exemplo mantidos no código;
- comentários, JavaDoc, TODOs técnicos e anotações de análise estática;
- mensagens de log, exceções, validações e diagnósticos técnicos;
- chaves de configuração, nomes de propriedades e scripts;
- identificadores de persistência, caso banco de dados ou metadados estruturados sejam introduzidos;
- textos da interface mantidos diretamente no código ou em arquivos de recursos.

Novos termos de domínio devem receber um nome canônico em inglês no `docs/product/glossary.md` antes de serem usados de maneiras diferentes no código. Não misture português e inglês em identificadores.

Documentação de produto, arquitetura e colaboração pode permanecer em português. Citações literais de entrada do usuário e testes de localização podem usar outro idioma quando esse idioma for o próprio comportamento testado. Se internacionalização for introduzida, as chaves dos recursos continuarão em inglês e os textos visíveis ficarão nos catálogos de tradução, não espalhados pelo código.

## 5. Segurança e privacidade

- Nunca adicionar senhas, tokens, chaves, dados pessoais ou credenciais ao repositório.
- Tratar o conteúdo dos arquivos editados pelo usuário como entrada não confiável.
- Validar caminhos e impedir traversal, sobrescrita indevida e acesso fora do espaço autorizado.
- Evitar execução de comandos, avaliação dinâmica e desserialização insegura de conteúdo do usuário.
- Aplicar o princípio do menor privilégio e práticas OWASP quando houver interfaces web ou APIs.
- Coletar somente os dados necessários e documentar qualquer telemetria antes de implementá-la.

## 6. Dados e compatibilidade

- Alterações de formato exigem decisão arquitetural, estratégia de compatibilidade e testes com dados antigos.
- Migrações devem preservar dados e oferecer recuperação ou rollback quando aplicável.
- Sincronização entre dispositivos não deve ser introduzida antes de uma estratégia explícita de conflitos.

## 7. Git e entrega

- Manter alterações pequenas e focadas.
- Não combinar refatoração ampla com mudança funcional sem justificativa.
- Não fazer commit, push, abrir PR, publicar artefatos ou reescrever histórico sem autorização explícita do responsável pelo projeto.
- Antes de declarar conclusão, informar arquivos alterados, verificações executadas e pendências conhecidas.

## 8. Convenções pendentes

Preencher após a escolha da stack:

- **Linguagem/runtime:** Java 21
- **Interface desktop:** JavaFX
- **Gerenciador de dependências:** Maven
- **Idioma do código:** inglês
- **Instalação:** JDK 21 e Maven 3.9+
- **Execução local:** `mvn javafx:run`
- **Testes:** `mvn test`
- **Lint/format:** compilação com `-Xlint:all -Werror`; formatador dedicado pendente
- **Análise de tipos:** compilador Java 21 durante `mvn verify`
- **Build/empacotamento:** `mvn verify` produz o JAR; instalador autocontido pendente
- **Verificações de segurança:** TODO
