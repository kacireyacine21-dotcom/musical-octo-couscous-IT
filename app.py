import base64
import json
import os
import random
import re
import uuid
from http import client as http_client
from urllib import error, request as urllib_request

from dotenv import load_dotenv
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request as flask_request,
    session,
    url_for,
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'it-assistant-secret-key-2026')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.after_request
def no_cache(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


VALID_USERS = {
    'admin': '123456',
    'it': 'it123',
}


def render_login_page(error=None):
    return render_template('login.html', error=error)


def render_register_page(error=None):
    return render_template('register.html', error=error)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def extract_name(message: str):
    text = (message or '').strip()
    if not text:
        return None

    patterns = [
        r'أسمي\s+([\w\u0600-\u06FF]+)',
        r'اسمي\s+([\w\u0600-\u06FF]+)',
        r'انا\s+اسمي\s+([\w\u0600-\u06FF]+)',
        r'أنا\s+اسمي\s+([\w\u0600-\u06FF]+)',
        r'أنا\s+([\w\u0600-\u06FF]+)',
        r'انا\s+([\w\u0600-\u06FF]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            name = match.group(1).strip(' .,!؟')
            if name and len(name) >= 2:
                return name

    return None


def local_response(message: str, user_name: str | None = None) -> str | None:
    text = (message or '').strip()
    if not text:
        return None

    normalized = text.lower()
    display_name = user_name or 'صديقي'

    if 'اسمك' in normalized or 'من انت' in normalized or 'من أنت' in normalized:
        options = [
            'أنا IT، مساعدك الذكي. طورت من قبل كـ مطور ويب ناشئ، وأستطيع مساعدتك في البرمجة، مواقع الويب، والمشاريع بشكل عملي وواضح.',
            'أنا IT، مساعدك الذكي. طورت من قبل كـ مطور ويب ناشئ، وأساعدك في بناء المشاريع، حل المشكلات، والتعلم خطوة بخطوة.',
            'أنا IT، مساعدك الذكي، وقد تم تطويري من قبل مطور ويب ناشئ، وأستطيع مساعدتك في البرمجة، تصميم المواقع، والتطوير بشكل مبسط.',
        ]
        return random.choice(options)

    if any(word in normalized for word in ['طالب', 'ثانوي', 'ناشئ', 'مطور ويب', 'تطوير مواقع', 'مطور الويب', 'ويب سايت', 'مواقع']):
        if 'أنا' in text or 'انا' in text or 'انـا' in text:
            options = [
                'أحسنت، هذا بداية ممتازة. أنت الآن في الطريق الصحيح، وأنا IT، مساعدك الذكي، وقد طورت من قبل كـ مطور ويب ناشئ، وأستطيع مساعدتك في التعلم، المشاريع، والتطوير خطوة بخطوة.',
                'هذا رائع، بداية قوية جدًا. أنا IT، مساعدك الذكي، وقد طورت من قبل كـ مطور ويب ناشئ، وسأساعدك في تنظيم مشروعك وتطوير مهاراتك بشكل عملي.',
                'بداية ممتازة، وأنت على الطريق الصحيح. أنا IT، مساعدك الذكي، وقد طورت من قبل كـ مطور ويب ناشئ، وسأساعدك في المشاريع والدروس بطريقة مريحة وواضحة.',
            ]
            return random.choice(options)

    if 'اسمي' in normalized or 'أنا اسمي' in normalized or 'انا اسمي' in normalized or 'أسمي' in normalized:
        detected_name = extract_name(text) or display_name
        options = [
            f'مرحبًا {detected_name}، سعيد بمعرفتك. أنا IT، مساعدك الذكي. طورت من قبل كـ مطور ويب ناشئ، وأستطيع مساعدتك في الدروس، المشاريع، البرمجة، وتطوير المواقع بشكل عملي وواضح.',
            f'مرحبًا {detected_name}، سعيد بمعرفتك. أنا IT، مساعدك الذكي، وقد طورت من قبل كـ مطور ويب ناشئ، وسأساعدك في التعلم وبناء مشاريعك بسهولة.',
            f'أهلاً {detected_name}، أنا IT، مساعدك الذكي. طورت من قبل كـ مطور ويب ناشئ، وأساعدك في البرمجة، المواقع، والمشاريع خطوة بخطوة.',
        ]
        return random.choice(options)

    if 'محمد' in text and ('مطور' in text or 'مبرمج' in text or 'ويب' in text or 'web' in normalized):
        options = [
            'مرحبًا محمد، هذا بداية ممتازة. أنا IT، مساعدك الذكي، وقد طورت من قبل كـ مطور ويب ناشئ، وأستطيع مساعدتك في بناء المشاريع، فهم الأكواد، والتعلم خطوة بخطوة.',
            'أهلاً محمد، هذا مشروع رائع للبدء. أنا IT، مساعدك الذكي، وقد طورت من قبل كـ مطور ويب ناشئ، وسأساعدك في تنظيم أفكارك وتطوير مهارتك.',
        ]
        return random.choice(options)

    if any(word in normalized for word in ['مرحبا', 'السلام', 'hello', 'hi', 'اهلا', 'اهلاً']):
        options = [
            f'مرحبًا {display_name}، أنا IT Assistant. ما الذي تريد أن نبدأ فيه اليوم؟',
            f'أهلاً {display_name}، أنا IT، مساعدك الذكي، ماذا تريد أن تبدأ به اليوم؟',
            f'مرحبًا {display_name}، أنا جاهز لمساعدتك في البرمجة، المشاريع، أو شرح أي فكرة.',
        ]
        return random.choice(options)

    if any(word in normalized for word in ['فكرة', 'اقتراح', 'مشروع', 'أفكار', 'idea']):
        options = [
            'أفكر معي في فكرة جيدة جدًا: ابدأ بمشكلة حقيقية، ثم حدّد المستخدم الذي سيستخدم الحل، وبعدها ضع خطة من 3 مراحل: الفكرة، التنفيذ، والاختبار.',
            'فكرة قوية تبدأ من مشكلة حقيقية. اجعل هدفك واضحًا، ثم قسّم المشروع إلى واجهة، منطق، وأمان، ثم اختبره خطوة بخطوة.',
            'يمكننا بناء فكرة جيدة إذا بدأت من سؤال واحد: من سيستخدم هذا التطبيق؟ ثم نخطط له من الفكرة إلى التنفيذ.',
        ]
        return random.choice(options)

    if any(word in normalized for word in ['درس', 'شرح', 'تعلم', 'مادة', 'تفسير', 'lesson']):
        options = [
            'أفضل طريقة للتعلم هي: أولًا فهم الفكرة، ثم تطبيق مثال صغير، وبعدها تدريب نفسك على نفس الفكرة في تمرين جديد. إذا أردت، أستطيع شرح الموضوع لك خطوة بخطوة.',
            'ابدأ بالفهم ثم التطبيق، وبعدها التكرار. أستطيع شرح أي درس بطريقة مبسطة ومباشرة جدًا.',
            'إذا كنت تتعلم موضوعًا جديدًا، فعليك تقسيمه إلى أجزاء صغيرة، ثم تدرب على مثال واحد فقط حتى تفهمه تمامًا.',
        ]
        return random.choice(options)

    if any(word in normalized for word in ['برمجة', 'كود', 'python', 'javascript', 'html', 'css', 'php', 'java', 'sql', 'app', 'تطبيق', 'code', 'مطور', 'web']):
        options = [
            'حسنًا، لنبدأ بتحديد الهدف أولًا، ثم نقسم المشروع إلى أجزاء صغيرة مثل الواجهة، المنطق، وقاعدة البيانات. إذا أعطيتني اللغة أو فكرة المشروع، أضع لك خطة واضحة ومباشرة.',
            'أقترح أن تبدأ بتحديد المشكلة، ثم تحدد اللغة المناسبة، وبعدها تقسم المشروع إلى واجهة ومنطق وقاعدة بيانات.',
            'ممتاز. سنبدأ من الفكرة ثم نرسم الخطة، ثم نعمل على التنفيذ خطوة بخطوة لتجنب الالتباس.',
        ]
        return random.choice(options)

    if any(word in normalized for word in ['حل', 'مشكلة', 'خطأ', 'error', 'bug', 'مشكل', 'توقف', 'لا يعمل']):
        options = [
            'دعنا نحلّها بشكل منظم: اذكر الخطأ بدقة، واذكر الخطوات السابقة له، وإذا أمكن أرسل صورة أو مثال. بهذه المعلومات سأحدد السبب بسرعة وأقترح الحل المناسب.',
            'أحسن طريقة لحل المشكلة هي توضيح الخطأ، سبب ظهوره، والجملة التي تسببها. بعد ذلك أساعدك في إيجاد السبب الصحيح.',
            'سأساعدك في تحليل المشكلة خطوة بخطوة، وبدون استنتاجات عشوائية. فقط أخبرني الخطأ الذي يظهر.',
        ]
        return random.choice(options)

    if any(word in normalized for word in ['تلخيص', 'لخص', 'نص', 'مقال', 'ملخص', 'summary']):
        options = [
            'أستطيع مساعدتك في التلخيص بشكل احترافي. فقط أعطني النص أو الفكرة الأساسية، وسأحوله إلى ملخص مختصر وواضح في 3 إلى 5 نقاط فقط.',
            'يمكنني تلخيص أي نص إلى نقاط واضحة ومختصرة جدًا. فقط أرسل النص وسأعد لك ملخصًا عمليًا.',
            'سأقوم بتلخيصك إلى شكل سريع ومباشر، مع إبقاء أهم الأفكار فقط.',
        ]
        return random.choice(options)

    if any(word in normalized for word in ['ساعدني', 'مساعدة', 'اختر', 'توجيه', 'ارشدني', 'help', 'أريد']):
        options = [
            f'أكيد {display_name}، سأساعدك. أخبرني فقط: ما الهدف؟ وما اللغة أو الأدوات التي تريد استخدامها؟ ثم أضع لك الخطة المناسبة.',
            f'طبعًا {display_name}، اشرح لي هدفك فقط، وسأعطيك الخطة المناسبة خطوة بخطوة.',
            f'بالتأكيد {display_name}، ما الذي تبحث عنه؟ المشروع، التعلم، أو حل مشكلة معينة؟',
        ]
        return random.choice(options)

    return None


def fallback_response(message: str, user_name: str | None = None) -> str:
    reply = local_response(message, user_name)
    if reply is not None:
        return reply

    text = (message or '').strip()
    if not text:
        return 'اكتب سؤالك أو طلبك، وسأساعدك خطوة بخطوة.'

    options = [
        'أفهم ما تقصده، وسأساعدك في ذلك. فقط أخبرني بالهدف، المجال، والخطوة التي تريد تنفيذها، وسأعطيك إجابة واضحة ومباشرة.',
        'هذه فكرة جيدة، لكن أحتاج إلى معرفة الهدف والدليل أو المثال الذي تريد حله. بعد ذلك أضع لك الحل المناسب.',
        'أستطيع المساعدة في هذا، لكن الأفضل أن توضح المطلوب بدقة حتى أقدم لك إجابة عملية ومفيدة.',
        'حسنًا، أخبرني أكثر عن المطلوب، وسأعطيك اقتراحًا عمليًا ومباشرًا.',
    ]
    return random.choice(options)


def get_gemini_reply(prompt: str, uploaded_files=None):
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None

    models = ['gemini-3.8-flash', 'gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']

    for model_name in models:
        parts = []
        if prompt:
            parts.append({'text': prompt})

        if uploaded_files:
            for file_path in uploaded_files:
                try:
                    with open(file_path, 'rb') as image_file:
                        image_bytes = image_file.read()
                    mime_type = 'image/jpeg'
                    extension = os.path.splitext(file_path)[1].lower().lstrip('.')
                    if extension in {'png', 'webp'}:
                        mime_type = f'image/{extension}'
                    parts.append({
                        'inline_data': {
                            'mime_type': mime_type,
                            'data': base64.b64encode(image_bytes).decode('utf-8')
                        }
                    })
                except OSError:
                    continue

        if not parts:
            return None

        payload = {
            'contents': [
                {'parts': parts}
            ],
            'generationConfig': {
                'temperature': 0.7,
                'maxOutputTokens': 300,
            }
        }

        req = urllib_request.Request(
            f'https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}',
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        try:
            with urllib_request.urlopen(req, timeout=45) as response:
                parsed = json.loads(response.read().decode('utf-8'))
                candidates = parsed.get('candidates') or []
                if not candidates:
                    continue

                collected = []
                for part in candidates[0].get('content', {}).get('parts', []):
                    if 'text' in part:
                        collected.append(part['text'])
                if collected:
                    return '\n'.join(collected).strip()
        except (
            error.HTTPError,
            error.URLError,
            ValueError,
            KeyError,
            TypeError,
            ConnectionError,
            http_client.RemoteDisconnected,
            OSError,
        ):
            continue
        except Exception:
            continue

    return None


def get_openai_reply(prompt: str):
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return None

    payload = {
        'model': 'gpt-4o-mini',
        'messages': [
            {
                'role': 'system',
                'content': 'أنت مساعد عربي ذكي ومفيد. أجب باللغة العربية فقط، وكن دقيقًا وواضحًا ومباشرًا.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ],
        'temperature': 0.7,
        'max_tokens': 300,
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib_request.Request(
        'https://api.openai.com/v1/chat/completions',
        data=data,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        },
        method='POST'
    )

    try:
        with urllib_request.urlopen(req, timeout=30) as response:
            decoded = response.read().decode('utf-8')
            parsed = json.loads(decoded)
            return parsed['choices'][0]['message']['content'].strip()
    except (
        error.HTTPError,
        error.URLError,
        ValueError,
        KeyError,
        TypeError,
        ConnectionError,
        http_client.RemoteDisconnected,
        OSError,
    ):
        return None
    except Exception:
        return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/plans')
def plans_page():
    return render_template('Bay.html')


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if flask_request.method == 'POST':
        username = (flask_request.form.get('username') or '').strip()
        password = (flask_request.form.get('password') or '').strip()

        if VALID_USERS.get(username) == password:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('chat_page'))

        return render_login_page('اسم المستخدم أو كلمة المرور غير صحيحة.')

    if session.get('logged_in'):
        return redirect(url_for('chat_page'))

    return render_login_page()


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if flask_request.method == 'POST':
        username = (flask_request.form.get('username') or '').strip()
        password = (flask_request.form.get('password') or '').strip()
        confirm_password = (flask_request.form.get('confirm_password') or '').strip()

        if not username or not password:
            return render_register_page('يرجى إدخال اسم المستخدم وكلمة المرور.')

        if len(password) < 4:
            return render_register_page('كلمة المرور يجب أن تكون 4 أحرف على الأقل.')

        if password != confirm_password:
            return render_register_page('كلمتا المرور غير متطابقتين.')

        if username in VALID_USERS:
            return render_register_page('اسم المستخدم موجود بالفعل. جرّب اسمًا آخر.')

        VALID_USERS[username] = password
        session['logged_in'] = True
        session['username'] = username
        return redirect(url_for('chat_page'))

    if session.get('logged_in'):
        return redirect(url_for('chat_page'))

    return render_register_page()


@app.route('/chat')
def chat_page():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    return render_template('index.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/api/chat', methods=['POST'])
def chat():
    if flask_request.mimetype == 'multipart/form-data':
        message = (flask_request.form.get('message') or '').strip()
        uploaded_files = []

        for file in flask_request.files.getlist('images'):
            if not file or not file.filename:
                continue
            ext = os.path.splitext(file.filename)[1].lower().lstrip('.')
            if ext not in ALLOWED_EXTENSIONS:
                continue
            filename = f"{uuid.uuid4().hex}_{file.filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            uploaded_files.append(save_path)

        if not message and not uploaded_files:
            return jsonify({'reply': 'اكتب سؤالًا أو ارفع صورة حتى أتمكن من مساعدتك.'})

        detected_name = extract_name(message)
        if detected_name:
            session['user_name'] = detected_name

        local_reply = local_response(message or 'تحليل الصورة', session.get('user_name'))
        if local_reply is not None:
            return jsonify({'reply': local_reply})

        ai_reply = get_gemini_reply(message, uploaded_files)
        if ai_reply is None:
            ai_reply = get_openai_reply(message)
        if ai_reply is None:
            ai_reply = fallback_response(message or 'تحليل الصورة', session.get('user_name'))
        return jsonify({'reply': ai_reply})

    payload = flask_request.get_json(silent=True) or {}
    message = str(payload.get('message', '')).strip()

    if not message:
        return jsonify({'reply': 'اكتب سؤالًا أو طلبًا صحيحًا حتى أتمكن من مساعدتك.'})

    detected_name = extract_name(message)
    if detected_name:
        session['user_name'] = detected_name

    local_reply = local_response(message, session.get('user_name'))
    if local_reply is not None:
        return jsonify({'reply': local_reply})

    ai_reply = get_gemini_reply(message)
    if ai_reply is None:
        ai_reply = get_openai_reply(message)
    if ai_reply is None:
        ai_reply = fallback_response(message, session.get('user_name'))

    return jsonify({'reply': ai_reply})


if __name__ == '__main__':
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=5000)
