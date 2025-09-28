# Estrategia de Anonimizacao para Benchmarking

## Objetivos
- Garantir que os datasets de benchmarking ingeridos nao revelem PII ou detalhes competitivos sensiveis.
- Aplicar k-anonymity basica (k>=3) em cada combinacao de indicadores.
- Manter utilidade analitica para o calculo de metricas agregadas.

## Regras Aplicadas
- **Normalizacao de codigo de metrica**: uppercase e trimming para remover variacoes de digitacao.
- **Bucketizacao de segmento**: apenas os tres primeiros caracteres em uppercase, seguidos de `*` (ex.: "PME-Logistica" -> "PME*").
- **Bucketizacao de regiao**: dois primeiros caracteres em uppercase, seguidos de `*` (ex.: "Sudeste" -> "SU*").
- **Rounding de valores**: valores numericos arredondados para duas casas decimais antes de qualquer agregacao.
- **Filtragem por cardinalidade**: combinacoes com menos de tres ocorrencias sao descartadas do resultado agregado.
- **Mascaramento de payloads**: apenas agregados e contagens sao expostos no audit trail (`payload_out`), evitando retencao de linhas brutas.
- **Transmissao de dados**: uploads locais sao enviados como fluxo binario (`application/octet-stream`) com parametro de nome, evitando depender de bibliotecas externas de multipart.

## Limitacoes Conhecidas
- Uploads acima de 2 MB sao rejeitados para limitar manipulacao de grandes volumes sem paginacao.
- Arquivos Excel (`.xlsx`) requerem `openpyxl`; ambientes sem a dependencia devem usar CSV.
- Futuras evolucoes podem armazenar agregados em particoes especificas de benchmarking no PostgreSQL e aplicar tecnicas adicionais (ex.: differential privacy).
