const SENHA = 'estoico365';
const STORAGE_KEY = 'estoic_player';

let reflexoes = [];
let indiceAtual = 0;
let listaVisivel = true;

// Carregar manifest das reflexões
async function gerarReflexoes() {
  try {
    const resp = await fetch('audio-manifest.json');
    reflexoes = await resp.json();
  } catch {
    // Fallback: gerar sequencial da pasta audio/
    for (let i = 1; i <= 350; i++) {
      const num = String(i).padStart(3, '0');
      reflexoes.push({
        num: i,
        label: `Reflexão ${i}`,
        src: `audio/reflexao_${num}.mp3`
      });
    }
  }
}

// --- Login ---
document.getElementById('btn-entrar').addEventListener('click', () => {
  const input = document.getElementById('senha-input');
  if (input.value === SENHA) {
    localStorage.setItem('estoic_logado', '1');
    mostrarApp();
  } else {
    document.getElementById('login-erro').textContent = 'Senha incorreta';
  }
});

document.getElementById('senha-input').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') document.getElementById('btn-entrar').click();
});

function mostrarApp() {
  document.getElementById('login-screen').classList.add('hidden');
  document.getElementById('app-screen').classList.remove('hidden');
  carregarProgresso();
  renderizarLista();
  carregarReflexao(indiceAtual);
}

// --- Player ---
const player = document.getElementById('player');

function carregarReflexao(idx) {
  if (idx < 0 || idx >= reflexoes.length) return;
  indiceAtual = idx;
  const ref = reflexoes[idx];

  document.getElementById('ref-num').textContent = `#${ref.num}`;
  document.getElementById('progresso-label').textContent = `${idx + 1} / ${reflexoes.length}`;

  // Carregar texto da reflexão
  const numStr = String(ref.num).padStart(3, '0');
  fetch(`textos/reflexao_${numStr}.txt`)
    .then(r => r.text())
    .then(txt => {
      document.getElementById('ref-texto').textContent = txt;
    })
    .catch(() => {
      document.getElementById('ref-texto').textContent = '';
    });

  // Tenta carregar o áudio
  player.src = ref.src;
  player.load();

  // Atualiza lista
  document.querySelectorAll('.item-reflexao').forEach(el => el.classList.remove('ativa'));
  const item = document.querySelector(`[data-idx="${idx}"]`);
  if (item) {
    item.classList.add('ativa');
    item.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }

  salvarProgresso();
}

player.addEventListener('ended', () => {
  marcarOuvida(indiceAtual);
  if (indiceAtual < reflexoes.length - 1) {
    carregarReflexao(indiceAtual + 1);
    player.play().catch(() => {});
  }
});

document.getElementById('btn-anterior').addEventListener('click', () => {
  if (indiceAtual > 0) carregarReflexao(indiceAtual - 1);
});

document.getElementById('btn-proximo').addEventListener('click', () => {
  if (indiceAtual < reflexoes.length - 1) carregarReflexao(indiceAtual + 1);
});

// Teclas de atalho
document.addEventListener('keydown', (e) => {
  if (localStorage.getItem('estoic_logado') !== '1') return;
  if (e.key === 'ArrowLeft') document.getElementById('btn-anterior').click();
  if (e.key === 'ArrowRight') document.getElementById('btn-proximo').click();
  if (e.key === ' ') { e.preventDefault(); player.paused ? player.play() : player.pause(); }
});

// --- Lista ---
document.getElementById('btn-toggle-lista').addEventListener('click', () => {
  listaVisivel = !listaVisivel;
  document.getElementById('lista-container').classList.toggle('hidden', !listaVisivel);
});

function renderizarLista(filtro = '') {
  const container = document.getElementById('lista-reflexoes');
  container.innerHTML = '';
  const ouvidas = getOuvidas();

  const filtradas = reflexoes.filter(r =>
    !filtro || r.label.toLowerCase().includes(filtro.toLowerCase())
  );

  filtradas.forEach(r => {
    const div = document.createElement('div');
    div.className = 'item-reflexao' + (r.num - 1 === indiceAtual ? ' ativa' : '');
    div.dataset.idx = r.num - 1;

    const ouvida = ouvidas.has(r.num);
    div.innerHTML = `
      <span class="num">#${r.num}</span>
      <span class="texto">${r.label}</span>
      <span class="check">${ouvida ? '✅' : ''}</span>
    `;

    div.addEventListener('click', () => carregarReflexao(r.num - 1));
    container.appendChild(div);
  });
}

document.getElementById('busca').addEventListener('input', (e) => {
  renderizarLista(e.target.value);
});

// --- Progresso ---
function getOuvidas() {
  try {
    const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    return new Set(data.ouvidas || []);
  } catch { return new Set(); }
}

function marcarOuvida(idx) {
  const ref = reflexoes[idx];
  if (!ref) return;
  const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
  const ouvidas = new Set(data.ouvidas || []);
  ouvidas.add(ref.num);
  data.ouvidas = [...ouvidas];
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  renderizarLista(document.getElementById('busca').value);
}

function carregarProgresso() {
  try {
    const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    indiceAtual = data.ultimo || 0;
  } catch { indiceAtual = 0; }
}

function salvarProgresso() {
  try {
    const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    data.ultimo = indiceAtual;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {}
}

// --- Toast ---
function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('visivel');
  setTimeout(() => el.classList.remove('visivel'), 2000);
}

// --- Sair ---
document.getElementById('btn-sair').addEventListener('click', () => {
  localStorage.removeItem('estoic_logado');
  document.getElementById('app-screen').classList.add('hidden');
  document.getElementById('login-screen').classList.remove('hidden');
  document.getElementById('senha-input').value = '';
});

// --- Init ---
(async () => {
  await gerarReflexoes();
  if (localStorage.getItem('estoic_logado') === '1') {
    mostrarApp();
  }
})();

// Registrar service worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js');
}
