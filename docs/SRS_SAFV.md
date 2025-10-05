# SRS – Software Requirements Specification – SaaS SAFV

## 1. Introdução
### 1.1 Propósito
Descrever os requisitos funcionais e não funcionais do sistema SAFV, garantindo clareza e rastreabilidade entre o PRD e o DTF.

### 1.2 Escopo
Sistema SaaS multi-tenant com módulos de simulação, valoração, benchmarking e IA preditiva.

## 2. Requisitos Funcionais
- **RF1:** O sistema deve permitir cadastrar e comparar múltiplos planos de pagamento.  
- **RF2:** O sistema deve calcular o Valor Presente (PV), Prazo Médio de Recebimento (PMR) e Prazo Médio de Venda (PMV).  
- **RF3:** O sistema deve importar e processar dados históricos de carteiras de recebíveis.  
- **RF4:** O sistema deve calcular valores presentes líquidos ajustados por inadimplência e cancelamento.  
- **RF5:** O sistema deve permitir comparações com benchmarks de mercado anonimizados.  
- **RF6:** O sistema deve gerar relatórios exportáveis em PDF e Excel.  
- **RF7:** O sistema deve gerar recomendações automáticas baseadas em modelos preditivos.  
- **RF8:** O sistema deve aplicar **índices de reajuste (IGPM, IPCA, INCC ou combinações)** às parcelas de contratos de venda futura **antes de calcular o Valor Presente (PV)**.  
- **RF9:** O sistema deve permitir configurar a periodicidade de aplicação do índice (mensal ou aniversário do contrato) e o percentual adicional (ex: INCC + 1%).  
- **RF10:** O sistema deve permitir **override de regra de reajuste por parcela**, incluindo:  
  - tipo_regra: `fixa` (sem reajuste) | `indexada`  
  - indice_base (quando indexada): IGPM | IPCA | INCC | custom  
  - acrescimo_percentual (p.ex. +1)  
  - periodicidade_reajuste: mensal | aniversario  
  - congelada: boolean (impedir reajuste em períodos específicos)
- **RF11:** Em cenários com regras mistas (parcelas fixas e indexadas), o cálculo deve respeitar a **regra efetiva da parcela**.

## 3. Requisitos Não Funcionais
- **NFR1:** Disponibilidade mínima de 99,5%.  
- **NFR2:** Tempo médio de resposta inferior a 2 segundos por cálculo.  
- **NFR3:** Escalabilidade horizontal em ambiente cloud-native.  
- **NFR4:** Logs centralizados e auditáveis.  
- **NFR5:** Conformidade com a LGPD.  
- **NFR6:** Autenticação JWT e controle de acesso RBAC.  
- **NFR7:** Dados segregados por tenant via RLS.

## 4. Restrições
- O sistema será exclusivamente SaaS, sem necessidade de instalação local.  
- A cobrança é realizada fora do sistema (painel apenas informativo no MVP).

## 5. Suposições e Dependências
- Integrações futuras com ERPs e CRMs.  
- Indexadores financeiros atualizados via API externa ou tabela manual.  
- Taxas de desconto e índices devem ser parametrizáveis por contrato e cenário de simulação.  
- Regras por parcela devem sobrescrever as regras do contrato quando presentes.
