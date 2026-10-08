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

# Estilos CSS personalizados para darle un toque más moderno, elegante y limpio
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        border-radius: 12px;
        font-weight: bold;
    }
    .css-1v0mbdj {
        border-radius: 10px;
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

# ---------------------------------------------------------
# BARRA LATERAL
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ✈️ Guía Rápida")
    st.info(
        "1. Presiona el botón **'Escuchar 🎤'**.\n"
        "2. Habla claramente cuando se active el micrófono.\n"
        "3. Selecciona tus configuraciones de idioma y acento.\n"
        "4. Haz clic en **'Convertir y Traducir'**."
    )
    st.markdown("---")
    st.markdown("### 🔒 Estado del Sistema")
    st.success("Modo de Emergencia: Activo 🟢")

# ---------------------------------------------------------
# CABECERA PRINCIPAL
# ---------------------------------------------------------
col_title, col_img = st.columns([3, 1])

with col_title:
    st.title("🚨 Asistente de Emergencia para Viajeros")
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
        st.warning("Imagen 'sirena.jpg' no encontrada en el directorio.")

st.markdown("---")

# ---------------------------------------------------------
# SECCIÓN DE RECONOCIMIENTO DE VOZ
# ---------------------------------------------------------
st.markdown("### 🎙️ Reconocimiento de Voz")
st.write("Haz clic en el botón inferior para comenzar a hablar:")

# Botón Bokeh para reconocimiento de voz
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

# ---------------------------------------------------------
# PROCESAMIENTO Y TRADUCCIÓN
# ---------------------------------------------------------
if result and "GET_TEXT" in result:
    recognized_text = result.get("GET_TEXT")
    
    with st.container():
        st.markdown(
            f"""
            <div class="custom-card">
                <h4>📝 Texto Reconocido:</h4>
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
    st.markdown("### ⚙️ Configuración de Traducción y Audio")
    
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

    # Mapeo de lenguajes
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

    # Mapeo de acentos (TLD)
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
    
    if st.button("🔊 Traducir y Generar Audio", type="primary", use_container_width=True):
        with st.spinner("Traduciendo y generando audio... Por favor espera."):
            res_file, output_text = text_to_speech(input_language, output_language, recognized_text, tld)
            audio_file_path = f"temp/{res_file}.mp3"
            
            if os.path.exists(audio_file_path):
                with open(audio_file_path, "rb") as audio_file:
                    audio_bytes = audio_file.read()
                
                st.success("¡Traducción completada con éxito!")
                st.markdown("#### 🎧 Audio Generado:")
                st.audio(audio_bytes, format="audio/mp3", start_time=0)
            
                if display_output_text:
                    st.markdown(
                        f"""
                        <div class="custom-card" style="border-left-color: #28a745;">
                            <h4>🌐 Traducción Local:</h4>
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
                except Exception as e:
                    print("Error eliminando archivo:", e)

    remove_files(7)        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado principal con diseño limpio
st.markdown('<p class="main-header">🚨 Asistente de Conversación para Viajeros</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Traductor en tiempo real para situaciones de emergencia, asistencia médica y seguridad en el extranjero.</p>', 
    unsafe_allow_html=True
)

st.markdown("---")

# 3. Diseño en columnas para la vista principal
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    try:
        image = Image.open('sirena.jpg')
        st.image(image, use_container_width=True)
    except:
        st.info("💡 Consejo: Añade una imagen llamada 'sirena.jpg' para personalizar el diseño.")
    
    st.markdown("### 📋 Instrucciones")
    st.info(
        "1. Selecciona los idiomas en la **barra lateral**.\n"
        "2. Presiona el botón de escucha.\n"
        "3. Habla claramente lo que deseas traducir.\n"
        "4. Reproduce el audio generado para comunicarte."
    )

with col2:
    st.markdown("### 🎙️ Panel de Grabación")
    st.write("Toca el botón y habla la frase que necesitas traducir de inmediato:")
    
    # Botón de Bokeh para reconocimiento de voz
    stt_button = Button(label=" Escuchar 🎤", width=300, height=50)
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
            if ( value != "") {
                document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
            }
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

# 4. Configuración en la barra lateral
with st.sidebar:
    st.header("⚙️ Configuración")
    st.write("Personaliza los parámetros de traducción y voz.")
    st.markdown("---")
    
    in_lang = st.selectbox(
        "Idioma de Entrada (Lo que hablas)",
        ("Español", "Inglés", "Francés", "Alemán", "Coreano", "Mandarín", "Japonés"),
    )
    
    out_lang = st.selectbox(
        "Idioma de Salida (Traducción local)",
        ("Inglés", "Francés", "Alemán", "Coreano", "Mandarín", "Japonés", "Español"),
    )
    
    english_accent = st.selectbox(
        "Acento del Audio (si aplica)",
        (
            "Defecto",
            "Español",
            "Reino Unido",
            "Estados Unidos",
            "Canada",
            "Australia",
            "Irlanda",
            "Sudáfrica",
        ),
    )
    
    display_output_text = st.checkbox("Mostrar texto traducido en pantalla", value=True)

# Mapeo de idiomas para Googletrans
lang_mapping = {
    "Español": "es",
    "Inglés": "en",
    "Francés": "fr",
    "Alemán": "de",
    "Coreano": "ko",
    "Mandarín": "zh-cn",
    "Japonés": "ja"
}

input_language = lang_mapping.get(in_lang, "es")
output_language = lang_mapping.get(out_lang, "en")

# Mapeo de acentos para gTTS
tld_mapping = {
    "Defecto": "com",
    "Español": "com.mx",
    "Reino Unido": "co.uk",
    "Estados Unidos": "com",
    "Canada": "ca",
    "Australia": "com.au",
    "Irlanda": "ie",
    "Sudáfrica": "co.za"
}
tld = tld_mapping.get(english_accent, "com")

# 5. Procesamiento de resultados
if result and "GET_TEXT" in result:
    spoken_text = result.get("GET_TEXT")
    
    with st.container():
        st.markdown("---")
        st.subheader("💬 Resultado de la Traducción")
        
        # Tarjeta visual para el texto detectado
        st.markdown(f"**Texto reconocido:** *\"{spoken_text}\"*")
        
        try:
            os.mkdir("temp")
        except:
            pass
        
        translator = Translator()
        
        def text_to_speech(in_lang_code, out_lang_code, text_to_translate, target_tld):
            translation = translator.translate(text_to_translate, src=in_lang_code, dest=out_lang_code)
            trans_text = translation.text
            tts = gTTS(trans_text, lang=out_lang_code, tld=target_tld, slow=False)
            try:
                my_file_name = text_to_translate[0:20].strip().replace(" ", "_")
            except:
                my_file_name = "audio"
            file_path = f"temp/{my_file_name}.mp3"
            tts.save(file_path)
            return my_file_name, trans_text

        with st.spinner("Traduciendo y generando audio..."):
            res_file, output_text = text_to_speech(input_language, output_language, spoken_text, tld)
            audio_file = open(f"temp/{res_file}.mp3", "rb")
            audio_bytes = audio_file.read()
            
        # Reproductor de audio estilizado y texto de salida
        st.audio(audio_bytes, format="audio/mp3", start_time=0)
        
        if display_output_text:
            st.success(f"**Traducción ({out_lang}):** {output_text}")

# 6. Limpieza automática de archivos temporales antiguos
def remove_files(n):
    mp3_files = glob.glob("temp/*mp3")
    if len(mp3_files) != 0:
        now = time.time()
        n_days = n * 86400
        for f in mp3_files:
            if os.stat(f).st_mtime < now - n_days:
                try:
                    os.remove(f)
                except:
                    pass

remove_files(7)        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado principal con diseño limpio
st.markdown('<p class="main-header">🚨 Asistente de Conversación para Viajeros</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Traductor en tiempo real para situaciones de emergencia, asistencia médica y seguridad en el extranjero.</p>', 
    unsafe_allow_html=True
)

st.markdown("---")

# 3. Diseño en columnas para la vista principal
col1, col2 = st.columns([1, 2], gap="large")

with col1:
    try:
        image = Image.open('sirena.jpg')
        st.image(image, use_container_width=True)
    except:
        st.info("💡 Consejo: Añade una imagen llamada 'sirena.jpg' para personalizar el diseño.")
    
    st.markdown("### 📋 Instrucciones")
    st.info(
        "1. Selecciona los idiomas en la **barra lateral**.\n"
        "2. Presiona el botón de escucha.\n"
        "3. Habla claramente lo que deseas traducir.\n"
        "4. Reproduce el audio generado para comunicarte."
    )

with col2:
    st.markdown("### 🎙️ Panel de Grabación")
    st.write("Toca el botón y habla la frase que necesitas traducir de inmediato:")
    
    # Botón de Bokeh para reconocimiento de voz
    stt_button = Button(label=" Escuchar 🎤", width=300, height=50)
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
            if ( value != "") {
                document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
            }
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

# 4. Configuración en la barra lateral
with st.sidebar:
    st.header("⚙️ Configuración")
    st.write("Personaliza los parámetros de traducción y voz.")
    st.markdown("---")
    
    in_lang = st.selectbox(
        "Idioma de Entrada (Lo que hablas)",
        ("Español", "Inglés", "Francés", "Alemán", "Coreano", "Mandarín", "Japonés"),
    )
    
    out_lang = st.selectbox(
        "Idioma de Salida (Traducción local)",
        ("Inglés", "Francés", "Alemán", "Coreano", "Mandarín", "Japonés", "Español"),
    )
    
    english_accent = st.selectbox(
        "Acento del Audio (si aplica)",
        (
            "Defecto",
            "Español",
            "Reino Unido",
            "Estados Unidos",
            "Canada",
            "Australia",
            "Irlanda",
            "Sudáfrica",
        ),
    )
    
    display_output_text = st.checkbox("Mostrar texto traducido en pantalla", value=True)

# Mapeo de idiomas para Googletrans
lang_mapping = {
    "Español": "es",
    "Inglés": "en",
    "Francés": "fr",
    "Alemán": "de",
    "Coreano": "ko",
    "Mandarín": "zh-cn",
    "Japonés": "ja"
}

input_language = lang_mapping.get(in_lang, "es")
output_language = lang_mapping.get(out_lang, "en")

# Mapeo de acentos para gTTS
tld_mapping = {
    "Defecto": "com",
    "Español": "com.mx",
    "Reino Unido": "co.uk",
    "Estados Unidos": "com",
    "Canada": "ca",
    "Australia": "com.au",
    "Irlanda": "ie",
    "Sudáfrica": "co.za"
}
tld = tld_mapping.get(english_accent, "com")

# 5. Procesamiento de resultados
if result and "GET_TEXT" in result:
    spoken_text = result.get("GET_TEXT")
    
    with st.container():
        st.markdown("---")
        st.subheader("💬 Resultado de la Traducción")
        
        # Tarjeta visual para el texto detectado
        st.markdown(f"**Texto reconocido:** *\"{spoken_text}\"*")
        
        try:
            os.mkdir("temp")
        except:
            pass
        
        translator = Translator()
        
        def text_to_speech(in_lang_code, out_lang_code, text_to_translate, target_tld):
            translation = translator.translate(text_to_translate, src=in_lang_code, dest=out_lang_code)
            trans_text = translation.text
            tts = gTTS(trans_text, lang=out_lang_code, tld=target_tld, slow=False)
            try:
                my_file_name = text_to_translate[0:20].strip().replace(" ", "_")
            except:
                my_file_name = "audio"
            file_path = f"temp/{my_file_name}.mp3"
            tts.save(file_path)
            return my_file_name, trans_text

        with st.spinner("Traduciendo y generando audio..."):
            res_file, output_text = text_to_speech(input_language, output_language, spoken_text, tld)
            audio_file = open(f"temp/{res_file}.mp3", "rb")
            audio_bytes = audio_file.read()
            
        # Reproductor de audio estilizado y texto de salida
        st.audio(audio_bytes, format="audio/mp3", start_time=0)
        
        if display_output_text:
            st.success(f"**Traducción ({out_lang}):** {output_text}")

# 6. Limpieza automática de archivos temporales antiguos
def remove_files(n):
    mp3_files = glob.glob("temp/*mp3")
    if len(mp3_files) != 0:
        now = time.time()
        n_days = n * 86400
        for f in mp3_files:
            if os.stat(f).st_mtime < now - n_days:
                try:
                    os.remove(f)
                except:
                    pass

remove_files(7)
var recognition = new webkitSpeechRecognition();
    recognition.continuous = false;  // Cambia a false
    recognition.interimResults = true;
    recognition.lang = 'es-ES';  // Puedes ajustar el idioma
 
    recognition.onresult = function (e) {
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if ( value != "") {
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
    debounce_time=0)

if result:
    if "GET_TEXT" in result:
        st.write(result.get("GET_TEXT"))
    try:
        os.mkdir("temp")
    except:
        pass
    st.title("Texto a Audio")
    translator = Translator()
    
    text = str(result.get("GET_TEXT"))
    in_lang = st.selectbox(
        "Selecciona el lenguaje de Entrada",
        ("Inglés", "Francés", "Alemán", "Coreano", "Mandarín", "Japonés"),
    )
    if in_lang == "Inglés":
        input_language = "en"
    elif in_lang == "Francés":
        input_language = "fr"
    elif in_lang == "Alemán":
        input_language = "de"
    elif in_lang == "Coreano":
        input_language = "ko"
    elif in_lang == "Mandarín":
        input_language = "zh-cn"
    elif in_lang == "Japonés":
        input_language = "ja"
    
    out_lang = st.selectbox(
        "Selecciona el lenguaje de salida",
        ("Inglés", "Francés", "Alemán", "Coreano", "Mandarín", "Japonés"),
    )
    if out_lang == "Inglés":
        output_language = "en"
    elif out_lang == "Francés":
        output_language = "fr"
    elif out_lang == "Alemán":
        output_language = "de"
    elif out_lang == "Coreano":
        output_language = "ko"
    elif out_lang == "Mandarín":
        output_language = "zh-cn"
    elif out_lang == "Japonés":
        output_language = "ja"
    
    english_accent = st.selectbox(
        "Selecciona el acento",
        (
            "Defecto",
            "Español",
            "Reino Unido",
            "Estados Unidos",
            "Canada",
            "Australia",
            "Irlanda",
            "Sudáfrica",
        ),
    )
    
    if english_accent == "Defecto":
        tld = "com"
    elif english_accent == "Español":
        tld = "com.mx"
    
    elif english_accent == "Reino Unido":
        tld = "co.uk"
    elif english_accent == "Estados Unidos":
        tld = "com"
    elif english_accent == "Canada":
        tld = "ca"
    elif english_accent == "Australia":
        tld = "com.au"
    elif english_accent == "Irlanda":
        tld = "ie"
    elif english_accent == "Sudáfrica":
        tld = "co.za"
    
    
    def text_to_speech(input_language, output_language, text, tld):
        translation = translator.translate(text, src=input_language, dest=output_language)
        trans_text = translation.text
        tts = gTTS(trans_text, lang=output_language, tld=tld, slow=False)
        try:
            my_file_name = text[0:20]
        except:
            my_file_name = "audio"
        tts.save(f"temp/{my_file_name}.mp3")
        return my_file_name, trans_text
    
    
    display_output_text = st.checkbox("Mostrar el texto")
    
    if st.button("convertir"):
        result, output_text = text_to_speech(input_language, output_language, text, tld)
        audio_file = open(f"temp/{result}.mp3", "rb")
        audio_bytes = audio_file.read()
        st.markdown(f"## Tú audio:")
        st.audio(audio_bytes, format="audio/mp3", start_time=0)
    
        if display_output_text:
            st.markdown(f"## Texto de salida:")
            st.write(f" {output_text}")
    
    
    def remove_files(n):
        mp3_files = glob.glob("temp/*mp3")
        if len(mp3_files) != 0:
            now = time.time()
            n_days = n * 86400
            for f in mp3_files:
                if os.stat(f).st_mtime < now - n_days:
                    os.remove(f)
                    print("Deleted ", f)

    remove_files(7)
           


        
    



        
    


