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
- Cálculo automático de PV, PMR e PMV.  
- Comparação e exportação de resultados.

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
