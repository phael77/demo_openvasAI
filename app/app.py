from flask import Flask, render_template, request
import pandas as pd
import openai
import os

app = Flask(__name__)
openai.api_key = os.environ.get("Ssk-proj-MQOyCnziyWNrg6QzXwrR8ORt8TdjLm7Novd7AtnLTarSbt3EAOs2QjCUtDkmWSmHZiY4iET-tOT3BlbkFJBPzGaHOVEGZyKD5RLkXC-RUIt4zmzuVf6IzV71bsfPoeTcKNctpRO31x2k2DVbeMY92epu0Xg")

# Rota principal para exibir a página de upload
@app.route('/')
def upload_file():
    return render_template('upload.html')

# Rota para processar o relatório OpenVAS
@app.route('/upload', methods=['POST'])
def process_openvas_report():
    # Recebe o arquivo carregado
    file = request.files['file']
    if not file:
        return "Por favor, envie um arquivo CSV válido."

    # Lê o relatório OpenVAS em CSV
    try:
        openvas_df = pd.read_csv(file)
    except Exception as e:
        return f"Erro ao ler o arquivo CSV: {str(e)}"

    # Seleciona colunas importantes
    try:
        processed_data = openvas_df[['NVT Name', 'Summary', 'Severity']]
    except KeyError:
        return "O arquivo CSV deve conter as colunas 'NVT Name', 'Summary' e 'Severity'."

    # Divide os dados em chunks para limitar tokens no modelo
    summaries = []
    chunks = [processed_data[i:i+10] for i in range(0, len(processed_data), 10)]  # Máx. 10 vulnerabilidades por vez

    # Gera o resumo para cada chunk
    for chunk in chunks:
        prompt = generate_prompt(chunk)
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",  # Substitua por "gpt-4-mini" se aplicável
                messages=[
                    {"role": "system", "content": "Você é um consultor de segurança cibernética."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,  # Limite ajustado para o modelo
                temperature=0.7
            )
            summaries.append(response['choices'][0]['message']['content'])
        except Exception as e:
            return f"Erro ao gerar o resumo: {str(e)}"

    # Combina os resumos
    full_summary = "\n\n".join(summaries)

    # Retorna o resumo gerado na página
    return f"<h1>Resumo do Relatório OpenVAS</h1><pre>{full_summary}</pre>"

# Função para criar um prompt otimizado para IA
def generate_prompt(data):
    prompt = (
        "Você é um consultor de segurança cibernética. Com base nos dados fornecidos, "
        "crie um relatório com as seções 'Vulnerabilidades Críticas', "
        "'Mitigações Recomendadas' e 'Avaliação Geral de Riscos'.\n\n"
    )
    for _, row in data.iterrows():
        prompt += f"- Vulnerabilidade: {row['NVT Name']}\n"
        prompt += f"  Severidade: {row['Severity']}\n"
        prompt += f"  Descrição: {row['Summary']}\n"
    prompt += "\nResuma as informações acima nas seções mencionadas."
    return prompt

# Função de teste da integração com OpenAI
@app.route('/test-openai')
def test_openai():
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Substitua por "gpt-4-mini" se aplicável
            messages=[
                {
                    "role": "user",
                    "content": "Say this is a test",
                }
            ],
            max_tokens=50
        )
        result = response['choices'][0]['message']['content']
        return f"<h1>Teste da OpenAI</h1><pre>{result}</pre>"
    except Exception as e:
        return f"Erro ao testar a API OpenAI: {str(e)}"

# Inicia o servidor Flask
if __name__ == '__main__':
    app.run(debug=True)