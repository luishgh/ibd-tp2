import io
import os
import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import warnings

st.title('Trabalho Prático 2')

st.markdown('# Conjunto de dados: Pontos de Abastecimento Autorizado')
st.markdown('Link: https://dados.gov.br/dados/conjuntos-dados/pontos-de-abastecimento-autorizados')

# Import database
try:
    os.remove('/tmp/consult.db')
except OSError:
    pass

conn = sqlite3.connect('/tmp/consult.db')
cursor = conn.cursor()

f = io.open('./dump.sql', 'r', encoding='utf-8')
sql = f.read()
cursor.executescript(sql)

st.markdown('## Consultas')

st.markdown('### Instalações em Belo Horizonte ordenadas pelo volume de sua tancagem (de qualquer combustivel) em ordem decrescente')

# Seleção e Projeção
# Instalações em Belo Horizonte ordenadas pelo volume de sua tancagem (de qualquer combustivel) em ordem decrescente
df = pd.read_sql_query('''
  SELECT DISTINCT TANCAGEM, COD_INSTALACAO, NOM_INSTALACAO, DSC_ENDERECO, NUM_ENDERECO, CEP
  FROM INSTALACAO NATURAL JOIN LOCALIDADE
  NATURAL JOIN INSTALACAO_COMBUSTIVEL
  WHERE MUNICIPIO LIKE 'Belo Horizonte'
  ORDER BY TANCAGEM DESC
''', conn)

df

st.markdown('### Numero de Instalações em Minas Gerais de cada tipo de combustivel')

# Seleção e Projeção
# Numero de Instalações em Minas Gerais de cada tipo de combustivel
df = pd.read_sql_query('''
  SELECT COMBUSTIVEL, NUM_INSTALACOES
  FROM (SELECT COD_COMBUSTIVEL, COUNT(COD_COMBUSTIVEL) NUM_INSTALACOES
  FROM COMBUSTIVEL
  NATURAL JOIN INSTALACAO_COMBUSTIVEL
  NATURAL JOIN INSTALACAO
  NATURAL JOIN LOCALIDADE
  WHERE UF = 'MG'
  GROUP BY COD_COMBUSTIVEL) MG_COMB_TOT
  NATURAL JOIN COMBUSTIVEL
  ORDER BY NUM_INSTALACOES DESC
''', conn)

df

st.markdown('### Quais tipos de combustivel nao são produzidos em MG?')

# Seleção e Projeção
# Quais tipos de combustivel nao são produzidos em MG?
df = pd.read_sql_query('''
  SELECT COMBUSTIVEL
  FROM (SELECT COD_COMBUSTIVEL
  FROM COMBUSTIVEL
  NATURAL JOIN INSTALACAO_COMBUSTIVEL
  NATURAL JOIN INSTALACAO
  NATURAL JOIN LOCALIDADE
  GROUP BY COD_COMBUSTIVEL)
  NATURAL JOIN COMBUSTIVEL

  EXCEPT

  SELECT COMBUSTIVEL
  FROM (SELECT COD_COMBUSTIVEL
  FROM COMBUSTIVEL
  NATURAL JOIN INSTALACAO_COMBUSTIVEL
  NATURAL JOIN INSTALACAO
  NATURAL JOIN LOCALIDADE
  WHERE UF = 'MG' /*AND MUNICIPIO <> 'BELO HORIZONTE'*/
  GROUP BY COD_COMBUSTIVEL) MG_COMB_TOT
  NATURAL JOIN COMBUSTIVEL
''', conn)

df

st.markdown('### Ranqueamento de todos os estados pelo número de instalações')

# Junção de duas relações;
# Ranqueamento de todos os estados pelo número de instalações
df = pd.read_sql_query('''
  SELECT UF, COUNT(*) AS NUM_INSTALACOES
  FROM INSTALACAO
  NATURAL JOIN LOCALIDADE
  GROUP BY UF
  ORDER BY NUM_INSTALACOES DESC
''', conn)

df
st.bar_chart(df, x='UF', y='NUM_INSTALACOES')

st.markdown('### Instalações que oferecem combustivel de aviação e jato')

# Junção de duas relações
# Instalações que oferecem combustivel de aviação e jato
df = pd.read_sql_query('''
  SELECT I.NOM_INSTALACAO
  FROM INSTALACAO I
  NATURAL JOIN INSTALACAO_COMBUSTIVEL IC
  WHERE COD_COMBUSTIVEL IN (
    SELECT COD_COMBUSTIVEL
    FROM COMBUSTIVEL
    WHERE CLASSE IN ('Aviacao', 'Jato')
  )
''', conn)
df

