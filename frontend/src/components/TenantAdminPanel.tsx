import { useEffect, useMemo, useState } from 'react';

import type { FinancialSettings, PaymentPlanTemplate, TenantSummary } from '../api/types';
import {
  createPaymentPlanTemplate,
  getFinancialSettings,
  listPaymentPlanTemplates,
  updateFinancialSettings,
  updatePaymentPlanTemplate,
  type FinancialSettingsUpdatePayload,
  type PaymentPlanInstallmentInput,
  type PaymentPlanTemplateCreatePayload,
  type PaymentPlanTemplateUpdatePayload,
} from '../api/adminPortal';

interface TenantAdminPanelProps {
  accessToken: string | null;
  tenants: TenantSummary[];
  selectedTenantId: string | null;
  onSelectTenant: (tenantId: string) => void;
  canSelectTenant: boolean;
}

interface TemplateDraftInstallment {
  period: string;
  amount: string;
}

interface TemplateDraft {
  id?: string;
  productCode: string;
  name: string;
  description: string;
  principal: string;
  discountRate: string;
  isActive: boolean;
  metadataText: string;
  installments: TemplateDraftInstallment[];
}

const defaultDraft = (): TemplateDraft => ({
  productCode: '',
  name: '',
  description: '',
  principal: '',
  discountRate: '',
  isActive: true,
  metadataText: '',
  installments: [{ period: '', amount: '' }],
});

const asDraft = (template: PaymentPlanTemplate): TemplateDraft => ({
  id: template.id,
  productCode: template.productCode,
  name: template.name ?? '',
  description: template.description ?? '',
  principal: template.principal.toString(),
  discountRate: template.discountRate.toString(),
  isActive: template.isActive,
  metadataText: template.metadata ? JSON.stringify(template.metadata, null, 2) : '',
  installments: template.installments.map((item) => ({
    period: item.period.toString(),
    amount: item.amount.toString(),
  })),
});

const normalizeNumber = (value: string, allowEmpty = true): number | null => {
  if (value.trim() === '') {
    if (allowEmpty) {
      return null;
    }
    throw new Error('Informe um valor numérico.');
  }
  const parsed = Number(value);
  if (Number.isNaN(parsed)) {
    throw new Error('Valor numérico inválido.');
  }
  return parsed;
};

const parseMetadata = (value: string): Record<string, unknown> | null => {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  try {
    const parsed = JSON.parse(trimmed);
    if (typeof parsed !== 'object' || parsed === null) {
      throw new Error('O metadata deve ser um objeto JSON.');
    }
    return parsed as Record<string, unknown>;
  } catch (error) {
    throw new Error(`Metadata inválido: ${(error as Error).message}`);
  }
};

