
<img width="100%" alt="Apresentação do Projeto BELUGA" src="https://github.com/user-attachments/assets/879bf2de-9a6d-4562-82ff-66277e852fe3" />

# Projeto: BELUGA GCHE 2026
### GCHE Solutions

## Sobre o Projeto
- Área: Ambiente Industrial
- Responsáveis: Eduarda Mazzaria, Guilherme Hideki, Carlos Eduardo, Henzo Montanari
## 1.Escopo
--
O Projeto BELUGA 2026 tem como foco pessoas com deficiência visual no setor industrial, especialmente nas atividades de controle e identificação de estoque. O sistema permite que o trabalhador identifique peças por meio de câmeras, realizando a captura e o reconhecimento dos objetos. Após a identificação, o sistema consulta um banco de dados e fornece ao usuário informações previamente cadastradas em formato de áudio, como nome da peça, cor, descrição e outras características relevantes. O objetivo é promover maior acessibilidade e inclusão de pessoas com deficiência visual no ambiente industrial.



## Persona

**Matheus, 26 anos**

Matheus, de 26 anos, apresenta problemas visuais severos. Ele faz parte da equipe de controle de estoque da indústria em que trabalha e sente que não consegue contribuir significativamente com sua equipe, nem cumprir todas as tarefas que lhe são solicitadas, já que sua deficiência visual dificulta diversas atividades.

A empresa apresenta negligência ao não oferecer recursos suficientes para pessoas com essas particularidades, demonstrando a falta de medidas inclusivas relacionadas à acessibilidade.

O dia a dia de Matheus no ambiente de trabalho é dificultoso e intenso. Outro aspecto importante são os sistemas adotados pela empresa, que não possuem contraste adequado nem suporte de leitura que facilite sua utilização.

Além disso, muitos produtos apresentam características semelhantes, tornando difícil diferenciá-los visualmente e dificultando ainda mais o desempenho de suas atividades profissionais.

---

## Fluxo de Utilização

O fluxo principal de utilização do projeto seguirá a seguinte sequência:

**Login → Home → Cadastro de Objetos → Câmera → Histórico → Pesquisa**

**Funcionalidade opcional:** Ajuda → Auxílio

---

## Objetivo do Projeto

Promover maior acessibilidade às pessoas com deficiência visual, oferecendo uma solução tecnológica que auxilie na identificação e no controle de objetos dentro do ambiente industrial.

O projeto busca contribuir para um ambiente de trabalho mais acessível e inclusivo.

---

## Requisitos Funcionais

**RF01** - Eu, como trabalhador, gostaria de capturar a imagem ou o sinal da peça por meio de uma câmera.

**RF02** - Eu, como trabalhador, gostaria de ouvir a descrição detalhada previamente cadastrada (nome, cor e descrição) por meio de áudio.

**RF03** - Eu, como trabalhador, gostaria de utilizar comandos de voz para repetir a última informação.

**RF04** - Eu, como trabalhador, gostaria de atualizar automaticamente a quantidade de itens no estoque.

**RF05** - Eu, como trabalhador, gostaria de cadastrar novas peças e suas características no banco de dados.

**RF06** - Eu, como trabalhador, gostaria que o sistema possuísse um cadastro de peças, com quantidades e descrições editáveis.

**RF07** - Eu, como trabalhador, gostaria que o sistema possuísse um histórico para registrar os produtos que já passaram (foram emprestados) pela câmera.

**RF08** - Eu, como trabalhador, gostaria que o sistema possuísse recursos de pesquisa e filtros para os itens já registrados no banco de dados.

---

## Requisitos Não Funcionais

**RNF01** - Eu, como trabalhador, gostaria que a parte física do sistema fosse de fácil manuseio para o auxiliador.

**RNF02** - Eu, como trabalhador, gostaria que o sistema possuísse uma interface mínima e simples de utilizar.

**RNF03** - Eu, como trabalhador, gostaria que o aplicativo possuísse um sistema protegido e com segurança atualizada.

**RNF04** - Eu, como trabalhador, gostaria que o tempo entre a leitura do objeto e o retorno do áudio fosse inferior a 2 segundos.

**RNF05** - Eu, como trabalhador, gostaria que a câmera fosse resistente à poeira e a quedas, seguindo padrões industriais.

**RNF06** - Eu, como trabalhador, gostaria que a solução permitisse o cadastro de itens sem apresentar lentidão.

---

## Tecnologias Utilizadas

- **Python:** Desenvolvimento do Back-End.
- **JavaScript:** Funcionalidades e interatividade do Front-End.
- **HTML:** Estruturação das páginas.
- **CSS:** Estilização das interfaces.
- **YOLO:** Identificação e reconhecimento dos objetos.
- **Node.js / Express:** Desenvolvimento da Landing Page.
- **Câmera com iluminação:** Captura das imagens dos objetos.

---

## Funcionamento do Sistema

O sistema foi desenvolvido para auxiliar trabalhadores com deficiência visual nas atividades de identificação e controle de objetos.

### Perfis de Usuário

**Auxiliador:** Funcionário responsável pelo acompanhamento e auxílio ao agregado.

**Agregado:** Funcionário com deficiência visual que utiliza o sistema.

### Login

O auxiliador deverá realizar o login utilizando o ID previamente registrado de seu agregado.

Após a autenticação, o agregado poderá utilizar as funcionalidades disponibilizadas pelo sistema, respeitando as permissões de acesso.

### Câmera

A funcionalidade de câmera permite identificar objetos e fornecer informações por áudio.

O agregado deverá posicionar o objeto desejado diante da câmera para que o sistema realize sua identificação e retorne as informações por meio de áudio.

### Cadastro

O agregado não possui permissão para cadastrar ou editar peças, mas poderá consultar os objetos já cadastrados.

A funcionalidade também permite a leitura das informações dos objetos e seu retorno por áudio.

### Pesquisa

O agregado poderá pesquisar e filtrar os produtos previamente registrados no banco de dados.

Além disso, a funcionalidade contará com leitura e retorno das informações por áudio.

### Histórico

O agregado poderá consultar os itens que já passaram pela câmera.

O sistema permitirá o preenchimento de informações relacionadas aos registros, como data de passagem, nome do objeto e descrição.

### Ajuda / Auxílio

O agregado poderá enviar mensagens por meio do Telegram caso enfrente problemas relacionados ao seu registro ou ao funcionamento do sistema.

Essa funcionalidade também poderá ser utilizada para solicitar ajuda ou esclarecer dúvidas.

---

## Equipe de Desenvolvimento

O Projeto BELUGA 2026 é desenvolvido pela equipe GCHE Solutions, composta pelos seguintes integrantes:

**Carlos Eduardo**
- Função: Full-Stack e Banco de Dados.

**Eduarda Mazzari**
- Função: Front-End e Design.
- Cargo: Líder.

**Guilherme Kodama**
- Função: Front-End e Design.
- Cargo: Analista.

**Henzo Montanari**
- Função: Banco de Dados e Back-End.

---

## Documentação do Projeto

A documentação do Projeto BELUGA 2026 reúne as informações relacionadas ao desenvolvimento, às funcionalidades e à proposta da solução.

### QR Code

![QR Code do Projeto BELUGA](https://github.com/user-attachments/assets/82ba0647-1cf4-4db4-9016-d55ea8c1f4a0)

---

## Apresentação do Projeto

<img width="100%" alt="Apresentação do Projeto BELUGA" src="https://github.com/user-attachments/assets/879bf2de-9a6d-4562-82ff-66277e852fe3" />

---
