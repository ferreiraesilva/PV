# SAFV Frontend

Aplicação web construída com Vite + React + TypeScript para operar o backend FastAPI do SAFV.

## Pré-requisitos
- Node.js 20+
- npm ou pnpm/yarn (exemplos abaixo usam npm)

## Configuração rápida
1. Copie as variáveis de ambiente padrão:
   ```bash
   cp .env.example .env
   ```
2. Ajuste `VITE_API_BASE_URL` conforme o endpoint do backend (padrão: `http://localhost:8000/v1`).
3. Instale as dependências e suba o servidor local:
   ```bash
   npm install
   npm run dev
   ```
4. Acesse `http://localhost:5173` e autentique-se com `tenantId`, e-mail e senha válidos.

## Funcionalidades principais
- **Autenticação JWT** com refresh automático usando `/t/{tenantId}/login` e `/refresh`.
- **Simulações financeiras**: construtor de parcelas para `POST /t/{tenant}/simulations` exibindo PV, FV, PMT e métricas.
- **Valuation de carteira**: criação de fluxos e cenários dinâmicos para `POST /valuations/snapshots/{id}/results`.
- **Benchmarking**: upload CSV/XLSX para `POST /benchmarking/batches/{batchId}/ingest` e consulta `GET /aggregations`.
- **Recomendações (placeholder)**: orquestra runs de IA (`/recommendations/runs`) com tratamento amigável caso o endpoint não exista.
- **Auditoria**: filtros simples sobre `/audit/logs`, com mensagens claras quando indisponível.

## Scripts úteis
- `npm run dev`: ambiente local com HMR.
- `npm run build`: build de produção.
- `npm run preview`: pré-visualização local do build.

## Estrutura resumida
```
frontend/
├── src/
│   ├── api/              # clients REST
│   ├── components/       # layout + utilitários
│   ├── hooks/            # hooks customizados
│   ├── pages/            # telas de domínio
│   ├── providers/        # AuthProvider e contexto
│   ├── styles/           # css global
│   └── main.tsx          # bootstrap da app
├── index.html            # template raíz
├── package.json
├── tsconfig*.json
└── vite.config.ts
```

## Integração com backend
- O frontend assume o mesmo tenantId utilizado pelas rotinas FastAPI.
- Tokens são persistidos em `sessionStorage` para evitar vazamento entre tenants.
- As requisições usam `fetch` com headers padronizados, exibindo mensagens de erro amigáveis quando o backend responde 4xx/5xx.

## Próximos passos sugeridos
- Substituir placeholders visuais por design system corporativo.
- Adicionar testes end-to-end (Playwright/Cypress) cobrindo os fluxos principais.
- Integrar com outros endpoints do OpenAPI (Users, Roles) assim que implementados no backend.
