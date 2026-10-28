# GHCE — detector híbrido

Sistema com frontend original, backend Python, MySQL, câmera, histórico,
YOLO-World e verificação auxiliar CLIP.

## Documentos úteis

- `COMO_RODAR.md`: instalação e inicialização pelo CMD.
- `training/README.md`: imagens, anotações e treinamento.
- `GUIA_EMPRESARIAL.md`: cuidados mínimos para produção.
- `../Bot_Telegram/README.md`: bot opcional.

## Funcionamento do detector

O modo padrão é `DETECTION_MODE=auto`:

- usa `Back-End\models\best.pt` quando existir;
- sem `best.pt`, usa o YOLO-World incluído e exige o CLIP local validado;
- mantém o contrato do frontend: `name`, `class_id`, `bbox` e `conf`.

As 65 classes do modo aberto ficam em:

```text
Back-End\configuration\object_catalog.json
```

## Endereços

```text
Frontend: http://localhost:5500/Login/index1_pag_Login.html
Backend:  http://localhost:5000
Saúde:    http://localhost:5000/api/health
Modelo:   http://localhost:5000/api/modelo
Métricas: http://localhost:5000/api/metricas
```

O checkpoint CLIP não está neste pacote: instale-o com `INSTALAR_CLIP.cmd` após `pip install -r requirements.txt`.

Para começar, siga `COMO_RODAR.md`.


Perfis Admin/Trabalhador e Telegram: consulte PERFIS_E_TELEGRAM.md antes de atualizar o banco.
