
def empathic_response(user: str, text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["tired", "exhausted", "sleepy", "yorgun", "bitkin", "uykusuz"]):
        return f"{user}, biraz dinlenmek ister misin? Istersen su icmeyi de hatirlatabilirim."
    if any(k in t for k in ["sad", "upset", "bad", "uzgun", "moralim bozuk", "kotu"]):
        return f"{user}, uzgun oldugunu duydum. Yanindayim. Kisa bir nefes egzersizi deneyelim mi?"
    if any(k in t for k in ["happy", "good", "great", "mutlu", "iyi", "harika"]):
        return f"{user}, bu harika. Bugun baska ne yapmami istersin?"
    return f"{user}, anladim. Sana nasil yardim edebilirim?"
