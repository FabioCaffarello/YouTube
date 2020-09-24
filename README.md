# YouTube

Neste Repositório contém códigos em Python, que estabelecem comunicação com o youtube.


**- Funcionalidade de Download**
tem por objetivo realizar o download e construir um arquivo de texto para todos os vídeos de uma playlist do youtube

Código: <a href="https://github.com/FabioCaffarello/YouTube/blob/master/youtube_download_videos.py">youtube_download_videos.py</a>

**- Funcionalidade de ETL**
tem por objetivo realizar ETL de dados do youtube e os carregar em banco de dados relacional (MySQL) e salvar a descrição em banco de dados Não relacional (MongoDB).

Código: <a href="https://github.com/FabioCaffarello/YouTube/blob/master/ETL_YouTube.py">ETL_YouTube.py</a>

Modelagem do SQL:

![database_model](https://user-images.githubusercontent.com/52248363/94188853-52676c00-fe80-11ea-8a24-0c42a0b95f87.png)

**Cada Função do código alimenta uma das tabelas e também alimenta uma collection no MongoDB, sendo que se armazena no MongoDB o ID proveniente do youtube e o ID proveniente do SQL e a descrição relacionada a cada collection.**
O objetivo de armazenar no MongoDB é de não onerar o BD relacional e poder realizar análises de text mining futuramente.




- Passos a serem realizados antes:
  1. Criar uma API KEY;
  2. Instalção do pacote google api client para python;
  3. Instalar o MySQL e salvar o user e password em variáveis de ambientes;
  4. Instalar o MongoDB.
  
### Criar uma API KEY

- Para cirar a API KEY do YouTube deve-se primeiro entrar no https://console.developers.google.com/ e criar um novo projeto:

![image](https://user-images.githubusercontent.com/52248363/90988521-c228c500-e569-11ea-9306-928fc1b3c0ce.png)

- Entre na biblioteca de APIs do Google

![image](https://user-images.githubusercontent.com/52248363/90988666-f81a7900-e56a-11ea-97c5-25532ccb279e.png)

- Procurar pela API do YOUTUBE (Obs.: neste projeto será utilizada a API "YouTube Data API v3" destacada)

![image](https://user-images.githubusercontent.com/52248363/90988760-9f97ab80-e56b-11ea-923c-0819b212cf82.png)

- Com a API selecionada, deve-se ativar a API no projeto:

![image](https://user-images.githubusercontent.com/52248363/90988801-0f0d9b00-e56c-11ea-8e8b-ac4c6b1b4200.png)

- Após ativação da API, deve-se criar a credencial

![image](https://user-images.githubusercontent.com/52248363/90988850-71ff3200-e56c-11ea-96bf-3c8c5167ef26.png)


- **Para habilitar a API KEY**, deve-se preencher os campos:

![image](https://user-images.githubusercontent.com/52248363/90988896-b68acd80-e56c-11ea-97f2-a265ed5c2fce.png)

- Feito os procedimetnos acima a **API KEY** será gerada:

![image](https://user-images.githubusercontent.com/52248363/90989004-9c9dba80-e56d-11ea-8c7a-84c8622b85b0.png)

**Esta API KEY foi armazenada em uma variável de ambiente.**

> **Documentação da API:** https://developers.google.com/youtube/v3?hl=pt_BR

### Instalção do pacote google api client para python

Neste projeto foi utilizado o pacote google api client para python (Documentação: https://github.com/googleapis/google-api-python-client)

Instalação: `pip install google-api-python-client`

Deste pacote foi utilizado a funçao build (http://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html#build)
Está função recebe como parâmetros serviceName e version, que, pode ser verificado em: https://github.com/googleapis/google-api-python-client/blob/master/docs/dyn/index.md, além desses parâmetros, também deve receber a API KEY, que, por sua vez foi criada anteriormente e está armazenada em uma variável de ambiente.

Com isso, pode-se consultar os metódos disponíveis da API do YouTube em: http://googleapis.github.io/google-api-python-client/docs/dyn/youtube_v3.html

Exemplo de request da API
```python
import os
from googleapiclient.discovery import build

api_key = os.environ.get('YT_API_KEY')

youtube = build('youtube','v3', developerKey=api_key)

request = youtube.channels().list(
			part='statistics',
			forUsername='dataschool'
	)

response = request.execute()
```
