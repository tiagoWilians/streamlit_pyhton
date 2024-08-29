import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import cx_Oracle
import time
import psycopg2
from time import strftime
from datetime import datetime as dt
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
import os


# Configuração da conexão com o banco de dados PostgreSQL
dbname = os.getenv('dbname')
user = os.getenv('user')
password = os.getenv('password')
host = 'PTIARA01NB033'
port = 5432


# Configuração da página
st.set_page_config(page_title="Produção Online", layout='wide', page_icon=":herb:")

#image_path_aralco = r'C:\Users\twoliveira\Desktop\App planilha online\assets\ARALCO.png'

# Carrega o CSS customizado
if os.path.exists("styles.css"):
    with open("styles.css") as file:
        st.markdown(f"<style>{file.read()}</style>", unsafe_allow_html=True)

#Carrega a Sidebar
with st.sidebar:
    #st.sidebar.image(width=200, use_column_width=False)
   ""
    
    

#Querys
query_entrada_cana = "select * from po_entrada_cana"

query_fato_entrada_cana = "select * from fato_entrada_cana where datamovimento = CURRENT_DATE"

query_entrada_cana_ultimos_15_dias = '''SELECT * 
FROM fato_entrada_cana
WHERE datamovimento >= CURRENT_DATE - INTERVAL '15' DAY 
  AND datamovimento < CURRENT_DATE'''

query_estoque_patio = "select * from po_estoque_patio"

#Data atual
data_atual = dt.now()
data_atual = data_atual.strftime("%d/%m/%Y")


def load_data_post(query):
    try:
        conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        cur = conn.cursor()
        query_entrada_cana = query
        cur.execute(query_entrada_cana)
        colnames = [desc[0] for desc in cur.description]
        resultado = cur.fetchall()
        df = pd.DataFrame(resultado, columns=colnames)
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        df = pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro
    return df


st.markdown('<div class="custom-header"><h1>PRODUÇÃO ONLINE</h1></div>', unsafe_allow_html=True)
col1_a,col2_a = st.columns([1.2,10])
with col1_a:
    periodo = st.selectbox(options=["Dia","Semana","Mês","Safra"],
            label="Período",
            placeholder="Selecione o Período")
with col2_a:
    ""

# Placeholder para a tabela
placeholder = st.empty()



