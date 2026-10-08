import os
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from PIL import Image
import time
import glob

from gtts import gTTS
from googletrans import Translator

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Asistente de Emergencia para Viajeros",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS limpios
st.markdown("""
<style>
.main {
    background-color: #f8f9fa;
}
.stButton>button {
    border-radius: 12px;
    font-weight: bold;
}
.custom-card {
    background-color: #ffffff;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    margin-bottom: 20px;
    border-left: 5px solid #ff4b4b;
}
</style>
""", unsafe_allow_html=True)

# BARRA LATERAL
with st.sidebar:
    st.markdown("### Guía Rápida")
    st.info(
        "1. Presiona el botón 'Escuchar 🎤'.\n"
        "2. Habla claramente cuando se active el micrófono.\n"
        "3. Selecciona tus configuraciones de idioma y acento.\n"
        "4. Haz clic en 'Traducir y Generar Audio'."
    )
    st.markdown("---")
    st.markdown("### Estado del Sistema")
    st.success("Modo de Emergencia: Activo")

# CABECERA PRINCIPAL
col_title, col_img = st.columns([3, 1])

with col_title:
    st.title("Asistente de Emergencia para Viajeros")
    st.markdown(
        "Transforma tu dispositivo en un **asistente médico y de seguridad en tiempo real**. "
        "Traduce al instante frases clave en situaciones de apuros (pérdida de pasaporte, farmacias, emergencias) "
        "a la lengua local en formato de voz alta y clara."
    )

with col_img:
    try:
        image = Image.open('sirena.jpg')
        st.image(image, width=200, caption="Asistente Turístico")
    except Exception:
        st.warning("Imagen 'sirena.jpg' no encontrada.")

st.markdown("---")

# RECONOCIMIENTO DE VOZ
st.markdown("### Reconocimiento de Voz")
st.write("Haz clic en el botón inferior para comenzar a hablar:")

stt_button = Button(label=" Escuchar 🎤", width=250, height=50)

stt_button.js_on_event("button_click", CustomJS(code="""
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'es-ES';
 
    recognition.onresult = function (e) {
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if (value != "") {
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        }
    }
    
    recognition.onend = function() {
        console.log("Reconocimiento detenido");
    }
    
    recognition.start();
"""))

result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0
)

# PROCESAMIENTO Y TRADUCCIÓN
if result and "GET_TEXT" in result:
    recognized_text = result.get("GET_TEXT")
    
    st.markdown(
        f"""
        <div class="custom-card">
            <h4>Texto Reconocido:</h4>
            <p style="font-size: 18px; color: #333;"><i>"{recognized_text}"</i></p>
        </div>
        """, 
        unsafe_allow_html=True
    )

    try:
        os.makedirs("temp", exist_ok=True)
    except Exception:
        pass

    translator = Translator()
    
    st.markdown("---")
    st.markdown("### Configuración de Traducción y Audio")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        in_lang = st.selectbox(
            "Lenguaje de Entrada",
            ("Inglés", "Francés", "Alemán", "Coreano", "Mandarín", "Japonés"),
            index=0
        )
    with col2:
        out_lang = st.selectbox(
            "Lenguaje de Salida (Local)",
            ("Inglés", "Francés", "Alemán", "Coreano", "Mandarín", "Japonés"),
            index=0
        )
    with col3:
        english_accent = st.selectbox(
            "Acento de Audio",
            ("Defecto", "Español", "Reino Unido", "Estados Unidos", "Canada", "Australia", "Irlanda", "Sudáfrica")
        )

    lang_map = {
        "Inglés": "en",
        "Francés": "fr",
        "Alemán": "de",
        "Coreano": "ko",
        "Mandarín": "zh-cn",
        "Japonés": "ja"
    }
    input_language = lang_map.get(in_lang, "en")
    output_language = lang_map.get(out_lang, "en")

    tld_map = {
        "Defecto": "com",
        "Español": "com.mx",
        "Reino Unido": "co.uk",
        "Estados Unidos": "com",
        "Canada": "ca",
        "Australia": "com.au",
        "Irlanda": "ie",
        "Sudáfrica": "co.za"
    }
    tld = tld_map.get(english_accent, "com")

    def text_to_speech(in_lang_code, out_lang_code, text_to_translate, tld_code):
        translation = translator.translate(text_to_translate, src=in_lang_code, dest=out_lang_code)
        trans_text = translation.text
        tts = gTTS(trans_text, lang=out_lang_code, tld=tld_code, slow=False)
        try:
            my_file_name = text_to_translate[0:20].strip().replace(" ", "_")
        except Exception:
            my_file_name = "audio"
        file_path = f"temp/{my_file_name}.mp3"
        tts.save(file_path)
        return my_file_name, trans_text

    display_output_text = st.checkbox("Mostrar texto traducido en pantalla", value=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("Traducir y Generar Audio", type="primary", use_container_width=True):
        with st.spinner("Traduciendo y generando audio..."):
            res_file, output_text = text_to_speech(input_language, output_language, recognized_text, tld)
            audio_file_path = f"temp/{res_file}.mp3"
            
            if os.path.exists(audio_file_path):
                with open(audio_file_path, "rb") as audio_file:
                    audio_bytes = audio_file.read()
                
                st.success("¡Traducción completada con éxito!")
                st.markdown("#### Audio Generado:")
                st.audio(audio_bytes, format="audio/mp3", start_time=0)
            
                if display_output_text:
                    st.markdown(
                        f"""
                        <div class="custom-card" style="border-left-color: #28a745;">
                            <h4>Traducción Local:</h4>
                            <p style="font-size: 18px; color: #333;"><b>{output_text}</b></p>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
            else:
                st.error("Hubo un error al generar el archivo de audio.")

    def remove_files(n):
        mp3_files = glob.glob("temp/*mp3")
        if len(mp3_files) != 0:
            now = time.time()
            n_days = n * 86400
            for f in mp3_files:
                try:
                    if os.stat(f).st_mtime < now - n_days:
                        os.remove(f)
                except Exception:
                    pass

    remove_files(7)
