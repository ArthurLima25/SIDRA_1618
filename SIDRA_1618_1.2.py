import pandas as pd
import sidrapy

# 1. Busca os dados mais recentes da Tabela 1618 para a Bahia (29)
data = sidrapy.get_table(
    table_code='1618',
    territorial_level='3',
    ibge_territorial_code='29',
    variable='109,35',  # 109 = Área plantada | 35 = Produção
    period='last',
    classifications={'49': 'all', '48': 'all'},
    header='n',
    format='list',
)

df = pd.DataFrame(data)

# 2. Filtra e renomeia colunas (no sidrapy: D2N = Mês, D3N = Variável)
df = df[['D2N', 'D3N', 'D4N', 'D5N', 'V']].rename(
    columns={
        'D2N': 'Mes_Divulgacao',
        'D3N': 'Variavel',
        'D4N': 'Ano_Safra',
        'D5N': 'Produto',
        'V': 'Valor',
    }
)

df['Ano_Safra'] = df['Ano_Safra'].str.replace('Safra ', '', regex=False).str.strip()
df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')

# Descobre dinamicamente os dois anos ativos na tabela (ex: ['2025', '2026'])
anos = sorted(df['Ano_Safra'].dropna().unique())
ano1, ano2 = anos[0], anos[1]

# 3. Pivota a tabela colocando tudo na mesma linha por Produto
df_final = df.pivot(
    index=['Mes_Divulgacao', 'Produto'],
    columns=['Variavel', 'Ano_Safra'],
    values='Valor',
)

df_final.columns = [f'{var}_{ano}' for var, ano in df_final.columns]
df_final = df_final.reset_index()

# 4. Calcula os Deltas antes de zerar os NaN
df_final['Delta_Area_Plantada'] = (
    df_final[f'Área plantada_{ano2}'] / df_final[f'Área plantada_{ano1}']
)
df_final['Delta_Producao'] = (
    df_final[f'Produção_{ano2}'] / df_final[f'Produção_{ano1}']
)

# 5. Substitui NaN e infinitos (divisão por zero) por 0
df_final = df_final.replace([float('inf'), float('-inf')], 0).fillna(0)

# 6. Ordenação numérica pelo prefixo do produto (1.1, ..., 4, ..., 10)
nums = df_final['Produto'].str.extract(r'^(\d+)(?:\.(\d+))?')
df_final['ord_1'] = pd.to_numeric(nums[0]).fillna(999999)
df_final['ord_2'] = pd.to_numeric(nums[1]).fillna(0)

df_final = (
    df_final.sort_values(['ord_1', 'ord_2'])
    .drop(columns=['ord_1', 'ord_2'])
    .reset_index(drop=True)
)

# 7. Organiza a ordem final das colunas
colunas_ordenadas = [
    'Mes_Divulgacao',
    'Produto',
    f'Área plantada_{ano1}',
    f'Área plantada_{ano2}',
    'Delta_Area_Plantada',
    f'Produção_{ano1}',
    f'Produção_{ano2}',
    'Delta_Producao',
]
df_final = df_final[colunas_ordenadas]

# 8. Exporta para Excel
df_final.to_excel('SIDRA_bahia_1618.xlsx', index=False, sheet_name='Bahia_1618')
df_final.to_csv('SIDRA_bahia_1618.csv', index=False, sep=';', decimal=',')
print('Planilha SIDRA_bahia_1618.xlsx gerada com sucesso!')


