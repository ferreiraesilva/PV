import { FormEvent, useState, ChangeEvent } from 'react';
import { PageHeader } from '../components/PageHeader';
import { useAuth } from '../hooks/useAuth';
import { createIndexValues, listIndexValues } from '../api/financial_index';
import type { IndexValueOutput } from '../api/types';

export default function IndexManagementPage() {
  const { tenantId, accessToken, user } = useAuth();
  const [indexCode, setIndexCode] = useState('INCC-CUSTOM');
  const [values, setValues] = useState<IndexValueOutput[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canManage =
    user?.roles.includes('tenant_admin') || user?.roles.includes('superuser');

  const handleFetch = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (!tenantId || !accessToken) {
        throw new Error('Usuário não autenticado.');
      }
      const response = await listIndexValues(tenantId, accessToken, indexCode);
      setValues(response);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setFile(event.target.files[0]);
    }
  };

  const handleUpload = async (event: FormEvent) => {
    event.preventDefault();
    if (!file) {
      setError('Por favor, selecione um arquivo CSV.');
      return;
    }
    if (!tenantId || !accessToken) {
      setError('Usuário não autenticado.');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const fileContent = await file.text();
      const lines = fileContent
        .split(/\r?\n/)
        .filter((line) => line.trim() !== '');
      if (lines.length < 2) {
        throw new Error(
          'O arquivo CSV deve conter um cabeçalho e pelo menos uma linha de dados.'
        );
      }

      const headers = lines[0].split(',').map((h) => h.trim().toLowerCase());
      const dateIndex = headers.indexOf('reference_date');
      const valueIndex = headers.indexOf('value');

      if (dateIndex === -1 || valueIndex === -1) {
        throw new Error(
          'O cabeçalho do CSV deve conter as colunas "reference_date" e "value".'
        );
      }

      const parsedValues = lines.slice(1).map((line, i) => {
        const columns = line.split(',');
        const reference_date = columns[dateIndex]?.trim();
        const value = parseFloat(columns[valueIndex]?.trim());

        if (!reference_date || isNaN(value)) {
          throw new Error(
            `Erro na linha ${i + 2}: formato de data ou valor inválido.`
          );
        }
        return { reference_date, value };
      });

      await createIndexValues(tenantId, accessToken, indexCode, {
        values: parsedValues,
      });
      alert(
        'Valores do índice enviados com sucesso! Clique em "Buscar Valores" para ver a lista atualizada.'
      );
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setUploading(false);
    }
  };

  if (!tenantId || !accessToken) {
    return (
      <div className="card">
        <p>Autentique-se para gerenciar índices.</p>
      </div>
    );
  }

  return (
    <div className="stack">
      <PageHeader
        title="Gestão de Índices Financeiros"
        subtitle="Cadastre e consulte os valores de índices customizados para seu tenant."
      />

      <div className="grid two">
        <form className="card stack" onSubmit={handleFetch}>
          <h3>Consultar Índice</h3>
          <div className="form-field">
            <label htmlFor="indexCode">Código do Índice</label>
            <input
              id="indexCode"
              value={indexCode}
              onChange={(e) => setIndexCode(e.target.value)}
              placeholder="Ex: INCC-CUSTOM"
            />
          </div>
          <div className="form-actions">
            <button type="submit" className="button" disabled={loading}>
              {loading ? 'Buscando...' : 'Buscar Valores'}
            </button>
          </div>
        </form>

        {canManage && (
          <form className="card stack" onSubmit={handleUpload}>
            <h3>Cadastrar/Atualizar via CSV</h3>
            <div className="form-field">
              <label htmlFor="csvFile">Arquivo CSV</label>
              <input
                id="csvFile"
                type="file"
                accept=".csv"
                onChange={handleFileChange}
              />
              <small>
                O arquivo deve ter as colunas: <code>reference_date,value</code>
                .
              </small>
            </div>
            <div className="form-actions">
              <button type="submit" className="button" disabled={uploading}>
                {uploading ? 'Enviando...' : 'Enviar Arquivo'}
              </button>
            </div>
          </form>
        )}
      </div>

      {error && <div className="alert error">{error}</div>}

      {values.length > 0 && (
        <div className="card">
          <h3>Valores para {indexCode}</h3>
          <table className="table">
            <thead>
              <tr>
                <th>Data de Referência</th>
                <th>Valor</th>
                <th>Última Atualização</th>
              </tr>
            </thead>
            <tbody>
              {values.map((v, i) => (
                <tr key={i}>
                  <td>{new Date(v.reference_date).toLocaleDateString()}</td>
                  <td>{v.value.toFixed(5)}</td>
                  <td>{new Date(v.updated_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
