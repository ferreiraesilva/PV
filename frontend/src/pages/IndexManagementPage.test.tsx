import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import IndexManagementPage from './IndexManagementPage';
import * as AuthHook from '../hooks/useAuth';
import * as IndexAPI from '../api/financial_index';

vi.mock('../hooks/useAuth');
vi.mock('../api/financial_index');

const mockUser = (roles: string[]) => {
  vi.spyOn(AuthHook, 'useAuth').mockReturnValue({
    tenantId: 'test-tenant',
    accessToken: 'test-token',
    user: { email: 'test@example.com', roles },
    login: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
  });
};

describe('IndexManagementPage', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.spyOn(IndexAPI, 'createIndexValues').mockResolvedValue([]);
    vi.spyOn(IndexAPI, 'listIndexValues').mockResolvedValue([]);
  });

  it('não deve renderizar o formulário de upload para usuários sem permissão', () => {
    mockUser(['user']); // Usuário comum
    render(<IndexManagementPage />);

    expect(
      screen.queryByText('Cadastrar/Atualizar via CSV')
    ).not.toBeInTheDocument();
  });

  it('deve renderizar o formulário de upload para tenant_admin', () => {
    mockUser(['tenant_admin']);
    render(<IndexManagementPage />);

    expect(screen.getByText('Cadastrar/Atualizar via CSV')).toBeInTheDocument();
  });

  it('deve exibir um erro ao tentar fazer upload sem um arquivo', async () => {
    mockUser(['tenant_admin']);
    render(<IndexManagementPage />);

    const uploadButton = screen.getByRole('button', {
      name: /Enviar Arquivo/i,
    });
    fireEvent.click(uploadButton);

    expect(
      await screen.findByText('Por favor, selecione um arquivo CSV.')
    ).toBeInTheDocument();
    expect(IndexAPI.createIndexValues).not.toHaveBeenCalled();
  });

  it('deve exibir um erro para CSV com cabeçalho inválido', async () => {
    mockUser(['tenant_admin']);
    render(<IndexManagementPage />);

    const invalidCsvContent = 'data,valor\n2024-01-01,1.05';
    const file = new File([invalidCsvContent], 'test.csv', {
      type: 'text/csv',
    });

    const fileInput = screen.getByLabelText<HTMLInputElement>(/Arquivo CSV/i);
    fireEvent.change(fileInput, { target: { files: [file] } });

    const uploadButton = screen.getByRole('button', {
      name: /Enviar Arquivo/i,
    });
    fireEvent.click(uploadButton);

    expect(
      await screen.findByText(
        'O cabeçalho do CSV deve conter as colunas "reference_date" e "value".'
      )
    ).toBeInTheDocument();
    expect(IndexAPI.createIndexValues).not.toHaveBeenCalled();
  });

  it('deve exibir um erro para CSV com linha de dados inválida', async () => {
    mockUser(['tenant_admin']);
    render(<IndexManagementPage />);

    const invalidCsvContent = 'reference_date,value\n2024-01-01,abc'; // 'abc' não é um número
    const file = new File([invalidCsvContent], 'test.csv', {
      type: 'text/csv',
    });

    const fileInput = screen.getByLabelText<HTMLInputElement>(/Arquivo CSV/i);
    fireEvent.change(fileInput, { target: { files: [file] } });

    const uploadButton = screen.getByRole('button', {
      name: /Enviar Arquivo/i,
    });
    fireEvent.click(uploadButton);

    expect(
      await screen.findByText(
        'Erro na linha 2: formato de data ou valor inválido.'
      )
    ).toBeInTheDocument();
    expect(IndexAPI.createIndexValues).not.toHaveBeenCalled();
  });

  it('deve fazer o parse do CSV e chamar a API com os dados corretos', async () => {
    mockUser(['tenant_admin']);
    const createIndexValuesSpy = vi.spyOn(IndexAPI, 'createIndexValues');
    // Mock do window.alert
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});

    render(<IndexManagementPage />);

    const validCsvContent =
      'reference_date,value\n2024-01-01,1.005\n2024-02-01,1.0045\n';
    const file = new File([validCsvContent], 'test.csv', { type: 'text/csv' });

    const fileInput = screen.getByLabelText<HTMLInputElement>(/Arquivo CSV/i);
    fireEvent.change(fileInput, { target: { files: [file] } });

    const uploadButton = screen.getByRole('button', {
      name: /Enviar Arquivo/i,
    });
    fireEvent.click(uploadButton);

    await waitFor(() => {
      expect(createIndexValuesSpy).toHaveBeenCalledTimes(1);
    });

    // Verifica se a API foi chamada com o payload correto
    expect(createIndexValuesSpy).toHaveBeenCalledWith(
      'test-tenant',
      'test-token',
      'INCC-CUSTOM',
      {
        values: [
          { reference_date: '2024-01-01', value: 1.005 },
          { reference_date: '2024-02-01', value: 1.0045 },
        ],
      }
    );

    // Verifica se o alerta de sucesso foi exibido
    expect(alertSpy).toHaveBeenCalledWith(
      'Valores do índice enviados com sucesso! Clique em "Buscar Valores" para ver a lista atualizada.'
    );

    alertSpy.mockRestore();
  });
});
