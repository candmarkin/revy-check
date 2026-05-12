"""
Simple mock API that accepts a screenshot and returns JSON.
If query param `force=reprovado` it returns reprovado; otherwise returns ok.

Run: python mock_api.py
"""

from time import time
from flask import Flask, request, jsonify
from PIL import Image
import io
import pytesseract
import unicodedata
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

try:
    import tkinter as _tk
    from tkinter import messagebox as _messagebox
except Exception:
    _tk = None
    _messagebox = None

app = Flask(__name__)



class Step:
    def __init__(self, name, text, action, next_step=None):
        self.name = name
        self.text = text
        self.action = action
        self.next = next_step

steps = {
    'step1': Step('Seleção de país', ['este e o pais ou regiao correto?', 'regido correto?', 'regiao correto?'], ['enter'], next_step='step2'),
    'step2': Step('Layout', ['este é o layout de teclado'], ['enter'], next_step='step3'),
    'step3': Step('Layout 2', ['segundo layout'], ['enter'], next_step='step4'),
    'step4': Step('EULA', ['revise o contrato'], ['tab'], next_step='step5'),
    'step5': Step('Troca de hostname', ['nome ao dispositivo'], ['tab', 'enter'], next_step='step6'),
    'step6': Step('Final', ['uso pessoal', 'reprovado'], [], next_step='final'),
    'final': Step('Final step', ['uso pessoal'], [], next_step=None),
}

# Generic analyze (no step param): previous behavior
# lists of substrings that indicate approval or reproval
APPROVE_TEXTS = [
    'uso pessoal', 'aprovado', 'autorizad', 'valido', 'confirmado', 'aceito', 'vinculo'
]
REPROVE_TEXTS = [
    'reprov', 'reprovado', 'negad', 'recusad', 'nao aprovado', 'inadimpl', 'vencid'
]