st.markdown('### Rankeamento de orgãos emissores pelo numero de licencas concedidas, desconsiderando as ausentes e isentas')

# Junção de duas relações
# Rankeamento de orgãos emissores pelo numero de licencas concedidas, desconsiderando as ausentes e isentas
df = pd.read_sql_query('''
  SELECT EMISSOR, COUNT(*) as LICENÇAS
  FROM LICENCA
  NATURAL JOIN INSTALACAO_LICENCA
  WHERE LICENCA <> 'ISENTO' and LICENCA <> 'AUSENTE'
  GROUP BY EMISSOR
  ORDER BY LICENÇAS DESC
''', conn)
df
st.bar_chart(df, x='EMISSOR', y='LICENÇAS')

st.markdown('### Engenheiros que mais trabalharam isentos de licença e a instação em questão (na query seguinte)')

# Junção de três ou mais relações
# Engenheiros que mais trabalharam isentos de licença e a instação em questão (na query seguinte)
df = pd.read_sql_query('''
  SELECT DISTINCT ENGENHEIRO, COUNT(NOM_INSTALACAO) NUM_INSTALACOES
  FROM ENGENHEIRO
  NATURAL JOIN INSTALACAO
  NATURAL JOIN INSTALACAO_LICENCA
  NATURAL JOIN LICENCA
  WHERE COD_LICENCA IN
  (SELECT DISTINCT COD_LICENCA
  FROM LICENCA
  WHERE LICENCA = 'ISENTO')
  GROUP BY ENGENHEIRO
  ORDER BY NUM_INSTALACOES DESC
''', conn)
df
st.bar_chart(df, x='ENGENHEIRO', y='NUM_INSTALACOES')

st.markdown('- Quais são essas instalações? São de qual UF?')

# Junção de três relações
# Quais são essas instalações? São de qual UF?
df = pd.read_sql_query('''
  SELECT DISTINCT ENGENHEIRO, NOM_INSTALACAO, UF
  FROM ENGENHEIRO
  NATURAL JOIN INSTALACAO
  NATURAL JOIN INSTALACAO_LICENCA
  NATURAL JOIN LICENCA
  NATURAL JOIN LOCALIDADE
  WHERE COD_LICENCA IN
  (SELECT DISTINCT COD_LICENCA
  FROM LICENCA
  WHERE LICENCA = 'ISENTO')
''', conn)
df

st.markdown('### UFs e o numero de instalacoes isentas de licenca ou com licenca ausente')

# Junção de três ou mais relações
# UFs e o numero de instalacoes isentas de licenca ou com licenca ausente
df = pd.read_sql_query('''
  SELECT UF, LICENCA, COUNT(*) NUM_LICENCAS
  FROM INSTALACAO
  NATURAL JOIN INSTALACAO_LICENCA
  NATURAL JOIN LOCALIDADE
  NATURAL JOIN LICENCA
  WHERE COD_LICENCA IN
  (SELECT DISTINCT COD_LICENCA
  FROM LICENCA
  WHERE LICENCA = 'ISENTO' OR LICENCA = 'AUSENTE')
  GROUP BY UF, LICENCA
''', conn)
df

st.markdown('### Quais são os 5 cobustiveis com menos instalações dedicadas?')

# Junção de 3 ou mais relações
# Quais são os 5 cobustiveis com menos instalações dedicadas? Quais UFs sediam a maior parte de suas instalações?
df = pd.read_sql_query('''
  SELECT COMBUSTIVEL, UF, INSTS_PRESENTE
  FROM (
    SELECT COMBUSTIVEL, UF, COUNT(*) INSTS_PRESENTE
    FROM INSTALACAO_COMBUSTIVEL IC
    NATURAL JOIN (
      SELECT COD_COMBUSTIVEL, COUNT(COD_COMBUSTIVEL) NUM_INSTALACOES
      FROM INSTALACAO
      NATURAL JOIN INSTALACAO_COMBUSTIVEL
      NATURAL JOIN COMBUSTIVEL
      GROUP BY COD_COMBUSTIVEL
      ORDER BY NUM_INSTALACOES
      LIMIT 5
    ) COMBS_MENOS_COMUNS
    NATURAL JOIN INSTALACAO
    NATURAL JOIN COMBUSTIVEL
    NATURAL JOIN LOCALIDADE
    GROUP BY COMBUSTIVEL, UF
  ) UF_COMB_COUNT
  ORDER BY INSTS_PRESENTE
''', conn)
df

