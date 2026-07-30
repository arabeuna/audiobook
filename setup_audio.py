import os, shutil, sys

# Copia os MP3s gerados para a pasta audio/ do player
origem = r'D:\AUDIOBOOK\LIVROS\CLASSIFICAÇÃO\AUTO AJUDA\reflexoes_audio'
destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audio')

os.makedirs(destino, exist_ok=True)

files = sorted(os.listdir(origem))
copiados = 0
for f in files:
    if f.endswith('.mp3'):
        shutil.copy2(os.path.join(origem, f), os.path.join(destino, f))
        copiados += 1

print(f'{copiados} arquivos MP3 copiados para {destino}')
print(f'Tamanho total: {sum(os.path.getsize(os.path.join(destino,f)) for f in os.listdir(destino))/1024/1024:.0f} MB')
