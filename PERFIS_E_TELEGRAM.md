# Admin e Trabalhador

O login utiliza seu ID de usuário e senha. O colaborador associado é opcional. O perfil vem do banco e não pode ser escolhido na tela de login.

| Função | Admin | Trabalhador |
|---|---|---|
| Consultar peças e histórico | Sim | Sim |
| Usar câmera e registrar checagem | Sim | Sim |
| Cadastrar, editar e excluir peças | Sim | Não |
| Editar e excluir histórico | Sim | Não |
| Solicitar auxílio | Sim, pelos botões da Home | Sim |
| Consultar solicitações | Todas | Apenas suas |
| Marcar solicitação como atendida | Sim | Não |

## Atualizar o banco

Depois de extrair, execute CRIAR_TABELAS.cmd. Ele adiciona o campo perfil e a tabela de solicitações sem apagar peças e históricos. Esse comando também executa o seed e redefine os usuários de demonstração 1 e 2 e suas senhas, como na versão anterior.

Contas de demonstração após executar:
- Admin: ID 1, senha 123456.
- Trabalhador: ID 2, senha 123456.
- O campo de colaborador associado pode ficar vazio.

Se você já usa as contas 1 e 2 e não quer redefini-las, execute apenas `python -m database.create_tables` dentro de Back-End, com o ambiente virtual ativo. Todos os usuários existentes recebem o perfil trabalhador. Defina explicitamente um Admin pelo MySQL:

```sql
UPDATE USUARIO SET perfil = 'admin' WHERE usuario_id = 1;
```

Troque o ID pelo usuário que realmente será Admin. Para rebaixar, use perfil = 'trabalhador'. Não existe promoção pelo navegador. O servidor confere o perfil e se a conta está ativa em cada requisição.

## Telegram

1. Crie um bot com @BotFather no Telegram e obtenha seu token.
2. O Admin deve abrir o bot e enviar /start.
3. Consulte `https://api.telegram.org/botSEU_TOKEN/getUpdates` no seu computador. Encontre o `message.chat.id` da mensagem do Admin. Não compartilhe o token.
4. Preencha Back-End/.env:

```env
TELEGRAM_BOT_TOKEN=token_do_seu_bot
TELEGRAM_ADMIN_CHAT_ID=id_do_chat_do_admin
```

5. Reinicie a API. Entre como Trabalhador e clique em “Solicitar auxílio do Admin”, ou nos botões Ajuda/Revisão da Home.

O pedido é salvo no banco antes do envio. Se o Telegram não estiver configurado ou falhar, a tela informa que a notificação não foi enviada; o pedido continua disponível no sistema. Não há reenvio automático.

O Admin recebe a notificação, entra no GHCE, consulta as solicitações e realiza a alteração como Admin. Depois marca o pedido como atendido. A notificação não libera permissões para o Trabalhador, e a aprovação não ocorre dentro do Telegram.

Documentação da integração: https://core.telegram.org/bots/api#sendmessage

## Sessão e validação

Sessão por token, válida por 8 horas. Sair revoga o token; reiniciar a API exige novo login. Cadastrar, editar e excluir exige Admin no servidor, mesmo que alguém altere o HTML ou sessionStorage. Senhas não são retornadas no login.

Mantido o esquema de senhas em texto do projeto original. Para uso real, migrar para hashes de senha e servir por HTTPS.

Foram executados 8 testes automatizados de acesso e solicitação com banco, detector e Telegram simulados. Também foi verificada a sintaxe Python e JavaScript. Não foi possível validar MySQL, câmera física e entrega real ao Telegram neste ambiente.

Executar testes de acesso dentro de Back-End: `python -m unittest tests.test_access_api -v`.

## Botões e avisos de edição

Histórico e Cadastro exibem a coluna Ações com Editar e Excluir. Admin abre um formulário com nome, descrição e quantidade; excluir exige confirmação. Trabalhador vê os mesmos botões, mas recebe o aviso estilizado “Permissão necessária” ao clicar e nenhuma alteração é enviada. O cadastro também apresenta esse aviso para Trabalhador.

Editar ou excluir um histórico não modifica o cadastro da peça. Excluir uma peça que possui vínculos no banco pode ser impedido para preservar os registros.

Nesta atualização foram conferidas as sintaxes JavaScript e repetidos os testes de acesso da API. A validação visual automatizada não pôde ser executada porque este ambiente não contém um navegador instalado.
