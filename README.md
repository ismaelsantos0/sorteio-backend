# 🎯 InstaSorteios — Back-end API

API do SaaS de Sorteios de Comentários do Instagram.
Construída com **Python + FastAPI**, hospedada no **Railway**.

---

## 🗂️ Estrutura de Pastas

```
sorteio-backend/
├── main.py                    # App FastAPI principal (CORS, Rate Limit, Rotas)
├── Procfile                   # Comando de start para o Railway
├── requirements.txt           # Dependências Python
├── .env.example               # Modelo das variáveis de ambiente (sem valores!)
├── .gitignore                 # Arquivos ignorados pelo Git
│
├── core/
│   ├── config.py              # Leitura segura das variáveis de ambiente (Settings)
│   └── security.py            # Criação e validação de JWT Tokens
│
├── services/
│   ├── apify_service.py       # Integração com Apify (Sondagem + Raspagem)
│   ├── payment_service.py     # Integração com Mercado Pago (Pix + Webhook)
│   └── sorteio_service.py     # Algoritmo de sorteio com filtros
│
└── api/
    └── routes/
        ├── auth.py            # POST /api/auth/login (Login Facebook → JWT)
        ├── scrape.py          # POST /api/scrape/sondagem (Conta comentários)
        ├── payment.py         # POST /api/payment/checkout | /webhook | /status
        └── sorteio.py         # POST /api/sorteio/executar (Sorteia após pagamento)
```

---

## ⚙️ Como rodar localmente

### 1. Clonar e instalar
```bash
git clone https://github.com/SEU_USUARIO/sorteio-backend.git
cd sorteio-backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 2. Configurar o .env
```bash
copy .env.example .env
# Edite o .env e preencha todas as chaves
```

### 3. Rodar o servidor
```bash
uvicorn main:app --reload
```

Acesse a documentação interativa em: http://localhost:8000/docs

---

## 🚀 Deploy no Railway

1. Faça push para o GitHub (repositório **privado**).
2. No Railway, crie um novo projeto → "Deploy from GitHub Repo".
3. Configure todas as variáveis do `.env.example` no painel **Variables** do Railway.
4. O Railway usará o `Procfile` para subir o servidor automaticamente.

---

## 🔥 Endpoints Principais

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/` | Health check |
| `POST` | `/api/auth/login` | Login com Facebook → JWT |
| `POST` | `/api/scrape/sondagem` | Sonda o post (contagem + preço) |
| `POST` | `/api/payment/checkout` | Gera QR Code Pix |
| `POST` | `/api/payment/webhook` | Recebe confirmação do MP |
| `GET` | `/api/payment/status/{id}` | Polling de status de pagamento |
| `POST` | `/api/sorteio/executar` | Executa o sorteio (pós-pagamento) |
