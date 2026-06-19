from typing import List

def chunka_con_titolo(testo: str,titolo_sezione: str,chunk_size: int = 400,overlap: int = 50) -> List[str]:
    """
    chunka_con_titolo divide un testo in chunk con sovrapposizione di 50 caratteri tra chucnk che appartengono alla stessa sezione 
    Args:
        testo:      Testo completo estratto dalla pagina web.
        titolo_sezione: Titolo e sezione del documento (usato come prefisso in ogni chunk).
        chunk_size: Dimensione di ogni chunk in parole (default 400).
        overlap:    Quante parole condividono due chunk contigui (default 50).
    Returns:
        Lista di stringhe, ognuna nella forma:
        "[Fonte: <titolo>]\\n<testo del chunk>"
    """
    if not testo or not testo.strip():
        return []

    words = testo.split()
    if not words:
        return []

    step = max(1, chunk_size - overlap)
    chunks: List[str] = []

    for i in range(0, len(words), step):
        chunk_words = words[i : i + chunk_size]
        chunk_text  = " ".join(chunk_words)

        if titolo_sezione:
            full_chunk = f"[Info: {titolo_sezione}]\n{chunk_text}"
        else:
            full_chunk = chunk_text

        chunks.append(full_chunk)

        if i + chunk_size >= len(words):
            break

    return chunks
