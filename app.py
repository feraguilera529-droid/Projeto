import io
from openai import AzureOpenAI
import pypdf
import streamlit as st

# ==========================================
# CONFIGURAÇÃO DA PÁGINA E ESTILO (CSS)
# ==========================================
st.set_page_config(
    page_title="ChatBot RAG - Microsoft Foundry",
    page_icon="🤖",
    layout="centered",
)

# Estilização CSS customizada para criar uma borda profissional na área principal
st.markdown(
    """
    <style>
    /* Borda e espaçamento ao redor do conteúdo principal */
    .stMainBlockContainer {
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 2rem;
        background-color: #ffffff;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    /* Estilização da barra lateral */
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Títulos e textos */
    h1 {
        color: #1e293b;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# CONFIGURAÇÃO DA API (MICROSOFT FOUNDRY)
# ==========================================
API_KEY = "6t2pTNsmNafDyo53MDAFIrvvQRBZXP7dLcr5j3TLxMS34LQVq3ZUJQQJ99CHACHYHv6XJ3w3AAAAACOGT7os"
ENDPOINT = "https://marcelomaffeis-05082026-resource.services.ai.azure.com/"
DEPLOYMENT_NAME = "gpt-4.1-mini"

# Inicialização do cliente Azure OpenAI
client = AzureOpenAI(
    api_key=API_KEY, api_version="2024-05-01-preview", azure_endpoint=ENDPOINT
)

# ==========================================
# FUNÇÕES DE PROCESSAMENTO DE ARQUIVOS (RAG)
# ==========================================


def extract_text(uploaded_file):
  """Extrai o texto de arquivos PDF ou TXT enviados pelo usuário."""
  file_extension = uploaded_file.name.split(".")[-1].lower()
  text = ""

  if file_extension == "pdf":
    reader = pypdf.PdfReader(uploaded_file)
    for page in reader.pages:
      extracted = page.extract_text()
      if extracted:
        text += extracted + "\n"
  elif file_extension == "txt":
    text = uploaded_file.getvalue().decode("utf-8")

  return text


# ==========================================
# INTERFACE DA BARRA LATERAL (SIDEBAR)
# ==========================================
st.sidebar.title("📁 Base de Conhecimento (RAG)")
st.sidebar.markdown(
    "Envie um arquivo PDF ou TXT para que o assistente utilize o conteúdo como"
    " contexto."
)

uploaded_file = st.sidebar.file_uploader(
    "Escolha um arquivo", type=["pdf", "txt"]
)

# Gerenciador de contexto no session_state
if "document_text" not in st.session_state:
  st.session_state.document_text = ""

if uploaded_file is not None:
  # Processa o arquivo apenas se for um novo envio
  if (
      "uploaded_file_name" not in st.session_state
      or st.session_state.uploaded_file_name != uploaded_file.name
  ):
    with st.spinner("Extraindo texto do documento..."):
      st.session_state.document_text = extract_text(uploaded_file)
      st.session_state.uploaded_file_name = uploaded_file.name
    st.sidebar.success(f"Arquivo '{uploaded_file.name}' carregado com sucesso!")
  else:
    st.sidebar.info(f"Arquivo ativo: {uploaded_file.name}")
else:
  st.sidebar.warning(
      "Nenhum arquivo carregado. O bot responderá com o conhecimento geral do"
      " modelo."
  )

if st.sidebar.button("🗑️ Limpar Conversa e Contexto"):
  st.session_state.messages = []
  st.session_state.document_text = ""
  if "uploaded_file_name" in st.session_state:
    del st.session_state.uploaded_file_name
  st.rerun()

# ==========================================
# INTERFACE PRINCIPAL DO CHAT
# ==========================================
st.title("🤖 ChatBot Acadêmico com RAG")
st.caption(
    "Utilizando Microsoft Foundry (Azure OpenAI) e Streamlit para"
    " Contextualização de Documentos."
)

# Inicializa o histórico de mensagens no session_state
if "messages" not in st.session_state:
  st.session_state.messages = []

# Exibe o histórico de mensagens existentes
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

# Captura a entrada do usuário
if prompt := st.chat_input("Faça uma pergunta sobre o documento ou geral..."):
  # Adiciona a mensagem do usuário ao histórico
  st.session_state.messages.append({"role": "user", "content": prompt})
  with st.chat_message("user"):
    st.markdown(prompt)

  # Constrói o prompt do sistema combinando comportamento padrão + RAG
  system_prompt = (
      "Você é um assistente virtual especialista e prestativo. "
      "Responda à pergunta do usuário com base primária no CONTEXTO DO DOCUMENTO fornecido abaixo. "
      "Se a resposta não estiver no documento, informe educadamente que o documento não contém essa informação, "
      "mas ofereça ajuda com base no seu conhecimento geral se aplicável."
  )

  if st.session_state.document_text:
    system_prompt += (
        f"\n\n--- CONTEXTO DO DOCUMENTO ---\n{st.session_state.document_text}\n"
        "-----------------------------"
    )

  # Prepara as mensagens para a API do Azure OpenAI
  messages_payload = [{"role": "system", "content": system_prompt}]
  for m in st.session_state.messages:
    messages_payload.append({"role": m["role"], "content": m["content"]})

  # Gera a resposta do modelo
  with st.chat_message("assistant"):
    with st.spinner("Pensando..."):
      try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME, messages=messages_payload, temperature=0.3
        )
        assistant_response = response.choices[0].message.content
        st.markdown(assistant_response)

        # Salva a resposta no histórico
        st.session_state.messages.append(
            {"role": "assistant", "content": assistant_response}
        )
      except Exception as e:
        error_msg = f"Ocorreu um erro ao comunicar com a API do Microsoft Foundry: {e}"
        st.error(error_msg)
