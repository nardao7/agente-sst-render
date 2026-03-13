const API_URL = "https://agente-sst-render-api.onrender.com";

const perguntaInput = document.getElementById("pergunta");
const botaoEnviar = document.getElementById("enviar");
const statusDiv = document.getElementById("status");
const resultadoCard = document.getElementById("resultado");

const respostaObjetiva = document.getElementById("resposta_objetiva");
const baseNormativaLegal = document.getElementById("base_normativa_legal");
const explicacaoPratica = document.getElementById("explicacao_pratica");
const limiteTecnico = document.getElementById("limite_tecnico");
const trechoNormativoExato = document.getElementById("trecho_normativo_exato");
const fontesContainer = document.getElementById("fontes");
const badgeConfianca = document.getElementById("badge_confianca");
const badgeModo = document.getElementById("badge_modo");

function limparResultado() {
  respostaObjetiva.textContent = "";
  baseNormativaLegal.textContent = "";
  explicacaoPratica.textContent = "";
  limiteTecnico.textContent = "";
  trechoNormativoExato.textContent = "";
  fontesContainer.innerHTML = "";
  badgeConfianca.textContent = "Confiança";
  badgeModo.textContent = "Modo";
}

function renderizarFontes(fontes) {
  fontesContainer.innerHTML = "";

  if (!fontes || fontes.length === 0) {
    fontesContainer.innerHTML = "<p>Nenhuma fonte encontrada.</p>";
    return;
  }

  fontes.forEach((fonte) => {
    const card = document.createElement("div");
    card.className = "fonte-card";

    card.innerHTML = `
      <div class="fonte-topo">
        <span class="document-badge">${fonte.documento || "Documento"}</span>
        <span class="item-badge">${fonte.item || fonte.referencia || "Sem item"}</span>
      </div>
      <h4>${fonte.titulo || "Trecho normativo"}</h4>
      <p><strong>Tipo:</strong> ${fonte.tipo_fonte || "Fonte normativa"}</p>
      <p>${fonte.trecho || ""}</p>
    `;

    fontesContainer.appendChild(card);
  });
}

async function enviarPergunta() {
  const pergunta = perguntaInput.value.trim();

  if (!pergunta) {
    statusDiv.textContent = "Digite uma pergunta antes de enviar.";
    resultadoCard.classList.add("hidden");
    return;
  }

  statusDiv.textContent = "Consultando o agente...";
  botaoEnviar.disabled = true;
  limparResultado();
  resultadoCard.classList.add("hidden");

  try {
    const resposta = await fetch(`${API_URL}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ pergunta })
    });

    if (!resposta.ok) {
      const textoErro = await resposta.text();
      throw new Error(`Erro HTTP ${resposta.status}: ${textoErro}`);
    }

    const dados = await resposta.json();

    respostaObjetiva.textContent = dados.resposta_objetiva || "";
    baseNormativaLegal.textContent = dados.base_normativa_legal || "";
    explicacaoPratica.textContent = dados.explicacao_pratica || "";
    limiteTecnico.textContent = dados.limite_tecnico || "";
    trechoNormativoExato.textContent = dados.trecho_normativo_exato || "";

    badgeConfianca.textContent = `Confiança: ${dados.nivel_confianca || "N/A"}`;
    badgeModo.textContent = `Modo: ${dados.modo_resposta || "desconhecido"}`;

    renderizarFontes(dados.fontes);

    resultadoCard.classList.remove("hidden");
    statusDiv.textContent = "Resposta carregada com sucesso.";
  } catch (erro) {
    console.error("Erro ao consultar API:", erro);
    statusDiv.textContent = `Erro ao consultar API: ${erro.message}`;
  } finally {
    botaoEnviar.disabled = false;
  }
}

botaoEnviar.addEventListener("click", enviarPergunta);

perguntaInput.addEventListener("keydown", function (event) {
  if (event.ctrlKey && event.key === "Enter") {
    enviarPergunta();
  }
});