def detect_text_result_from_image_bytes(image_bytes):
    """Extract text from image bytes using pytesseract.
    Returns the extracted text lowercased, or None if OCR failed / no text.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        print(f"Image opened for OCR: format={img.format}, size={img.size}, mode={img.mode}")
    except Exception as e:
        print(f"Failed to open image for OCR: {e}")
        return None

    try:
        # try Portuguese first if available; pytesseract will fallback to default
        text = pytesseract.image_to_string(img, lang='por')
        print(f"OCR text (Portuguese): {text}")
    except Exception:
        try:
            text = pytesseract.image_to_string(img)
            print(f"OCR text (default): {text}")
        except Exception as e:
            print(f"OCR failed to extract text: {e}")
            return None

    if not text:
        print("OCR found no text.")
        return None

    return text.lower()


@app.route('/analyze', methods=['POST'])
def analyze():
    force = request.args.get('force')
    step_param = request.args.get('step')
    # accept file but we don't need to save it
    f = request.files.get('screenshot')
    print(f"Received file: {f.filename if f else 'None'}, force={force}")

    # read the file bytes for processing
    image_bytes = None
    if f:
        try:
            # read into memory
            image_bytes = f.read()
        except Exception:
            image_bytes = None
            
    print(f"Received image bytes: {len(image_bytes) if image_bytes else 'None'}")

    # salva a imagem recebida para debug (opcional)
    if image_bytes:
        try:
            with open('received.png', 'wb') as fh:
                fh.write(image_bytes)
        except Exception:
            pass

    # Force param for testing
    if force == 'reprovado':
        return jsonify({'result': 'reprovado'})
    if force == 'ok':
        return jsonify({'result': 'ok'})
    # If a step was provided, try to match the step's expected text inside the image
    def _normalize(s):
        if s is None:
            return ''
        return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode().lower()

    def _text_matches_expected(ocr_norm_text, expected_text):
        expected_norm = _normalize(expected_text)
        if not expected_norm:
            return False
        if expected_norm in ocr_norm_text:
            return True

        # OCR can break phrases; accept when most expected words are present.
        words = [w for w in expected_norm.replace('?', ' ').replace('.',    
                                                                    ' ').split() if len(w) >= 3]
        if not words:
            return False
        present = sum(1 for w in words if w in ocr_norm_text)
        needed = max(1, len(words) - 1)
        return present >= needed

    if step_param:
        st = steps.get(step_param)
        if not st:
            return jsonify({'error': 'unknown step', 'step': step_param}), 400

        ocr_norm = ''
        if image_bytes:
            print("Attempting OCR for step matching...")
            ocr_text = detect_text_result_from_image_bytes(image_bytes)
            print(f"OCR text: {ocr_text}")
            
            if ocr_text:
                ocr_norm = _normalize(ocr_text)

        # Final step: classify only by approve/reprove token lists.
        # If no token is found, return unknown.
        if step_param == 'final':
            for token in REPROVE_TEXTS:
                if token in ocr_norm:
                    return jsonify({'result': 'reprovado', 'method': 'ocr', 'step': step_param, 'matched': token, 'action': st.action, 'next': None})
            for token in APPROVE_TEXTS:
                if token in ocr_norm:
                    return jsonify({'result': 'ok', 'method': 'ocr', 'step': step_param, 'matched': token, 'action': st.action, 'next': None})
            return jsonify({'result': 'unknown', 'method': 'ocr' if image_bytes else 'nofile', 'step': step_param, 'matched': None, 'action': st.action, 'next': None})

        # Non-final steps: only return "aguardando".
        # If expected text is found, include current step and next step so client can advance.
        for expected in st.text:
            if _text_matches_expected(ocr_norm, expected):
                print(f"Matched expected text: '{expected}' in OCR result for step '{step_param}'.")
                return jsonify({'result': 'aguardando', 'method': 'ocr', 'step': step_param, 'matched': expected, 'action': st.action, 'next': st.next})

        # Resync fallback: if current step does not match, try to detect any known step
        # from OCR so the client can recover progression.
        if ocr_norm:
            for step_key, step_obj in steps.items():
                if step_key == 'final':
                    continue
                for expected in step_obj.text:
                    if _text_matches_expected(ocr_norm, expected):
                        print(f"Resync matched '{expected}' for step '{step_key}' while current was '{step_param}'.")
                        return jsonify({
                            'result': 'aguardando',
                            'method': 'ocr-resync',
                            'step': step_key,
                            'matched': expected,
                            'action': step_obj.action,
                            'next': step_obj.next,
                        })

        return jsonify({'result': 'aguardando', 'method': 'ocr' if image_bytes else 'nofile', 'step': step_param, 'matched': None, 'action': [], 'next': None})
    if image_bytes:
        print("Attempting OCR-based detection...")
        ocr_text = detect_text_result_from_image_bytes(image_bytes)
        print(f"OCR text: {ocr_text}")
        if ocr_text:
            ocr_norm = _normalize(ocr_text)
            # try to find which step contains expected substrings
            for step_key, step in steps.items():
                for expected in step.text:
                    if _normalize(expected) in ocr_norm:
                        print(f"Matched expected text: '{expected}' in OCR result for step '{step_key}'.")
                        # determine quick result by scanning ocr text for known tokens
                        res = 'ok'
                        for token in REPROVE_TEXTS:
                            if token in ocr_norm:
                                res = 'reprovado'
                                break
                        if res != 'reprovado':
                            for token in APPROVE_TEXTS:
                                if token in ocr_norm:
                                    res = 'ok'
                                    break
                        # return matched step and next info
                        return jsonify({'result': res, 'method': 'ocr', 'step': step_key, 'matched': expected, 'next': step.next})

            # no step matched specifically, still try token-based generic classification
            for token in REPROVE_TEXTS:
                if token in ocr_norm:
                    return jsonify({'result': 'reprovado', 'method': 'ocr', 'matched': token})
            for token in APPROVE_TEXTS:
                if token in ocr_norm:
                    return jsonify({'result': 'ok', 'method': 'ocr', 'matched': token})
            return jsonify({'result': 'unknown', 'method': 'ocr', 'matched': None})

    if image_bytes is None:
        return jsonify({'result': 'unknown', 'method': 'nofile'})

    size = len(image_bytes)
    if size > 10 * 1024:
        return jsonify({'result': 'unknown', 'method': 'size'})
    return jsonify({'result': 'unknown', 'method': 'size'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
