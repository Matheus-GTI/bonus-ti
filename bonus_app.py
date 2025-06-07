import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
from io import BytesIO
from fpdf import FPDF

st.set_page_config(page_title="Sistema de Bônus - TI", layout="wide")

st.title("Sistema de Bônus - Equipe de TI")

uploaded_file = st.file_uploader("Carregar planilha de requisições (.xlsx)", type=["xlsx"])

logo_url = "https://upload.wikimedia.org/wikipedia/commons/6/6c/Bensaude-logo.png"

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df['Data_Prevista'] = pd.to_datetime(df['Data_Prevista'])
    df['Data_Real'] = pd.to_datetime(df['Data_Real'])

    df['Ano'] = df['Data_Real'].dt.year
    df['Mes'] = df['Data_Real'].dt.month
    anos = sorted(df['Ano'].unique())
    meses = sorted(df['Mes'].unique())

    col1, col2 = st.columns(2)
    with col1:
        ano_sel = st.selectbox("Selecione o ano", anos, index=len(anos)-1)
    with col2:
        mes_sel = st.selectbox("Selecione o mês", meses, index=len(meses)-1)

    df = df[(df['Ano'] == ano_sel) & (df['Mes'] == mes_sel)]

    st.subheader("Base de Requisições Filtrada")
    st.dataframe(df)

    st.subheader("Apuração de Bônus")

    avaliacoes = []
    for nome in df['Nome'].unique():
        sub_df = df[df['Nome'] == nome]

        produtividade = len(sub_df) / len(df) * 2
        qualidade = (sub_df['Retrabalho'] == 0).sum() / len(sub_df) * 2
        prazo = (sub_df['Data_Real'] <= sub_df['Data_Prevista']).sum() / len(sub_df) * 2

        nota_total = produtividade + qualidade + prazo
        nota_valida = nota_total >= 4 and produtividade > 0 and qualidade > 0 and prazo > 0

        faltas = sub_df['Faltas'].iloc[0] == "Sim"
        ferias = sub_df['Férias'].iloc[0] == "Sim"
        horas_trab = sub_df['Horas'].sum()

        elegivel = nota_valida and not faltas

        bonus_individual = 0
        bonus_coletivo = 0
        if elegivel:
            bonus_individual = 6000 / 4
            bonus_coletivo = 4000 / 4

        if ferias:
            bonus_individual *= (horas_trab / 160)
            bonus_coletivo *= (horas_trab / 160)

        avaliacoes.append({
            "Nome": nome,
            "Produtividade": round(produtividade, 2),
            "Qualidade": round(qualidade, 2),
            "Prazo": round(prazo, 2),
            "Total": round(nota_total, 2),
            "Elegível": "Sim" if elegivel else "Não",
            "Bônus Individual": round(bonus_individual, 2),
            "Bônus Coletivo": round(bonus_coletivo, 2),
            "Bônus Total": round(bonus_individual + bonus_coletivo, 2)
        })

    resultado_df = pd.DataFrame(avaliacoes)
    st.dataframe(resultado_df)

    st.subheader("Dashboard de Desempenho")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(resultado_df['Nome'], resultado_df['Bônus Total'], color='skyblue')
    ax.set_title("Bônus Total por Colaborador")
    ax.set_ylabel("R$")
    st.pyplot(fig)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        resultado_df.to_excel(writer, index=False, sheet_name='Relatorio')
        writer.save()
    st.download_button(
        label="Exportar Relatório em Excel",
        data=buffer.getvalue(),
        file_name="relatorio_bonus.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    def gerar_pdf(df):
        pdf = FPDF()
        pdf.add_page()
        pdf.image(logo_url, x=80, y=10, w=50)
        pdf.ln(50)
        pdf.set_font("Arial", 'B', 20)
        pdf.cell(0, 20, "Sistema de Bônus - Relatório Mensal", ln=True, align='C')
        pdf.set_font("Arial", '', 14)
        pdf.cell(0, 10, f"Referente a: {mes_sel:02d}/{ano_sel}", ln=True, align='C')
        pdf.cell(0, 10, "Empresa: Bensaúde Plano de Assistência Médica", ln=True, align='C')
        pdf.ln(20)
        pdf.set_font("Arial", 'I', 12)
        pdf.cell(0, 10, "Relatório gerado automaticamente via sistema Streamlit.", ln=True, align='C')

        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, txt="Detalhamento por Colaborador", ln=True, align='C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(200, 8, txt=f"Data de Geração: {datetime.today().strftime('%d/%m/%Y')}", ln=True, align='R')
        pdf.ln(8)

        pdf.set_font("Arial", 'B', 11)
        pdf.cell(40, 8, "Nome", 1)
        pdf.cell(30, 8, "Prod.", 1, align='C')
        pdf.cell(30, 8, "Qualid.", 1, align='C')
        pdf.cell(30, 8, "Prazo", 1, align='C')
        pdf.cell(25, 8, "Elegível", 1, align='C')
        pdf.cell(35, 8, "Bônus Total", 1, align='C')
        pdf.ln()

        pdf.set_font("Arial", '', 10)
        for _, row in df.iterrows():
            pdf.cell(40, 8, row['Nome'], 1)
            pdf.cell(30, 8, f"{row['Produtividade']}", 1, align='C')
            pdf.cell(30, 8, f"{row['Qualidade']}", 1, align='C')
            pdf.cell(30, 8, f"{row['Prazo']}", 1, align='C')
            pdf.cell(25, 8, row['Elegível'], 1, align='C')
            pdf.cell(35, 8, f"R$ {row['Bônus Total']:.2f}", 1, align='R')
            pdf.ln()

        pdf.ln(10)
        pdf.set_font("Arial", 'I', 9)
        pdf.cell(0, 10, txt="Assinado eletronicamente por: Diretor de TI", ln=True, align='L')

        pdf_output = BytesIO()
        pdf.output(pdf_output)
        return pdf_output

    pdf_file = gerar_pdf(resultado_df)
    st.download_button(
        label="Exportar PDF do Relatório",
        data=pdf_file.getvalue(),
        file_name="relatorio_bonus.pdf",
        mime="application/pdf"
    )
else:
    st.info("Por favor, envie um arquivo Excel com a planilha de requisições.")
