# Como a identificação funciona

A versão aberta usa um ensemble conservador:

1. **YOLO-World** localiza regiões que podem conter objetos do catálogo.
2. Cada região é recortada em três vistas: exata, com 8% e com 20% de contexto.
3. **CLIP ViT-B/32 local** compara cada vista com várias descrições/sinônimos de todas as classes.
4. O mesmo recorte também compete contra conceitos de **rejeição** (objetos fora do inventário).
5. A decisão exige score mínimo, margem para o segundo colocado, concordância entre vistas e evidência extra para trocar de família.
6. Regras geométricas eliminam rótulos incompatíveis com a forma da caixa.
7. O resultado precisa reaparecer em frames próximos da mesma origem antes de ser confirmado.

Os scores CLIP são similaridades cosseno, não probabilidades calibradas.

## Por que isso é melhor do que apenas adicionar classes

Um classificador fechado sempre tenta escolher alguma classe, mesmo quando vê um objeto desconhecido. O modo open-set adiciona uma saída prática: **rejeitar**. Assim um pedaço de metal, uma mão ou outro objeto não precisa virar `Mouse`, `Teclado` ou `Tesoura`.

Sinônimos ajudam variações legítimas, por exemplo `Garrafa PET` pode ser descrita como garrafa descartável transparente, garrafa de água PET ou garrafa de refrigerante; `Garrafa esportiva` inclui squeeze, shaker e garrafa de academia. Esses aliases produzem várias representações textuais para a mesma classe final.

## Perfil de precisão

Os limites padrão foram deliberadamente endurecidos. Isso prioriza **precision** (menos falsos positivos) sobre **recall** (detectar tudo). Em uma demonstração, `não identificado` é preferível a um objeto incorreto.

## Onde a precisão realmente sobe de nível

YOLO-World + CLIP é adequado para demonstração aberta, mas não substitui treinamento supervisionado. Para itens pequenos, parecidos ou específicos do seu ambiente (pregos, parafusos, porcas, arruelas, chaves, garrafas), a melhor evolução é fotografar os objetos reais em vários ângulos/iluminações, anotar as caixas e treinar `models\best.pt`.

O modo `auto` já prioriza esse modelo especializado quando ele existir, mantendo o pipeline aberto como fallback.
