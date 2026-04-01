import os

import textwrap

from flask import Flask, render_template, request, jsonify, send_file

from google import genai  # Nova biblioteca

from dotenv import load_dotenv

from io import BytesIO

from reportlab.pdfgen import canvas

from reportlab.lib.pagesizes import A4



load_dotenv()



app = Flask(__name__)



# Configuração do novo Cliente

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

MODEL_ID = "gemini-2.5-flash"



@app.route('/')

def index():

    return render_template('index.html')



@app.route('/gerar-cardapio', methods=['POST'])

def gerar_cardapio():

    try:

        dados = request.json

        peso = float(str(dados.get('peso', '0')).replace(',', '.'))

        altura = float(str(dados.get('altura', '0')).replace(',', '.'))



        if altura <= 0 or peso <= 0:

            return jsonify({"error": "Dados inválidos"}), 400



        imc = peso / (altura ** 2)

        objetivo = dados.get('objetivo')

        preferencias = dados.get('preferencias')



        prompt = f"""

        Atue como um Chef de Cozinha Especializado em Nutrição Esportiva.

        PACIENTE: IMC {imc:.2f}, OBJETIVO: {objetivo}.

        INGREDIENTES DISPONÍVEIS: {preferencias}.



        TAREFA: Gere um cardápio semanal (7 dias) com REFEIÇÕES COMPLETAS (Receitas rápidas).

       

        DIRETRIZES DE GASTRONOMIA:

        1. COMBINAÇÃO: Os ingredientes devem combinar entre si. Ex: Se usar ovo e aveia, sugira uma panqueca ou mingau salgado, não itens isolados.

        2. ESTRUTURA: Cada refeição DEVE ter 1 Proteína, 1 Carboidrato e 1 Legume/Leguminosa de forma integrada.

        3. DESCRIÇÃO: Não dê apenas o ingrediente bruto. Dê o NOME DA PREPARAÇÃO e os ingredientes com porções.

        4. PORCIONAMENTO: É importante que as porções respeitem, de forma lógica, o objetivo e IMC de cada pessoa.

        5. CALORIAS: Calcule o total calórico aproximado para cada DIA baseado no objetivo '{objetivo}'.

       

        REGRAS DE FORMATAÇÃO (CRÍTICO):

        - Use EXATAMENTE o modelo abaixo.

        - NÃO use Markdown (sem asteriscos **, sem negrito).

        - Use listas com "-" para os itens.



        MODELO DE RESPOSTA (SIGA RIGOROSAMENTE):

        ---

        Dia: Segunda-feira

        Calorias Totais: 2100 kcal

        Café:

        Omelete de Aveia e Ervas

        - 2 ovos inteiros

        - 30g de aveia em flocos

        Almoço:

        Bowl de Frango com Quinoa

        - 150g de frango grelhado

        - 100g de quinoa cozida

        Jantar:

        Tilápia com Purê de Inhame

        - 150g de tilápia

        - 120g de inhame cozido

        ---

        """

       

        # Nova forma de chamar a geração de conteúdo

        response = client.models.generate_content(

            model=MODEL_ID,

            contents=prompt

        )



        if not response.text:

            return jsonify({"error": "IA não retornou texto"}), 500



        return jsonify({"cardapio": response.text, "imc": round(imc, 2)})



    except Exception as e:

        print(f"Erro: {e}")

        return jsonify({"error": str(e)}), 500



@app.route('/exportar-pdf', methods=['POST'])

def exportar_pdf():

    try:

        dados = request.json

        if not dados or 'conteudo' not in dados:

            return jsonify({"error": "Conteúdo vazio"}), 400



        buffer = BytesIO()

        p = canvas.Canvas(buffer, pagesize=A4)

        width, height = A4

       

        p.setFont("Helvetica-Bold", 16)

        p.drawString(50, height - 50, "PLANO ALIMENTAR - NUTR IA")

       

        p.setFont("Helvetica", 10)

        y = height - 80

       

        # O segredo está aqui: ignorar caracteres que o PDF não suporta

        texto = str(dados['conteudo']).encode('ascii', 'ignore').decode('ascii')

       

        for linha in texto.split('\n'):

            # Divide linhas muito longas para não saírem da folha

            linhas_wrap = textwrap.wrap(linha, width=85)

            for wrap_line in linhas_wrap:

                if y < 50:

                    p.showPage()

                    p.setFont("Helvetica", 10)

                    y = height - 50

                p.drawString(50, y, wrap_line)

                y -= 15

            y -= 5

           

        p.save()

        buffer.seek(0)

        return send_file(

            buffer,

            as_attachment=True,

            download_name="cardapio_nutria.pdf",

            mimetype='application/pdf'

        )

    except Exception as e:

        print(f"Erro no PDF: {e}")

        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':

    app.run(debug=True)

