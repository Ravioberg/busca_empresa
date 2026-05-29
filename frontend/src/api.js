const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ── Cache LRU em memória ───────────────────────────────────────────────────
const CACHE_MAX = 100;
const _cache = new Map();

function _cacheGet(key) {
  const v = _cache.get(key);
  if (v === undefined) return null;
  _cache.delete(key);
  _cache.set(key, v); // move para o fim (LRU touch)
  return v;
}

function _cacheSet(key, value) {
  if (_cache.size >= CACHE_MAX) _cache.delete(_cache.keys().next().value);
  _cache.set(key, value);
}

// ── AbortControllers — um por tipo de busca ───────────────────────────────
let _ctrlEmpresa = null;
let _ctrlSocio = null;

async function _get(path, signal) {
  const res = await fetch(`${BASE_URL}${path}`, signal ? { signal } : {});
  if (res.status === 404) return null;
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Erro ${res.status}`);
  }
  return res.json();
}

// ── Info ─────────────────────────────────────────────────────────────────

export async function fetchInfo() {
  try { return await _get("/api/v1/info", null); }
  catch { return null; }
}

// ── Empresa ───────────────────────────────────────────────────────────────

export async function buscarEmpresaPorCnpj(cnpj) {
  const cnpjLimpo = cnpj.replace(/\D/g, "");
  return _get(`/api/v1/empresa/${cnpjLimpo}`, null);
}

export async function buscarEmpresaPorNome(nome, skip = 0, limit = 20, knownTotal = 0) {
  const key = `e:${nome}:${skip}:${limit}`;
  const cached = _cacheGet(key);
  if (cached) return cached;

  _ctrlEmpresa?.abort();
  _ctrlEmpresa = new AbortController();

  try {
    const params = new URLSearchParams({ nome, skip, limit });
    if (knownTotal > 0) params.set("known_total", knownTotal);
    const data = await _get(`/api/v1/empresa/busca?${params}`, _ctrlEmpresa.signal);
    if (data !== null) _cacheSet(key, data);
    return data;
  } catch (err) {
    if (err.name === "AbortError") return null;
    throw err;
  }
}

// ── Sócio ──────────────────────────────────────────────────────────────────

export async function buscarPerfilSocio(cpf, nome) {
  const params = new URLSearchParams();
  if (cpf) params.set("cpf", cpf.replace(/\D/g, ""));
  if (nome) params.set("nome", nome);
  const key = `perfil:${params.toString()}`;
  const cached = _cacheGet(key);
  if (cached) return cached;

  _ctrlSocio?.abort();
  _ctrlSocio = new AbortController();

  try {
    const data = await _get(`/api/v1/socio/perfil?${params}`, _ctrlSocio.signal);
    if (data !== null) _cacheSet(key, data);
    return data;
  } catch (err) {
    if (err.name === "AbortError") return null;
    throw err;
  }
}

export async function buscarSocioPorNome(nome, skip = 0, limit = 20, knownTotal = 0) {
  const key = `sn:${nome}:${skip}:${limit}`;
  const cached = _cacheGet(key);
  if (cached) return cached;

  _ctrlSocio?.abort();
  _ctrlSocio = new AbortController();

  try {
    const params = new URLSearchParams({ nome, skip, limit });
    if (knownTotal > 0) params.set("known_total", knownTotal);
    const data = await _get(`/api/v1/socio/busca?${params}`, _ctrlSocio.signal);
    if (data !== null) _cacheSet(key, data);
    return data;
  } catch (err) {
    if (err.name === "AbortError") return null;
    throw err;
  }
}

export async function buscarEmpresaRede(cnpj) {
  const cnpjLimpo = cnpj.replace(/\D/g, "");
  const key = `rede:${cnpjLimpo}`;
  const cached = _cacheGet(key);
  if (cached) return cached;
  const data = await _get(`/api/v1/empresa/${cnpjLimpo}/rede`, null);
  if (data !== null) _cacheSet(key, data);
  return data;
}

export async function buscarGrafoEmpresa(cnpj, profundidade = 2) {
  const cnpjLimpo = cnpj.replace(/\D/g, "");
  const key = `grafoE:${cnpjLimpo}:${profundidade}`;
  const cached = _cacheGet(key);
  if (cached) return cached;
  const data = await _get(`/api/v1/empresa/${cnpjLimpo}/grafo?profundidade=${profundidade}`, null);
  if (data !== null) _cacheSet(key, data);
  return data;
}

export async function buscarGrafoSocio(cpf, nome, profundidade = 2) {
  const params = new URLSearchParams();
  if (cpf) params.set("cpf", cpf.replace(/\D/g, ""));
  if (nome) params.set("nome", nome);
  params.set("profundidade", profundidade);
  const key = `grafoS:${params.toString()}`;
  const cached = _cacheGet(key);
  if (cached) return cached;
  const data = await _get(`/api/v1/socio/grafo?${params}`, null);
  if (data !== null) _cacheSet(key, data);
  return data;
}

export async function buscarSocioPorCpf(cpf, skip = 0, limit = 20, knownTotal = 0) {
  const cpfLimpo = cpf.replace(/\D/g, "");
  const key = `sc:${cpfLimpo}:${skip}:${limit}`;
  const cached = _cacheGet(key);
  if (cached) return cached;

  _ctrlSocio?.abort();
  _ctrlSocio = new AbortController();

  try {
    const params = new URLSearchParams({ cpf: cpfLimpo, skip, limit });
    if (knownTotal > 0) params.set("known_total", knownTotal);
    const data = await _get(`/api/v1/socio/busca?${params}`, _ctrlSocio.signal);
    if (data !== null) _cacheSet(key, data);
    return data;
  } catch (err) {
    if (err.name === "AbortError") return null;
    throw err;
  }
}