export function TenantAdminPanel({
  accessToken,
  tenants,
  selectedTenantId,
  onSelectTenant,
  canSelectTenant,
}: TenantAdminPanelProps) {
  const [settings, setSettings] = useState<FinancialSettings | null>(null);
  const [settingsForm, setSettingsForm] = useState({
    periodsPerYear: '',
    defaultMultiplier: '',
    cancellationMultiplier: '',
  });
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [settingsStatus, setSettingsStatus] = useState<string | null>(null);

  const [templates, setTemplates] = useState<PaymentPlanTemplate[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(false);
  const [templateDraft, setTemplateDraft] = useState<TemplateDraft | null>(null);
  const [templateSaving, setTemplateSaving] = useState(false);
  const [templateStatus, setTemplateStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const activeTenant = useMemo(
    () => tenants.find((tenant) => tenant.id === selectedTenantId) ?? null,
    [tenants, selectedTenantId],
  );

  useEffect(() => {
    if (!accessToken || !selectedTenantId) {
      setSettings(null);
      setSettingsForm({
        periodsPerYear: '',
        defaultMultiplier: '',
        cancellationMultiplier: '',
      });
      setTemplates([]);
      setSettingsStatus(null);
      setTemplateStatus(null);
      setTemplateDraft(null);
      setSettingsLoading(false);
      setTemplatesLoading(false);
      return;
    }

    let cancelled = false;
    setSettingsLoading(true);
    setTemplatesLoading(true);
    setError(null);
    setSettingsStatus(null);
    setTemplateStatus(null);
    setTemplateDraft(null);
    setTemplates([]);

    (async () => {
      try {
        const [fetchedSettings, fetchedTemplates] = await Promise.all([
          getFinancialSettings(accessToken, selectedTenantId),
          listPaymentPlanTemplates(accessToken, selectedTenantId),
        ]);
        if (cancelled) {
          return;
        }
        setSettings(fetchedSettings);
        setSettingsForm({
          periodsPerYear: fetchedSettings.periodsPerYear?.toString() ?? '',
          defaultMultiplier: fetchedSettings.defaultMultiplier?.toString() ?? '',
          cancellationMultiplier: fetchedSettings.cancellationMultiplier?.toString() ?? '',
        });
        setTemplates(fetchedTemplates);
      } catch (err) {
        if (!cancelled) {
          setError((err as Error).message);
        }
      } finally {
        if (!cancelled) {
          setSettingsLoading(false);
          setTemplatesLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [accessToken, selectedTenantId]);

  const handleSettingsChange = (field: keyof typeof settingsForm, value: string) => {
    setSettingsForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSaveSettings = async () => {
    if (!accessToken || !selectedTenantId) {
      return;
    }
    setSettingsSaving(true);
    setSettingsStatus(null);
    setError(null);
    try {
      const payload: FinancialSettingsUpdatePayload = {
        periodsPerYear: normalizeNumber(settingsForm.periodsPerYear),
        defaultMultiplier: normalizeNumber(settingsForm.defaultMultiplier),
        cancellationMultiplier: normalizeNumber(settingsForm.cancellationMultiplier),
      };
      const updated = await updateFinancialSettings(accessToken, selectedTenantId, payload);
      setSettings(updated);
      setSettingsForm({
        periodsPerYear: updated.periodsPerYear?.toString() ?? '',
        defaultMultiplier: updated.defaultMultiplier?.toString() ?? '',
        cancellationMultiplier: updated.cancellationMultiplier?.toString() ?? '',
      });
      setSettingsStatus('Configurações financeiras atualizadas com sucesso.');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSettingsSaving(false);
    }
  };

  const handleStartCreation = () => {
    setTemplateDraft(defaultDraft());
    setTemplateStatus(null);
    setError(null);
  };

  const handleEditTemplate = (template: PaymentPlanTemplate) => {
    setTemplateDraft(asDraft(template));
    setTemplateStatus(null);
    setError(null);
  };

  const handleCancelTemplate = () => {
    setTemplateDraft(null);
    setTemplateStatus(null);
  };

  const handleDraftChange = (field: keyof TemplateDraft, value: string | boolean) => {
    if (!templateDraft) {
      return;
    }
    setTemplateDraft({
      ...templateDraft,
      [field]: value,
    });
  };

  const handleInstallmentChange = (index: number, field: keyof TemplateDraftInstallment, value: string) => {
    if (!templateDraft) {
      return;
    }
    setTemplateDraft((prev) => {
      if (!prev) {
        return prev;
      }
      const next = prev.installments.slice();
      next[index] = { ...next[index], [field]: value };
      return { ...prev, installments: next };
    });
  };

  const handleAddInstallment = () => {
    if (!templateDraft) {
      return;
    }
    setTemplateDraft({
      ...templateDraft,
      installments: [...templateDraft.installments, { period: '', amount: '' }],
    });
  };

  const handleRemoveInstallment = (index: number) => {
    if (!templateDraft) {
      return;
    }
    setTemplateDraft({
      ...templateDraft,
      installments: templateDraft.installments.filter((_, idx) => idx !== index),
    });
  };

  const buildInstallmentsPayload = (draft: TemplateDraft): PaymentPlanInstallmentInput[] => {
    if (draft.installments.length === 0) {
      throw new Error('Inclua ao menos uma parcela para o template.');
    }
    return draft.installments.map((item, index) => {
      const period = normalizeNumber(item.period, false);
      const amount = normalizeNumber(item.amount, false);
      if (period === null || amount === null || period <= 0 || amount <= 0) {
        throw new Error(`Valores inválidos na parcela ${index + 1}.`);
      }
      return { period, amount };
    });
  };

  const handleSaveTemplate = async () => {
    if (!accessToken || !selectedTenantId || !templateDraft) {
      return;
    }
    if (!templateDraft.productCode.trim()) {
      setError('Informe o código do produto.');
      return;
    }
    setTemplateSaving(true);
    setError(null);
    setTemplateStatus(null);
    try {
      const installments = buildInstallmentsPayload(templateDraft);
      const metadata = parseMetadata(templateDraft.metadataText);
      const basePayload: Omit<PaymentPlanTemplateCreatePayload, 'installments'> = {
        productCode: templateDraft.productCode.trim(),
        principal: normalizeNumber(templateDraft.principal, false),
        discountRate: normalizeNumber(templateDraft.discountRate, false),
        name: templateDraft.name.trim() || undefined,
        description: templateDraft.description.trim() || undefined,
        metadata,
        isActive: templateDraft.isActive,
      };

      if (!templateDraft.id) {
        const created = await createPaymentPlanTemplate(accessToken, selectedTenantId, {
          ...basePayload,
          installments,
        });
        setTemplates((prev) => [...prev, created]);
        setTemplateStatus('Template de plano criado com sucesso.');
        setTemplateDraft(asDraft(created));
      } else {
        const payload: PaymentPlanTemplateUpdatePayload = {
          name: templateDraft.name.trim() || undefined,
          description: templateDraft.description.trim() || null,
          principal: normalizeNumber(templateDraft.principal, false),
          discountRate: normalizeNumber(templateDraft.discountRate, false),
          metadata,
          isActive: templateDraft.isActive,
          installments,
        };
        const updated = await updatePaymentPlanTemplate(
          accessToken,
          selectedTenantId,
          templateDraft.id,
          payload,
        );
        setTemplates((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
        setTemplateStatus('Template de plano atualizado com sucesso.');
        setTemplateDraft(asDraft(updated));
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setTemplateSaving(false);
    }
  };

  return (
    <div className="stack">
      {canSelectTenant && (
        <div className="card stack">
          <h2>Selecione o tenant</h2>
          <div className="form-field">
            <label htmlFor="tenant-select">Tenant</label>
            <select
              id="tenant-select"
              value={selectedTenantId ?? ''}
              onChange={(event) => onSelectTenant(event.target.value)}
            >
              <option value="" disabled>
                Escolha um tenant
              </option>
              {tenants.map((tenant) => (
                <option key={tenant.id} value={tenant.id}>
                  {tenant.name} {tenant.isActive ? '' : '(inativo)'}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {error && (
        <div className="alert error">
          {error}
        </div>
      )}

      {!selectedTenantId ? (
        <div className="card">
          <p>Selecione um tenant para visualizar configurações e parâmetros.</p>
        </div>
      ) : (
        <>
          <section className="card stack">
            <div>
              <h2>Configurações financeiras</h2>
              {activeTenant && (
                <small>
                  Tenant: <strong>{activeTenant.name}</strong>
                </small>
              )}
            </div>
            {settingsLoading ? (
              <p>Carregando configurações...</p>
            ) : (
              <>
                <div className="grid two">
                  <div className="form-field">
                    <label htmlFor="periods-per-year">Períodos por ano</label>
                    <input
                      id="periods-per-year"
                      value={settingsForm.periodsPerYear}
                      onChange={(event) => handleSettingsChange('periodsPerYear', event.target.value)}
                      placeholder="Ex: 12"
                    />
                  </div>
                  <div className="form-field">
                    <label htmlFor="default-multiplier">Multiplicador de inadimplência</label>
                    <input
                      id="default-multiplier"
                      value={settingsForm.defaultMultiplier}
                      onChange={(event) => handleSettingsChange('defaultMultiplier', event.target.value)}
                      placeholder="Ex: 1.2"
                    />
                  </div>
                  <div className="form-field">
                    <label htmlFor="cancellation-multiplier">Multiplicador de cancelamento</label>
                    <input
                      id="cancellation-multiplier"
                      value={settingsForm.cancellationMultiplier}
                      onChange={(event) => handleSettingsChange('cancellationMultiplier', event.target.value)}
                      placeholder="Ex: 1.0"
                    />
                  </div>
                </div>
                <div>
                  <button
                    type="button"
                    className="button"
                    onClick={handleSaveSettings}
                    disabled={settingsSaving}
                  >
                    {settingsSaving ? 'Salvando...' : 'Salvar configurações'}
                  </button>
                  {settingsStatus && <small>{settingsStatus}</small>}
                </div>
              </>
            )}
          </section>

          <section className="card stack">
            <div className="stack">
              <h2>Templates de planos de pagamento</h2>
              {templateStatus && <small>{templateStatus}</small>}
              <div>
                <button type="button" className="button ghost" onClick={handleStartCreation}>
                  Novo template
                </button>
              </div>
            </div>

            {templatesLoading ? (
              <p>Carregando templates...</p>
            ) : templates.length === 0 ? (
              <p>Nenhum template cadastrado.</p>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Nome</th>
                    <th>Principal</th>
                    <th>Taxa de desconto</th>
                    <th>Parcelas</th>
                    <th>Status</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {templates.map((template) => (
                    <tr key={template.id}>
                      <td>{template.productCode}</td>
                      <td>{template.name ?? '-'}</td>
                      <td>{template.principal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                      <td>{template.discountRate.toLocaleString('pt-BR')}%</td>
                      <td>{template.installments.length}</td>
                      <td>
                        <span className="badge">{template.isActive ? 'Ativo' : 'Inativo'}</span>
                      </td>
                      <td>
                        <button
                          type="button"
                          className="button ghost"
                          onClick={() => handleEditTemplate(template)}
                        >
                          Editar
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {templateDraft && (
              <div className="card stack">
                <h3>{templateDraft.id ? 'Editar template' : 'Novo template'}</h3>
                <div className="grid two">
                  <div className="form-field">
                    <label htmlFor="template-product-code">Código do produto</label>
                    <input
                      id="template-product-code"
                      value={templateDraft.productCode}
                      onChange={(event) => handleDraftChange('productCode', event.target.value)}
                      disabled={!!templateDraft.id}
                    />
                  </div>
                  <div className="form-field">
                    <label htmlFor="template-name">Nome</label>
                    <input
                      id="template-name"
                      value={templateDraft.name}
                      onChange={(event) => handleDraftChange('name', event.target.value)}
                    />
                  </div>
                  <div className="form-field">
                    <label htmlFor="template-principal">Principal (valor)</label>
                    <input
                      id="template-principal"
                      value={templateDraft.principal}
                      onChange={(event) => handleDraftChange('principal', event.target.value)}
                      placeholder="Ex: 100000"
                    />
                  </div>
                  <div className="form-field">
                    <label htmlFor="template-discount-rate">Taxa de desconto (%)</label>
                    <input
                      id="template-discount-rate"
                      value={templateDraft.discountRate}
                      onChange={(event) => handleDraftChange('discountRate', event.target.value)}
                      placeholder="Ex: 1.5"
                    />
                  </div>
                </div>

                <div className="form-field">
                  <label htmlFor="template-description">Descrição</label>
                  <textarea
                    id="template-description"
                    rows={3}
                    value={templateDraft.description}
                    onChange={(event) => handleDraftChange('description', event.target.value)}
                  />
                </div>

                <div className="form-field">
                  <label htmlFor="template-metadata">Metadata (JSON)</label>
                  <textarea
                    id="template-metadata"
                    rows={4}
                    value={templateDraft.metadataText}
                    onChange={(event) => handleDraftChange('metadataText', event.target.value)}
                    placeholder='Ex: { "segment": "varejo" }'
                  />
                </div>

                <div className="form-field">
                  <label>
                    <input
                      type="checkbox"
                      checked={templateDraft.isActive}
                      onChange={(event) => handleDraftChange('isActive', event.target.checked)}
                    />
                    &nbsp;Template ativo
                  </label>
                </div>

                <div className="stack">
                  <h4>Parcelas</h4>
                  {templateDraft.installments.map((installment, index) => (
                    <div className="grid two" key={`${index}-${installment.period}-${installment.amount}`}>
                      <div className="form-field">
                        <label htmlFor={`installment-period-${index}`}>Período (mês)</label>
                        <input
                          id={`installment-period-${index}`}
                          value={installment.period}
                          onChange={(event) =>
                            handleInstallmentChange(index, 'period', event.target.value)
                          }
                          placeholder="Ex: 1"
                        />
                      </div>
                      <div className="form-field">
                        <label htmlFor={`installment-amount-${index}`}>Valor</label>
                        <input
                          id={`installment-amount-${index}`}
                          value={installment.amount}
                          onChange={(event) =>
                            handleInstallmentChange(index, 'amount', event.target.value)
                          }
                          placeholder="Ex: 1500"
                        />
                      </div>
                      <div>
                        <button
                          type="button"
                          className="button ghost"
                          onClick={() => handleRemoveInstallment(index)}
                          disabled={templateDraft.installments.length === 1}
                        >
                          Remover
                        </button>
                      </div>
                    </div>
                  ))}
                  <button type="button" className="button ghost" onClick={handleAddInstallment}>
                    Adicionar parcela
                  </button>
                </div>

                <div className="grid two">
                  <button
                    type="button"
                    className="button"
                    onClick={handleSaveTemplate}
                    disabled={templateSaving}
                  >
                    {templateSaving ? 'Salvando...' : 'Salvar template'}
                  </button>
                  <button type="button" className="button ghost" onClick={handleCancelTemplate}>
                    Cancelar
                  </button>
                </div>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
