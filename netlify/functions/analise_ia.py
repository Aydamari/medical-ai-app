import os
import json
import requests

def handler(event, context):
    # Imprime o início da invocação para sabermos que a função foi chamada
    print("Iniciando a função analise_ia...")

    if event['httpMethod'] != 'POST':
        print(f"Método HTTP não permitido: {event['httpMethod']}")
        return {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method Not Allowed'})
        }

    try:
        print("A processar o corpo da requisição...")
        body = json.loads(event['body'])
        model_key = body.get('model_key')
        prompt = body.get('prompt')
        image_base64 = body.get('image_base64')
        print(f"Modelo selecionado: {model_key}")

        if not all([model_key, prompt, image_base64]):
            print("Erro: Dados em falta na requisição.")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Dados em falta na requisição.'})
            }

        # --- Carregamento Seguro das Variáveis de Ambiente ---
        print("A carregar variáveis de ambiente...")
        HF_API_TOKEN = os.environ.get('HF_TOKEN')
        
        if model_key == '4b':
            API_URL = os.environ.get('ENDPOINT_URL_4B')
        elif model_key == '27b':
            API_URL = os.environ.get('ENDPOINT_URL_27B')
        else:
            print(f"Erro: Chave de modelo inválida: {model_key}")
            raise ValueError("Chave de modelo inválida.")

        if not HF_API_TOKEN or not API_URL:
            print("Erro: Variáveis de ambiente não configuradas corretamente no Netlify.")
            raise EnvironmentError("Variáveis de ambiente não configuradas no Netlify.")
        
        print(f"A enviar requisição para o endpoint: {API_URL}")

        # --- Chamada para a API do Hugging Face ---
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        payload = {"inputs": {"prompt": prompt, "image": image_base64}}
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=180) # Timeout de 3 minutos
        print(f"Resposta recebida do Hugging Face com status: {response.status_code}")
        response.raise_for_status()
        
        result = response.json()
        print("Resposta processada com sucesso.")

        return {
            'statusCode': 200,
            'headers': { 'Content-Type': 'application/json' },
            'body': json.dumps(result)
        }

    except requests.exceptions.Timeout:
        print("Erro: Timeout na comunicação com a API do Hugging Face.")
        return {'statusCode': 504, 'body': json.dumps({'error': 'A API demorou demasiado a responder (Timeout).'})}
    except requests.exceptions.RequestException as e:
        print(f"Erro de RequestException: {str(e)}")
        # Tenta devolver o corpo da resposta de erro do HF, se existir
        error_body = e.response.text if e.response else "Nenhuma resposta do servidor."
        return {'statusCode': 502, 'body': json.dumps({'error': f'Erro na comunicação com a API: {str(e)}', 'details': error_body})}
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': f'Ocorreu um erro interno: {str(e)}'})}