st.markdown('  - Quais UFs sediam a maior parte de suas instalações?')

dict = {}
for fuel_type in df['COMBUSTIVEL'].unique()[::-1]:
    curr_df = df[df['COMBUSTIVEL'] == fuel_type]
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.barh(curr_df['UF'], curr_df['INSTS_PRESENTE'], color='skyblue')
    ax.xaxis.set_major_locator(MaxNLocator(integer=True)) # deixar o eixo X apenas com inteiros

    # Configurar plot
    plt.xlabel('Número de Ocorrências')
    plt.ylabel('UF')
    plt.title('Distribuição de Ocorrências por UF para ' + curr_df['COMBUSTIVEL'].iloc[0], fontsize=8)
    st.pyplot(plt)
    # st.bar_chart(curr_df, y='INSTS_PRESENTE', x='UF')
    print(end='\n')

    # Salva UF com maior num de ocorrencias
    idx_max = curr_df.INSTS_PRESENTE.argmax()
    dict[fuel_type] = [curr_df.iloc[idx_max]['UF'], curr_df.iloc[idx_max]['INSTS_PRESENTE']]

st.markdown('  - Para cada tipo, qual é a UF com mais postos?')
# Para cada tipo, qual é a UF com mais postos?
df = pd.DataFrame(dict).T.rename(columns={0: 'UF', 1: 'NumInstalacoes'})
df

st.markdown('### Engenheiros se especializam em projetos de apenas um tipo de combustivel?')

# Agregação sobre junção de duas ou mais relações
# Engenheiros se especializam em projetos de apenas um tipo de combustivel?
df = pd.read_sql_query('''
  SELECT ENGENHEIRO, COMBUSTIVEL, NUM_PROJETOS_POR_COMBUSTIVEL
  FROM (
    SELECT E.ENGENHEIRO, IC.COD_COMBUSTIVEL, COUNT(IC.COD_COMBUSTIVEL) NUM_PROJETOS_POR_COMBUSTIVEL
    FROM INSTALACAO I
    NATURAL JOIN ENGENHEIRO E
    NATURAL JOIN INSTALACAO_COMBUSTIVEL IC
    GROUP BY E.ENGENHEIRO, IC.COD_COMBUSTIVEL
  ) ENG_PROJ_COMB
  NATURAL JOIN COMBUSTIVEL
  ORDER BY ENGENHEIRO DESC, NUM_PROJETOS_POR_COMBUSTIVEL DESC
''', conn)
df

mask_combs_diferentes = df.ENGENHEIRO.duplicated(keep=False)

# Engenheiros em projetos de diferentes tipos de combustivel
engs_mult_combs = df.loc[mask_combs_diferentes]
engs_mult_combs = engs_mult_combs.merge(engs_mult_combs.groupby('ENGENHEIRO').NUM_PROJETOS_POR_COMBUSTIVEL.sum(), \
                      left_on = 'ENGENHEIRO',right_on='ENGENHEIRO')
engs_mult_combs['%PROJ_COMB'] = engs_mult_combs.NUM_PROJETOS_POR_COMBUSTIVEL_x / engs_mult_combs.NUM_PROJETOS_POR_COMBUSTIVEL_y
engs_mult_combs = engs_mult_combs.groupby('ENGENHEIRO')[['%PROJ_COMB', 'COMBUSTIVEL']].first()

# Engenheiros em projetos de um unico tipo de combustivel
engs_unico_comb = df.loc[~mask_combs_diferentes]

st.markdown('#### Qual é a proporção dos engenheiros que se especializam em único tipo de combustivel para seus projetos?')
# Qual é a proporção dos engenheiros que se especializam em único tipo de combustivel para seus projetos?
st.write('    - Número de engenheiros em projetos de diferentes tipos de combustivel: ', engs_mult_combs.shape[0])
st.write('    - Número de engenheiros em projetos de um único tipo de combustivel: ', engs_unico_comb.shape[0])
st.write(f'    - Proporção entre eles: __{100*(engs_mult_combs.shape[0]/engs_unico_comb.shape[0]):.2f}%__')

st.markdown('#### Dentre os engenheiros que trabalham com projetos com diferentes combustiveis qual é o combustivel mais presente nos projetos?')

# Dentre os engenheiros que trabalham com projetos com diferentes combustiveis qual é o combustivel mais presente nos projetos?
plt.subplots(figsize=(20, 15))
plt.hist(engs_mult_combs.COMBUSTIVEL, color='skyblue',orientation='horizontal',edgecolor = "blue")
plt.xlabel('Engenheiro')
plt.title('Combustivel mais presente em projetos de engenheiros que trabalham com projetos com diferentes combustiveis')
st.pyplot(plt)

