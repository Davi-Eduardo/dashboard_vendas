import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(layout='wide')

def formata_numero(valor, prefixo=''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

st.title('DASHBOARD DE VENDAS :shopping_trolley:')

url = 'https://labdados.com/produtos'
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')
regiao = st.sidebar._selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o período', value=True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)

query_string = {'regiao': regiao.lower(), 'ano':ano}

response = requests.get(url, params=query_string)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

## Tabelas aba1
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(
    receita_estados, left_on='Local da compra', right_index=True).sort_values('Preço', ascending=False)

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='ME'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()

receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

##Tabelas aba2
vendas_regiao = dados.groupby('Local da compra').size().reset_index(name='Quantidade de Vendas')
vendas_regiao = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(
    vendas_regiao, on='Local da compra').sort_values('Quantidade de Vendas', ascending=False)

vendas_mensal = dados.set_index(['Data da Compra']).groupby(pd.Grouper(freq='ME')).size().reset_index(name='Quantidade de Vendas')
vendas_mensal['Ano'] = vendas_mensal['Data da Compra'].dt.year
vendas_mensal['Mes'] = vendas_mensal['Data da Compra'].dt.month_name()

vendas_estado = dados.groupby('Local da compra').size().reset_index(name='Quantidade de Vendas').sort_values('Quantidade de Vendas', ascending=False)

vendas_produto = dados.groupby('Categoria do Produto').size().reset_index(name='Quantidade de Vendas').sort_values('Quantidade de Vendas', ascending=False)

## Tabelas aba3
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

## Gráficos aba1
fig_mapa_receita = px.scatter_geo(
                                receita_estados,
                                lat='lat',
                                lon='lon',
                                scope='south america',
                                size='Preço',
                                template='seaborn',
                                hover_name='Local da compra',
                                hover_data={'lat': False, 'lon': False},
                                title='Receita por Estado'
                                )

fig_receita_mensal = px.line(
                            receita_mensal,
                            x='Mes',
                            y='Preço',
                            markers=True,
                            range_y=(0, receita_mensal.max()),
                            color='Ano',
                            line_dash='Ano',
                            title='Receita mensal'
                            )

fig_receita_mensal.update_layout(yaxis_title='Receita')

fig_receita_estados = px.bar(
                            receita_estados.head(),
                            x='Local da compra',
                            y='Preço',
                            text_auto=True,
                            title='Top Estados (Receita)'
                            )

fig_receita_estados.update_layout(yaxis_title='Receita')

fig_receita_categorias = px.bar(
                                receita_categorias,
                                text_auto=True,
                                title='Receita por Categoria'
                                )

fig_receita_categorias.update_layout(yaxis_title='Receita')

## Gráficos aba2
fig_vendas_regiao = px.scatter_geo(vendas_regiao,
                                   lat='lat',
                                   lon='lon',
                                   scope='south america',
                                   size='Quantidade de Vendas',
                                   template='seaborn',
                                   hover_name='Local da compra',
                                   hover_data={'lat': False, 'lon': False},
                                   title='Total de vendas por Estado'
                                   )

fig_vendas_mensal = px.line(
                            vendas_mensal,
                            x='Mes',
                            y='Quantidade de Vendas',
                            markers=True,
                            range_y=(0, vendas_mensal.max()),
                            color='Ano',
                            line_dash='Ano',
                            title='Vendas mensal'
                            )

fig_vendas_produto = px.bar(
                            vendas_produto.head(),
                            x='Categoria do Produto',
                            y='Quantidade de Vendas',
                            text_auto=True,
                            title='Vevndas por Categoria'
                            )

fig_vendas_estados = px.bar(
                            vendas_estado.head(),
                            x='Local da compra',
                            y='Quantidade de Vendas',
                            text_auto=True,
                            title='Top Estados (Vendas)'
                            )

## Visualização no streamlit
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de Vendas', 'Vendedores'])

with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_estados, use_container_width=True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categorias, use_container_width=True)

with aba2:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_vendas_regiao, use_container_width=True)
        st.plotly_chart(fig_vendas_estados, use_container_width=True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_vendas_mensal, use_container_width=True)
        st.plotly_chart(fig_vendas_produto, use_container_width=True)   

with aba3:
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),
                                        x='sum',
                                        y=vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores).index,
                                        text_auto=True,
                                        title=f'Top {qtd_vendedores} vendedores (receita)')
        fig_receita_vendedores.update_layout(xaxis_title='Receita')
        fig_receita_vendedores.update_layout(yaxis_title='Vendedor')
        st.plotly_chart(fig_receita_vendedores, use_container_width=True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
                                        x='count',
                                        y=vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores).index,
                                        text_auto=True,
                                        title=f'Top {qtd_vendedores} vendedores (quantidade de vendas)')
        fig_vendas_vendedores.update_layout(xaxis_title='Qtd. Vendas')
        fig_vendas_vendedores.update_layout(yaxis_title='Vendedor')
        st.plotly_chart(fig_vendas_vendedores, use_container_width=True)
       