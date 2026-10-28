# Uso empresarial

Antes de colocar o sistema em produção:

- teste todas as classes na câmera e iluminação reais;
- inclua mãos, fundos variados, oclusões e objetos parecidos;
- meça falsos positivos, falsos negativos e latência;
- use `best.pt` treinado com imagens próprias para peças críticas;
- troque `CORS_ORIGIN=*` pela origem real do frontend;
- use HTTPS, autenticação corporativa, logs e backups;
- proteja o `.env` e restrinja o acesso ao MySQL;
- confira o licenciamento comercial da Ultralytics.

Monitoramento:

```text
http://localhost:5000/api/health
http://localhost:5000/api/modelo
http://localhost:5000/api/metricas
```

O modelo genérico ajuda a iniciar, mas a aprovação industrial depende de testes
com dados separados e condições reais da empresa.