st.markdown('#### Dentre os engenheiros que trabalham com unico tipo de combustivel, quais são os mais presentes?')

# Dentre os engenheiros que trabalham com unico tipo de combustivel, quais são os mais presentes?
plt.subplots(figsize=(20, 15))
plt.hist(engs_unico_comb.COMBUSTIVEL, color='skyblue',orientation='horizontal', edgecolor = "blue")
plt.xlabel('Engenheiro')
plt.title('Combustivel mais presente em projetos de engenheiros que trabalham com único tipo de combustivel')
st.pyplot(plt)

tot_comb = pd.read_sql_query('''
  SELECT COMBUSTIVEL, NUM_INSTALACOES
  FROM (SELECT COD_COMBUSTIVEL, COUNT(COD_COMBUSTIVEL) NUM_INSTALACOES
  FROM COMBUSTIVEL
  NATURAL JOIN INSTALACAO_COMBUSTIVEL
  NATURAL JOIN INSTALACAO
  NATURAL JOIN LOCALIDADE
  GROUP BY COD_COMBUSTIVEL)
  NATURAL JOIN COMBUSTIVEL
''', conn)

st.markdown('#### Combustiveis mais presentes em instalações')

# Combustiveis mais presentes em instalações
plt.subplots(figsize=(20, 15))
plt.hist(df.COMBUSTIVEL, color='skyblue',orientation='horizontal', edgecolor = "blue")
plt.xlabel('Engenheiro')
plt.title('Numero de instalações com cada tipo de combustivel')
st.pyplot(plt)

st.write("""
Notamos que engenheiros especializados, no geral, trabalham com instalações que produzem óleo diesel de diferentes tipos, ao passo que engenheiros mais generalistas, apesar de também trabalharem com óleo diesel, também estão bastante presentes em projetos com Gasolina Comum, o que seria esperado pelo senso comum.

É possível perceber que a maior parte dos engenheiros trabalham com projetos de um único tipo de combustível, o que é um indicativo de que a especialização desse tipo de profissional é comum. E faz sentido que os tipos de combustivel mais presente em instalações de maneira geral sejam aqueles com os quais a maior parte dos engenheiros trabalha.
""")

st.markdown('### Percentual produzido de cada combustivel em relação à produção total de cada estado')

st.markdown("""**Tancagem**: é o volume total que pode ser armazenado nas unidades,
cadastrado como capacidade operacional pela ANP. A
quantidade é arredondada para o número inteiro mais
próximo.""")

# Agregação sobre junção de duas ou mais relações
# Percentual produzido de cada combustivel em relação à produção total de cada estado
aux = pd.read_sql_query('''
  WITH COMB_UF AS (
      SELECT COD_COMBUSTIVEL, L.UF, TANCAGEM
    FROM INSTALACAO I
    NATURAL JOIN LOCALIDADE L
    NATURAL JOIN INSTALACAO_COMBUSTIVEL IC
    NATURAL JOIN COMBUSTIVEL C
    ORDER BY L.UF
  )

  SELECT UF, COMBUSTIVEL, TANCAGEM_COMB_UF / TANCAGEM_TOT_UF '%TANCAGEM'
  FROM (
    SELECT UF, COD_COMBUSTIVEL, SUM(TANCAGEM) TANCAGEM_COMB_UF, TANCAGEM_TOT_UF
    FROM COMB_UF
    NATURAL JOIN (
      SELECT UF, SUM(TANCAGEM) TANCAGEM_TOT_UF
      FROM COMB_UF
      GROUP BY UF
  ) UF_TOT
  GROUP BY UF, COD_COMBUSTIVEL) TANCAGEM_UF_COMB
  NATURAL JOIN COMBUSTIVEL
  ORDER BY UF, '%TANCAGEM' DESC

''', conn)
aux

st.markdown('#### Qual tipo de combustivel é o majoritario em cada estado?')

# Qual tipo de combustivel é o majoritario em cada estado?
st.write(aux.groupby('UF')[['%TANCAGEM', 'COMBUSTIVEL']].first())

st.markdown('#### E qual tipo de combustivel é o "menos produzido" em cada estado?')

# E qual tipo de combustivel é o "menos produzido" em cada estado?
st.write(aux.groupby('UF')[['%TANCAGEM', 'COMBUSTIVEL']].last())