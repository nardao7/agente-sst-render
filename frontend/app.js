// URL da sua API já publicada no Render.
// Essa URL aponta para o backend que já está rodando.
const API_URL = "https://agente-sst-render-api.onrender.com";

// Captura os elementos do HTML para manipular com JavaScript.
const perguntaInput = document.getElementById("pergunta");
const botaoEnviar = document.getElementById("enviar");
const statusDiv = document.getElementById("status");
const resultadoCard = document.getElementById("resultado");

// Campos onde a resposta será colocada.
const respostaObjetiva = document.getElementById("resposta_objetiva");
const baseNormativaLegal = document.getElementById("base_normativa_legal");
const explicacaoPratica = document.getElementById("explicacao_pratica");
const limiteTecnico = document.getElementById("limite_tecnico");
const nivelConfianca = document.getElementById("nivel_confianca");
const fontesLista = document.getElementById("fontes");

// Função que limpa os resultados anteriores.
function limparResultado() {
  respostaObjetiva.textContent = "";
  baseNormativaLegal.textContent = "";
  explicacaoPratica.textContent = "";
  limiteTecnico.textContent = "";
  nivelConfianca.textContent = "";
  fontesLista.innerHTML = "";
}

// Função que exibe as fontes recebidas da API.
function renderizarFontes(fontes) {
  fontesLista.innerHTML = "";

  // Se não houver fontes, mostra uma mensagem padrão.
  if (!fontes || fontes.length === 0) {
    const li = document.createElement("li");
    li.textContent = "Nenhuma fonte encontrada.";
    fontesLista.appendChild(li);
    return;
  }

  // Para cada fonte, criamos um item de lista.
  fontes.forEach((fonte) => {
    const li = document.createElement("li");

    const documento = fonte.documento || "Documento não informado";
    const referencia = fonte.referencia || "Referência não informada";

    li.textContent = `${documento} — ${referencia}`;
    fontesLista.appendChild(li);
  });
}

// Função principal que envia a pergunta para a API.
async function enviarPergunta() {
  const pergunta = perguntaInput.value.trim();

  // Validação simples para evitar envio vazio.
  if (!pergunta) {
    statusDiv.textContent = "Digite uma pergunta antes de enviar.";
    resultadoCard.classList.add("hidden");
    return;
  }

  // Prepara a interface para o carregamento.
  statusDiv.textContent = "Consultando o agente...";
  botaoEnviar.disabled = true;
  limparResultado();
  resultadoCard.classList.add("hidden");

  try {
    // Envia a requisição POST para a rota /ask da API.
    const resposta = await fetch(`${API_URL}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ pergunta: pergunta })
    });

    // Se a resposta HTTP não for sucesso, lança erro.
    if (!resposta.ok) {
      throw new Error(`Erro HTTP: ${resposta.status}`);
    }

    // Converte a resposta em JSON.
    const dados = await resposta.json();

    // Preenche a interface com os dados recebidos.
    respostaObjetiva.textContent = dados.resposta_objetiva || "";
    baseNormativaLegal.textContent = dados.base_normativa_legal || "";
    explicacaoPratica.textContent = dados.explicacao_pratica || "";
    limiteTecnico.textContent = dados.limite_tecnico || "";
    nivelConfianca.textContent = dados.nivel_confianca || "";

    renderizarFontes(dados.fontes);

    // Mostra o card da resposta.
    resultadoCard.classList.remove("hidden");

    // Limpa mensagem de status.
    statusDiv.textContent = "Resposta carregada com sucesso.";
  } catch (erro) {
    // Exibe erro amigável para o usuário.
    statusDiv.textContent =
      "Não foi possível consultar a API. Verifique se o backend está online e se a URL está correta.";

    console.error("Erro ao consultar API:", erro);
  } finally {
    // Reativa o botão ao final da execução.
    botaoEnviar.disabled = false;
  }
}

// Evento de clique no botão.
botaoEnviar.addEventListener("click", enviarPergunta);

// Permite enviar com Ctrl + Enter dentro do textarea.
perguntaInput.addEventListener("keydown", function (event) {
  if (event.ctrlKey && event.key === "Enter") {
    enviarPergunta();
  }
});