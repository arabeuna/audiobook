import os
import re
import sys
import pdfplumber
import pytesseract
from PIL import Image
from tqdm import tqdm

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
os.environ['TESSDATA_PREFIX'] = os.path.join(os.environ['LOCALAPPDATA'], 'Tesseract-OCR', 'tessdata')

PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(PASTA_PROJETO, '365 Reflexões Estoicas.pdf')
PASTA_TEXTO = os.path.join(PASTA_PROJETO, 'reflexoes_texto')
PASTA_AUDIO = os.path.join(PASTA_PROJETO, 'reflexoes_audio')
ARQUIVO_OCR = os.path.join(PASTA_PROJETO, 'texto_completo_ocr.txt')

def extrair_texto_pdf():
    print("Extraindo texto do PDF via OCR...")
    pdf = pdfplumber.open(PDF_PATH)
    paginas_texto = []
    for pg in tqdm(range(len(pdf.pages))):
        page = pdf.pages[pg]
        pil_img = page.to_image(resolution=200).original
        text = pytesseract.image_to_string(pil_img, lang='por')
        paginas_texto.append(text)

    texto_completo = '\n'.join(
        f'--- PAGE {pg+1} ---\n{texto}'
        for pg, texto in enumerate(paginas_texto)
    )
    pdf.close()

    with open(ARQUIVO_OCR, 'w', encoding='utf-8') as f:
        f.write(texto_completo)
    return texto_completo

def limpar_texto(texto):
    texto = re.sub(r'[_|]+', '', texto)
    texto = re.sub(r'\bGN\b', '', texto)
    texto = re.sub(r'^\d+\s*---\s*', '', texto, flags=re.MULTILINE)
    texto = re.sub(r'\n{4,}', '\n\n\n', texto)
    texto = re.sub(r'^[-\d\/\(\)\[\]\{\}]{1,10}\s*', '', texto)
    return texto.strip()

def extrair_reflexoes(texto_completo):
    sections = texto_completo.split('--- PAGE ')
    sections = sections[1:]

    texto_reflexoes = []
    for sec in sections:
        m = re.match(r'(\d+) ---\n', sec)
        if m and int(m.group(1)) >= 24:
            texto_reflexoes.append(sec[m.end():])

    texto_unido = '\n'.join(texto_reflexoes)

    author_pat = re.compile(
        r'^\s*(?:Marco Aur[ée]lio|S[éeê]neca|Epiteto|Epicteto|L[áa]cio)[,;]',
        re.IGNORECASE
    )

    reflexoes = []
    buf = []
    for line in texto_unido.split('\n'):
        s = line.strip()
        if not s:
            buf.append('')
            continue
        if author_pat.match(s):
            if buf:
                buf.append(line)
                reflexoes.append('\n'.join(buf))
                buf = []
            else:
                buf = [line]
        else:
            buf.append(line)

    if buf:
        reflexoes.append('\n'.join(buf))

    result = []
    for i, ref in enumerate(reflexoes, 1):
        ref = limpar_texto(ref)
        if ref and len(ref) > 20:
            result.append((i, ref))

    return result

def salvar_reflexoes(reflexoes):
    os.makedirs(PASTA_TEXTO, exist_ok=True)
    paths = []
    for num, texto in reflexoes:
        nome = f'reflexao_{num:03d}.txt'
        path = os.path.join(PASTA_TEXTO, nome)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(texto)
        paths.append((nome, texto))
    return paths

def gerar_audio_pyttsx3(reflexoes):
    import pyttsx3

    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)

    for v in engine.getProperty('voices'):
        if 'portuguese' in v.name.lower() or 'maria' in v.name.lower():
            engine.setProperty('voice', v.id)
            print(f"Voz: {v.name}")
            break

    os.makedirs(PASTA_AUDIO, exist_ok=True)
    for nome, texto in tqdm(reflexoes, desc="Audios (pyttsx3)"):
        path = os.path.join(PASTA_AUDIO, nome.replace('.txt', '.mp3'))
        engine.save_to_file(texto, path)
        engine.runAndWait()

    engine.stop()

def gerar_audio_edge(reflexoes):
    import asyncio
    import edge_tts

    voz = 'pt-BR-FranciscaNeural'
    print(f"Voz: {voz}")
    os.makedirs(PASTA_AUDIO, exist_ok=True)

    async def gerar():
        for nome, texto in tqdm(reflexoes, desc="Audios (edge-tts)"):
            path = os.path.join(PASTA_AUDIO, nome.replace('.txt', '.mp3'))
            communicate = edge_tts.Communicate(texto, voz)
            await communicate.save(path)

    asyncio.run(gerar())

def gerar_audio(reflexoes, engine='edge'):
    if engine == 'pyttsx3':
        gerar_audio_pyttsx3(reflexoes)
    else:
        gerar_audio_edge(reflexoes)

def main():
    if not os.path.exists(PDF_PATH):
        print(f"ERRO: PDF nao encontrado: {PDF_PATH}")
        sys.exit(1)

    if not os.path.exists(ARQUIVO_OCR):
        texto = extrair_texto_pdf()
    else:
        with open(ARQUIVO_OCR, 'r', encoding='utf-8') as f:
            texto = f.read()
        print("Usando OCR ja extraido.")

    print("Identificando reflexoes...")
    reflexoes = extrair_reflexoes(texto)
    print(f"Encontradas {len(reflexoes)} reflexoes (esperado ~365)")

    if len(reflexoes) < 300:
        print("AVISO: Muitas reflexoes podem estar faltando. Reexecute sem o arquivo OCR para re-extrair.")
        return

    paths = salvar_reflexoes(reflexoes)
    print(f"Textos salvos em: {PASTA_TEXTO}")

    for nome, texto in paths[:3]:
        print(f"\n--- {nome} ---")
        print(texto[:120])

    engine = 'edge'
    if '--pyttsx3' in sys.argv:
        engine = 'pyttsx3'

    gerar = '--audio' in sys.argv
    if not gerar:
        try:
            resp = input(f"\nGerar audios com {engine}? (s/N): ")
            gerar = resp.lower() == 's'
        except EOFError:
            pass

    if gerar:
        print(f"Gerando audios ({engine})...")
        gerar_audio(paths, engine)
        print(f"Concluido! Audios em: {PASTA_AUDIO}")
    else:
        print(f"Para gerar audios, use: python gerar_audiobook.py --audio")
        print(f"  edge-tts (rapido): python gerar_audiobook.py --audio")
        print(f"  pyttsx3 (offline): python gerar_audiobook.py --audio --pyttsx3")

if __name__ == '__main__':
    main()
