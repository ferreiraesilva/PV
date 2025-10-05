# DTF – Documento Técnico-Funcional – SaaS SAFV

## 1. Arquitetura Multi-Tenant
- Cada empresa (tenant) possui isolamento lógico de dados e configurações.  
- Autenticação via JWT com escopo de TenantID.  
- Controles RLS no banco de dados.  
- Painel de administração central (Labs4Ideas) para provisionamento e monitoramento.

## 2. Controle de Acesso (RBAC)
Papéis definidos:  
- **Superadmin:** gestão global de tenants e planos.  
- **Suporte:** acesso restrito para troubleshooting.  
- **TenantAdmin:** gestão de usuários e configurações locais.  
- **Usuário:** acesso às funcionalidades de negócio.

## 3. Cobrança e Faturamento (MVP Manual)
- O sistema gera períodos de cobrança automáticos.  
- Operador marca faturas como quitadas manualmente.  
- Tenants inadimplentes são sinalizados como suspensos.

## 4. Auditoria e Logs
- Logs de acesso, autenticação e ações administrativas.  
- Eventos críticos monitorados com alertas automáticos.  
- Retenção de logs por 12 meses.

## 5. Segurança e LGPD
- TLS 1.2+ para criptografia em trânsito.  
- Backups diários segregados por tenant.  
- Retenção de backups por 90 dias + 12 meses arquivados.  
- Dados sensíveis armazenados com hashing e salting.  
- Dados eliminados após cancelamento e período de retenção.

## 6. APIs e Integrações
- APIs REST autenticadas via JWT.  
- Limite de requisições por plano (rate limiting).  
- Webhooks previstos para eventos futuros (ex: criação de tenant, quitação de fatura).

## 7. Módulos do SaaS

### 7.1 Simulação de Planos de Pagamento
- Cadastro de cenários e parâmetros financeiros.  
- Aplicação automática de índices de reajuste (IGPM, IPCA, INCC ou customizados).  
- Configuração de periodicidade: mensal ou aniversário do contrato.  
- Possibilidade de acréscimo percentual (ex: INCC + 1%).  
- **Regra por parcela (override):**  
  - `fixa` (sem reajuste) ou `indexada` com (indice_base, acrescimo_percentual, periodicidade_reajuste).  
  - Campo `congelada` para impedir reajuste em períodos definidos.  
  - **Precedência:** regra_da_parcela > regra_do_contrato > padrão_do_tenant.
- Cálculo automático do valor futuro reajustado (VF) antes do cálculo do PV.  
- Cálculo de PV, PMR e PMV com base nos valores corrigidos.  
- Comparação e exportação de resultados.

#### 7.1.1 Algoritmo (resumo)
1. Para cada parcela `i`, determinar a **regra efetiva** (aplicando precedência).  
2. Se `fixa` → `VF_i = valor_original`.  
3. Se `indexada` → obter série de índices e aplicar:  
   - **mensal:** multiplicar fator acumulado mês a mês até `data_venc_i`.  
   - **aniversario:** aplicar fator acumulado somente nos aniversários desde `data_contrato`.  
   - Considerar `acrescimo_percentual` somado à variação do índice (p.ex. INCC + 1% a.m.).  
4. Calcular `PV_i = VF_i / (1 + taxa_mensal)^(n_meses(data_base, data_venc_i))`.  
5. Somar `PV_total = Σ PV_i`.  
6. Persistir/retornar tabela: (valor_original, regra_aplicada, valor_corrigido=VF_i, PV_i).

### 7.2 Valoração de Carteira de Recebíveis
- Importação de dados históricos.  
- Cálculo de VPL e perdas ajustadas.  
- Geração de relatórios e comparativos de performance.

### 7.3 Benchmarking de Mercado
- Consolidação anônima de dados entre tenants.  
- Dashboards comparativos e rankings.

### 7.4 IA Preditiva e Recomendações
- Modelos de machine learning para previsão de inadimplência e oportunidades.  
- Painel de recomendações automáticas para otimização de planos e carteiras.

## 8. Monitoramento e Métricas
- Métricas de uptime, consumo por tenant e eventos de auditoria.  
- Alertas automáticos em falhas de login, acessos indevidos ou erros sistêmicos.

## 9. Modelo de Dados (trecho relevante)
- **Contrato**: id, tenant_id, data_contrato, regra_default (indice_base, acrescimo_percentual, periodicidade)  
- **Parcela**: id_contrato, num_parcela, data_venc, valor_original,  
  - tipo_regra (`fixa`|`indexada`), indice_base?, acrescimo_percentual?, periodicidade_reajuste?, congelada?  
  - campos calculados: valor_corrigido, pv_individual
