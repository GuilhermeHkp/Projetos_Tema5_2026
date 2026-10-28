# COMO RODAR — Windows CMD

Este ZIP já é a pasta do projeto. **Não existe uma pasta `PROJETOSV1` acima dele.**
Execute os `.cmd` na mesma pasta onde estão `Back-End` e `Front-End`.

## Primeira vez

Se Python 3.12 x64 ainda não estiver instalado:

```cmd
BAIXAR_PYTHON_312.cmd
```

Depois feche e abra o CMD.

Prepare o ambiente:

```cmd
INSTALAR_WINDOWS.cmd
```

O script cria `.venv` nesta pasta e preserva `Back-End\.env` se ele já existir.

## MySQL

Configure `Back-End\.env` com `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` e `DB_NAME`.
O arquivo enviado foi conferido e tem sintaxe válida; a senha nunca é impressa pelos diagnósticos.

Depois rode:

```cmd
CRIAR_TABELAS.cmd
```

Esse comando cria apenas o que estiver faltando e configura o login de demonstração:

```text
responsável: 1
associado:   2
senha:       123456
```

## Validar

```cmd
DIAGNOSTICAR.cmd
VALIDAR_PROJETO.cmd
```

Com `DETECTION_MODE=auto`, `Back-End\models\best.pt` tem prioridade.
YOLO-World + CLIP são fallback opcionais e **não bloqueiam** a validação quando o `best.pt` está carregável.

## Rodar diariamente

CMD 1:

```cmd
RODAR_BACKEND.cmd
```

CMD 2:

```cmd
RODAR_FRONTEND.cmd
```

Abra:

```text
http://localhost:5500/Login/index1_pag_Login.html
```

API:

```text
http://127.0.0.1:5000/api/health
```

## CLIP / modo aberto

O CLIP só é necessário quando você realmente usar `DETECTION_MODE=open`, ou quando `auto` não tiver um `best.pt`.
Nesse caso rode:

```cmd
INSTALAR_CLIP.cmd
```

e coloque `yolov8s-worldv2.pt` em `Back-End\models`.