# Loop para atualização contínua
while True:
    
    placeholder.empty()
    # Exibe os dados no dashboard
    with placeholder.container():
         # Carregar os dados
        
        
        
        #Carrega as Querys
        df_estoque_patio = load_data_post(query_estoque_patio)
        df_entrada_cana = load_data_post(query_entrada_cana)
        df_fato_entrada_cana = load_data_post(query_fato_entrada_cana)
        

        df_entrada_cana['Grupo'] = df_entrada_cana[['alcoazul', 'generalco', 'figueira']].fillna(0).sum(axis=1)

        df_fato_entrada_cana['unidade'] = df_fato_entrada_cana['cod_grupoempresa'].astype(str) + '-' + \
                                    df_fato_entrada_cana['cod_empresa'].astype(str) + '-' + \
                                    df_fato_entrada_cana['cod_filial'].astype(str)

        # Mapeie as combinações para os nomes das unidades
        unidade_map = {
            '1-7-1': 'Figueira',
            '1-7-2': 'Alcoazul',
            '1-3-1': 'Generalco'
        }
        df_fato_entrada_cana['unidade'] = df_fato_entrada_cana['unidade'].map(unidade_map)

        # Converter a coluna 'horasaida' para datetime se ainda não estiver
        df_fato_entrada_cana['horasaida'] = pd.to_datetime(df_fato_entrada_cana['horasaida'], format='%H:%M')

        # Extrair a hora no formato HH:MM
        df_fato_entrada_cana['hora'] = df_fato_entrada_cana['horasaida'].dt.strftime('%H:00')

        # Agrupar por 'unidade' e 'hora', somando os valores de 'pesoliquido'
        df_fato_entrada_cana_grafico = df_fato_entrada_cana.groupby(['unidade', 'hora'])['pesoliquido'].sum().reset_index()

        # Criar uma série com todas as horas do dia
        horas_dia = pd.Series(pd.date_range('00:00', '23:00', freq='H').strftime('%H:00'))

        # Expandir para todas as unidades
        unidades = ['Figueira', 'Alcoazul', 'Generalco']

        # Criar um DataFrame com todas as combinações de unidade e hora
        horas_dia_unidades = pd.MultiIndex.from_product([unidades, horas_dia], names=['unidade', 'hora']).to_frame(index=False)

        # Fazer o merge com o DataFrame agrupado
        df_entrada_cana_hora = pd.merge(horas_dia_unidades, df_fato_entrada_cana_grafico, on=['unidade', 'hora'], how='left')

        # Preencher valores NaN com 0
        df_entrada_cana_hora['pesoliquido'] = df_entrada_cana_hora['pesoliquido'].fillna(0)


       
        st.markdown(f'<div class="custom-header2"><h3>Moagem (ton) - {periodo}</h3></div>', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if periodo =='Dia':
                var_teste = f'{df_entrada_cana["alcoazul"].iloc[0]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
            elif periodo=='Semana':
                var_teste = f'{df_entrada_cana["alcoazul"].iloc[1]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
            elif periodo=='Mês':
                var_teste = f'{df_entrada_cana["alcoazul"].iloc[2]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
            elif periodo=='Safra':
                var_teste = f'{df_entrada_cana["alcoazul"].iloc[3]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
            st.markdown(f'''
            <div class="card-box">
                <h2>ALCOAZUL</h2>
                <h3>{var_teste}</h3> 
            </div>
            ''', unsafe_allow_html=True)

        with col2:
            if periodo =='Dia':
                var_teste = f'{df_entrada_cana["generalco"].iloc[0]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
            elif periodo=='Semana':
                var_teste = f'{df_entrada_cana["generalco"].iloc[1]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
            elif periodo=='Mês':
                var_teste = f'{df_entrada_cana["generalco"].iloc[2]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
            elif periodo=='Safra':
                var_teste = f'{df_entrada_cana["generalco"].iloc[3]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
            st.markdown(f'''
            <div class="card-box">
                <h2>GENERALCO</h2>
                <h3>{var_teste}</h3> 
            </div>
            ''', unsafe_allow_html=True)

        with col3:
            if periodo =='Dia':
                var_teste = f'{df_entrada_cana["figueira"].iloc[0]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
            elif periodo=='Semana':
                var_teste = f'{df_entrada_cana["figueira"].iloc[1]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
            elif periodo=='Mês':
                var_teste = f'{df_entrada_cana["figueira"].iloc[2]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
            elif periodo=='Safra':
                var_teste = f'{df_entrada_cana["figueira"].iloc[3]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
            st.markdown(f'''
            <div class="card-box">
                <h2>FIGUEIRA</h2>
                <h3>{var_teste}</h3> 
            </div>
            ''', unsafe_allow_html=True)

        with col4:
            if periodo =='Dia':
                var_teste = f'{df_entrada_cana["Grupo"].iloc[0]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
            elif periodo=='Semana':
                var_teste = f'{df_entrada_cana["Grupo"].iloc[1]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
            elif periodo=='Mês':
                var_teste = f'{df_entrada_cana["Grupo"].iloc[2]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
            elif periodo=='Safra':
                var_teste = f'{df_entrada_cana["Grupo"].iloc[3]:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".")
            st.markdown(f'''
            <div class="card-box">
                <h2>GRUPO</h2>
                <h3>{var_teste}</h3> 
            </div>
            ''', unsafe_allow_html=True)

            # Separar as horas em dois períodos
            df_manha_tarde = df_entrada_cana_hora[(df_entrada_cana_hora['hora'] >= '07:00') & (df_entrada_cana_hora['hora'] <= '23:00')]
            df_noite_madrugada = df_entrada_cana_hora[(df_entrada_cana_hora['hora'] >= '00:00') & (df_entrada_cana_hora['hora'] < '07:00')]

            # Concatenar os dois períodos para criar a nova ordem
            df_entrada_cana_hora_ajustada = pd.concat([df_manha_tarde, df_noite_madrugada])

            df_grupo = df_entrada_cana_hora_ajustada.groupby('hora')['pesoliquido'].sum().reset_index()
            df_grupo['unidade'] = 'Grupo'  # Adicionar uma coluna para identificar que esta linha é o total do grupo

            # Adicionar essa informação ao DataFrame original
            df_combined = pd.concat([df_entrada_cana_hora_ajustada, df_grupo], ignore_index=True)

        
        st.markdown(f'<div class="custom-header2"><h3>Estoque Pátio (ton)</h3></div>', unsafe_allow_html=True)
        col5, col6, col7, col8 = st.columns(4) 
        
        #AVALIAR O STATUS DO ESTOQUE DE CANA PELA MOAGEM HORA

        capacidade_mo_generalco = 8500
        capacidade_mo_alcoazul = 8000
        capacidade_mo_figueira = 6360
        capacidade_mo_grupo = capacidade_mo_generalco+capacidade_mo_alcoazul+capacidade_mo_figueira

        generalco_moagem_hora = capacidade_mo_generalco/24
        alcoazul_moagem_hora = capacidade_mo_alcoazul/24
        figueira_moagem_hora = capacidade_mo_figueira/24
        grupo_moagem_hora = capacidade_mo_grupo/24

        #⚠🔻✅
        #ALCOAZUL
        if df_estoque_patio['valor'].iloc[0] <alcoazul_moagem_hora*2:
            icone_alcoazul = "🔻"
        else:
            icone_alcoazul = "✅"

        #GENERALCO
        if df_estoque_patio['valor'].iloc[2] <generalco_moagem_hora*2:
            icone_generalco = "🔻"
        else:
            icone_generalco = "✅"

        #FIGUEIRA
        if df_estoque_patio['valor'].iloc[1] <figueira_moagem_hora*2:
            icone_figueira = "🔻"
        else:
            icone_figueira = "✅"

        with col5:
            var_teste = df_estoque_patio['valor'].iloc[0]
            st.markdown(f'''
            <div class="card-box">
                <h3 class="valor-teste">{var_teste}</h3><h6 class="icone-teste">{icone_alcoazul}</h6>         
            </div>
            ''', unsafe_allow_html=True)

        with col6:
            var_teste = df_estoque_patio['valor'].iloc[2]
            st.markdown(f'''
            <div class="card-box">
                <h3 class="valor-teste">{var_teste}</h3><h6 class="icone-teste">{icone_generalco}</h6> 
            </div>
            ''', unsafe_allow_html=True)

        with col7:
            var_teste = df_estoque_patio['valor'].iloc[1]
            st.markdown(f'''
            <div class="card-box">
                <h3 class="valor-teste">{var_teste}</h3><h6 class="icone-teste">{icone_figueira}</h6> 
            </div>
            ''', unsafe_allow_html=True)
        with col8:
            var_teste = df_estoque_patio['valor'].sum()
            st.markdown(f'''
            <div class="card-box">
                <h3>{var_teste}</h3> 
            </div>
            ''', unsafe_allow_html=True)

        col9,col10 = st.columns([2.2,1])
        with col9:
            st.markdown(f'<div class="custom-header2"><h3>Moagem Hora</h3></div>', unsafe_allow_html=True)
            fig = px.bar(
            df_entrada_cana_hora_ajustada,
            x='hora',
            y='pesoliquido',
            color='unidade',  
            title="Moagem por Hora (07:00 - 06:00)",
            text='pesoliquido',
            labels={'pesoliquido': 'Peso Líquido (ton)', 'hora': 'Hora', 'unidade': 'Unidade'}
            )

            fig.update_traces(texttemplate='%{text:.2f}')  # Exibe dois dígitos decimais

            # Atualizar o layout do gráfico, se necessário
            fig.update_layout(
                barmode='stack',  # Modo empilhado ('stack') ou lado a lado ('group')
                xaxis_title="Hora do Dia",
                yaxis_title="Peso Líquido (ton)",
                legend_title="Unidade",
                legend=dict(
                    orientation="h",  # Horizontal
                    yanchor="bottom",  # Âncora vertical
                    y=1.02,  # Posição vertical
                    xanchor="center",  # Âncora horizontal
                    x=0.5  # Centraliza horizontalmente
                ),
                plot_bgcolor="rgba(0, 0, 0, 0)",  # Fundo transparente (opcional)
                paper_bgcolor="rgba(0, 0, 0, 0)",  # Fundo transparente (opcional)
            )

            # Exibir o gráfico no Streamlit
            st.plotly_chart(fig, use_container_width=True)
        with col10:
            total_final = 3856158
            total_atual = df_entrada_cana["Grupo"].iloc[3]
            saldo_moagem =  total_final - total_atual
            percentual_de_progresso = (total_atual / total_final) * 100

            #pegando a moagem dos últimos 15 dias
            with st.spinner("Carregando dados.."):   
             df_fato_entrada_cana_ultimos_15_dias = load_data_post(query_entrada_cana_ultimos_15_dias)
            df_moagem_dia = df_fato_entrada_cana_ultimos_15_dias.groupby('datamovimento')['pesoliquido'].sum().reset_index()
            df_moagem_dia = df_moagem_dia.sort_values(by='datamovimento')    
            # Filtrar os últimos 15 dias
            df_ultimos_15_dias = df_moagem_dia.tail(15)
            # Calcular a média da moagem nos últimos 15 dias
            media_15_dias = df_ultimos_15_dias['pesoliquido'].mean()
            # Calcular os dias restantes para moer o saldo com base na média dos últimos 15 dias      
            dias_restantes = float(saldo_moagem) / media_15_dias
            if np.isnan(dias_restantes):
                dias_restantes = 0
            ultima_data = df_moagem_dia['datamovimento'].max()
            try:
                data_estimativa_termino = ultima_data + timedelta(days=dias_restantes)
            except:
                data_estimativa_termino =0
            fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=percentual_de_progresso,
            title={'text': "Percentual de moagem safra (%)"},
            gauge={
                'axis': {'range': [0, 100]},  # Definir o intervalo do gauge
                'bar': {'color': "lime"},  # Cor da barra
                'steps': [
                    {'range': [0, 100], 'color': "gray"}  # Cor do fundo
                ],
            },
            domain={'x': [0, 1], 'y': [0, 1]}
            ))

            # Alterar a cor de fundo do gráfico
            fig.update_layout(
                paper_bgcolor="#161717",  # Cor de fundo do gráfico
                plot_bgcolor="#161717",  # Cor de fundo da área de plotagem
                font={'color': "white"},  # Cor do texto
                margin={'t':70,'b':50,'l':0,'r':0},
                height=280,
            )

            st.markdown(f'<div class="custom-header2"><h3>Status Safra</h3></div>', unsafe_allow_html=True)
            st.write("")
            st.write(f'''
                        Moagem Safra Realizado: **{total_atual:,.0f}** - 
                        Moagem Previsto: **{total_final:,.0f}**'''.replace(",", "X").replace(".", ",").replace("X", "."))
            st.write(f"Saldo a moer: **{saldo_moagem:,.0f}**".replace(",", "X").replace(".", ",").replace("X", "."))
            st.write(f"Média de moagem dos últimos 15 dias: **{media_15_dias:.2f} ton**")
            st.write(f"Data estimada para final de safra: **{data_estimativa_termino.strftime('%d/%m/%Y')}**")

            st.plotly_chart(fig, use_container_width=True)
                
    time.sleep(60)  