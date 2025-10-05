# PRD – Product Requirements Document – SaaS SAFV

## 1. Visão Geral
O SAFV é um sistema SaaS multi-tenant desenvolvido para automatizar e otimizar a gestão de fluxos de pagamento e recebíveis. Ele permite que empresas com vendas parceladas possam simular planos de pagamento, valorar carteiras, comparar resultados com o mercado e receber recomendações inteligentes com base em IA.

## 2. Objetivos de Negócio
- Melhorar a tomada de decisão comercial sobre condições de pagamento.  
- Fornecer valuation transparente de carteiras de recebíveis.  
- Oferecer comparativos de desempenho com dados de mercado.  
- Gerar recomendações automáticas de otimização financeira.

## 3. Público-Alvo
- Incorporadoras e construtoras  
- Concessionárias e distribuidoras  
- Indústrias com vendas parceladas  
- Empresas de serviços recorrentes  
- Fundos de investimento e securitizadoras

## 4. Funcionalidades Principais
- Simulação de Planos de Pagamento  
- Valoração de Carteira de Recebíveis  
- Benchmarking de Mercado  
- IA Preditiva e Recomendações  
- **Reajuste automático de parcelas com base em índices financeiros (IGPM, IPCA, INCC ou combinações como INCC + 1%)**  
- **Cálculo do Valor Presente (PV) considerando o valor corrigido das parcelas antes do desconto financeiro**  
- **Configuração de regra de reajuste por parcela (override): cada parcela pode ter índice/acréscimo/periodicidade próprios ou ser fixa (sem correção).**

## 5. Critérios de Sucesso
- Precisão nos cálculos financeiros (PV, PMR, PMV)  
- Redução do tempo de análise manual  
- Adoção crescente entre os segmentos-alvo  
- Geração de insights úteis e acionáveis  
- **Correção exata de parcelas conforme regras por contrato e por parcela**

## 6. Escopo
O produto será oferecido como SaaS hospedado em nuvem, com interface web responsiva, APIs REST e arquitetura multi-tenant segura. Integrações com ERPs e CRMs ocorrerão via API ou importação de planilhas.  
O sistema aplicará automaticamente os reajustes configurados antes de calcular o valor presente, permitindo **regras de reajuste por contrato e por parcela** (parcelas fixas ou indexadas, com overrides).
