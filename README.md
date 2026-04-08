# Projetos_BELUGA_2026
Nome do Grupo:GCHE solutions
Grupo de auxílio GITHUB |  
Carlos Eduardo - FullStack + BD |  
Eduarda Mazzari - FrontEnd + Design - LIDER |  
Guilherme Kodama - FrontEnd + Design - ANALISTA |  
Henzo Montanari - BD + BackEnd |  
GCHE Solutions |  
Consistiria em focar nos indivíduos com pessoas que têm deficiência visuais no setor indústrial. Especialmente no controle e identificação de estoque. Ele permitiria que o trabalhador identificasse peças por meio de sensores, câmeras ou outros dispositivos, fazendo a leitura e o reconhecimento do objeto. E após isso, o sistema consulta um banco de dados e fornece ao usuário informações detalhadas em formato de áudio, como nome da peça, tipo, cor, localização e outras características relevantes.
<img width="2048" height="1118" alt="569127385-55e019b2-c98a-4dc4-a4ec-a64650730596" src="https://github.com/user-attachments/assets/24e281b9-6a62-41a1-84f1-e8eed59a878a" />

Definição da Persona 
Matheus, 26 anos, apresenta problemas visuais sevéros. Ele faz parte da equipe de controle de estoque da indùstria que trabalha, se sente como alguém que não consegue agregar muito à sua equipe, e que não é capaz de cumprir tudo o que lhe é pedido, já que a sua dificuldade individual o atrapalha muito em diversos fatores. A empresa não consegue oferecer tantos auxílios à essas pessoas que tem essa particularidade, apresentando faltas de maneiras incluidoras como a acessibilidade e inclusão, o dia-a-dia de Matheus no ambiente de trabalho é dificultoso e intenso. Outros aspecos a serem notados são os sistemas adotados pela a empresa, ele não possui contraste adequado e nem um suporte de leitura que o ajude e facilite mais, quebrando essas barreiras. A falta de etiquetas e identificação é outra dor de Matheus, já que muitas embalagens de produtos não possuem etiquetas que sejam fáceis de diferenciar, dificultando a sua distinção entre itens de tamanhos similares. 
  
Caminho: 
Uso do Python version 3.11 ou Java, Cabe ao reponsável Beck-end decidir qual à trabalhar.
É possível que, o início do projeto seja marcado pelo uso do teachable machine, uma ferramenta do Google que permite o registro e guardamento de imagens e retornando a sua identificação. Ele funciona da seguinte forma: Primeiro é necessário que as imagens dos objetos escolhidos seja registradas, por volta de 3.000 à 5.000 fotos dos objetos, depois a ferramenta processará essa informação e passará por uma checkagem. As imagens seão guardadas e convertidas em ZIP, na sala de aula foi possível que o python e o teachable machine conversem entre sí. 
OBS: O código necessita o import e download do TensorFlow, Numpy e PIL e do ambiente virtual venv (py -3.11 -m venv venv);  
OBS: Para que seja possível o Python identificar o objeto, se, salvo no Teachable estiver em MODELO de tamanho X(por exemplo 64x64) a grade escolhida no Python deve também ter o MESMO tamanho no código;  
OBS: Uso da GrayScle (RGB) deve ter o mesmo número, por exemplo se salvo no aplicativo: [1, 96, 96, 1], ou seja classe 1 (preto e branco) então no código também deve ter o mesmo tamanho.  
https://cagiuso2.atlassian.net/jira/core/projects/GHCE/board?filter=&groupBy=status
