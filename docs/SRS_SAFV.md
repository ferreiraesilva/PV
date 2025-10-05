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
