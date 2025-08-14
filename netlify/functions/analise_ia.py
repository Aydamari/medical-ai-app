import os
import json
import requests

def handler(event, context):
    # Apenas permite requisições POST
    if event['httpMethod'] != 'POST':
        return {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method Not Allowed'})
        }

    try:
        # Carrega os dados enviados pelo front-end
        body = json.loads(event['body'])
        model_key = body.get('model_key')
        prompt = body.get('prompt')
        image_base64 = body.get('image_base64')

        if not all([model_key, prompt, image_base64]):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Dados em falta na requisição.'})
            }

        # --- Carregamento Seguro das Variáveis de Ambiente ---
        HF_API_TOKEN = os.environ.get('HF_TOKEN')
        
        # Seleciona a URL do endpoint com base na escolha do utilizador
        if model_key == '4b':
            API_URL = os.environ.get('ENDPOINT_URL_4B')
        elif model_key == '27b':
            API_URL = os.environ.get('ENDPOINT_URL_27B')
        else:
            raise ValueError("Chave de modelo inválida.")

        if not HF_API_TOKEN or not API_URL:
            raise EnvironmentError("Variáveis de ambiente não configuradas no Netlify.")

        # --- Chamada para a API do Hugging Face ---
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        
        # O payload para modelos de imagem-para-texto geralmente espera a imagem em base64
        payload = {
            "inputs": {
                "prompt": prompt,
                "image": image_base64
            }
        }
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120) # Timeout de 2 minutos
        response.raise_for_status() # Lança um erro para respostas HTTP > 400
        
        result = response.json()

        # Retorna a resposta com sucesso para o front-end
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*' # Permite que o seu site aceda à resposta
            },
            'body': json.dumps(result)
        }

    except requests.exceptions.RequestException as e:
        # Erro de rede ou da API do Hugging Face
        return {
            'statusCode': 502,
            'body': json.dumps({'error': f'Erro na comunicação com a API do Hugging Face: {str(e)}'})
        }
    except Exception as e:
        # Outros erros inesperados
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Ocorreu um erro interno: {str(e)}'})
        }


